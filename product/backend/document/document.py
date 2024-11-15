from textdb.text_preprocess import TextPreprocesser
from textdb.textdb import TextDB
from vecdb.vecdb import VecDB
from dbManage import dbManage
import time
import os
from concurrent import futures
from tqdm import tqdm
import urllib.request
from langchain.document_loaders import PyPDFLoader, UnstructuredHTMLLoader
from pdfminer.pdfparser import PDFParser
from pdfminer.pdfdocument import PDFDocument

class Document():
    """
    add documents to MongoDB and update vecdb
    """

    def __init__(self, config, textdb: TextDB, vecdb: VecDB, text_preprocesser: TextPreprocesser):
        self._config = config["data"]
        self._text_processor = text_preprocesser
        self._text_db = textdb
        self._vec_db = vecdb
        self._dbManage = dbManage(textdb._mydb, vecdb)
        self._password = '231206StockChat'

    def is_valid_pdf(self, file_path):
        try:
            with open(file_path, 'rb') as pdf_file:
                parser = PDFParser(pdf_file)
                document = PDFDocument(parser)
                if document.catalog:
                    return True
                else:
                    return False
        except Exception:
            return False

    def add_one_document(self, document_str_id, document_title, datatype,
                         windcode, company_name_en, company_name_cn,
                         date, month, text=None, chunk_texts=None):

        if text is None and chunk_texts is None:
            raise ValueError("! text and chunk_texts cannot be both None")
        print("Processing document:", document_str_id)

        # obtain document str id
        result = self._text_db.get_document_str_id(document_str_id)
        if result is not None:
            print(f"- document {document_str_id} already exists, skip it")
            return

        # obtain company id
        company_id = self._text_db.get_company_id_by_windcode(windcode)
        if company_id is None:
            company_id = self._text_db.insert_company(
                windcode, company_name_en, company_name_cn)

        # obtain datatype id
        datatype_id = self._text_db.get_datatype_id_by_name(datatype)

        # preprocess text
        start_time = time.time()
        chunk_embeddings, chunk_texts = self._text_processor.preprocess(company_name_en, text, chunk_texts)
        print(f"- split chunks and get {len(chunk_texts)} embeddings, time:", 
              time.time() - start_time, "s")

        # insert chunks into text db
        start_time = time.time()
        chunk_ids = self._text_db.insert_batch_chunks(document_str_id, chunk_texts, chunk_embeddings)
        print(f"- insert embeddings into text db needs {time.time()-start_time}s, number of embeddings:", 
              self._text_db.get_number_of_chunks())
        
        # insert into vec db
        self._vec_db.insert(ids=chunk_ids,
                            embeddings=chunk_embeddings,
                            months=[month for _ in range(len(chunk_embeddings))],
                            company_ids=[company_id for _ in range(len(chunk_embeddings))],
                            datatypes=[datatype_id for _ in range(len(chunk_embeddings))])
        
        # insert document into text db
        start_time = time.time()
        self._text_db.insert_document(document_str_id, document_title, datatype_id, company_id, date, month, text,
                                      chunk_ids=chunk_ids)
        print(f"- insert document into text db needs {time.time()-start_time}s")

    def get_research_text(self, document_data):
        url = document_data["url"]
        url = os.path.join('../data/', url).replace('\\','/')
        if not os.path.exists(url):
            raise Exception(f"! Error: file path {url} does not exist")
        if url[-3:] == 'pdf':
            if self.is_valid_pdf(f"{url}"):
                loader = PyPDFLoader(f"{url}")
                doc_type = 'pdf'
            else:
                raise Exception(f"! Error: the pdf file {url} is invalid")
        elif url[-4:] == 'html':
            loader = UnstructuredHTMLLoader(
                f"{url}", mode="elements", strategy="fast",
            )
            doc_type = 'html'
        else:
            raise Exception(f"Unsupported file type. File path: {url}")

        try:
            pages = loader.load_and_split()
            text = [page.page_content for page in pages]
            if isinstance(text, list):
                text = ' '.join(text)
        except Exception as e:
            print(f"! Error in processing {id}.{doc_type}, skip it:")
            print(e)
        return text

    def delete_private_documents(self, document_data):
        print(f'Deleting documents: {[each["document_str_id"] for each in document_data]}')
        doc_copyright_map = self._text_db.get_doc_to_copyright_id_map_by_doc_ids([each['document_str_id'] for each in document_data])
        error_list = []
        for each in document_data:
            copyright_id = doc_copyright_map[each['document_str_id']]
            copyright = self._text_db._get_copyright_name_by_id(copyright_id)
            if copyright == each['copyright']:
                self._dbManage.delete_doc_and_chunk(each['document_str_id'], self._password)
            else:
                error_list.append(each['document_str_id'])
        if len(error_list) == 0:
            return
        else:
            raise Exception(f"! Error: authentification failed for documents {error_list}")

    def delete_document(self, document_str_id):
        print(f'Deleting document: {document_str_id}')
        self._dbManage.delete_doc_and_chunk(document_str_id, self._password)

    # for one company's certain datatype
    def add_batch_document(self, documents_data):
        new_documents_data = []
        for each in documents_data:
            if each['text'] is None and each['chunk_texts'] is None:
                if each['datatype'] == 'research':
                    each['text'] = self.get_research_text(each)
                else:
                    raise ValueError(f"! text and chunk_texts cannot be both None, doc:{each['document_str_id']}")
            result = self._text_db.get_document_str_id(each['document_str_id'])
            if result is not None:
                print(f"- document {each['document_str_id']} already exists, skip it")
            else:
                new_documents_data.append(each)
        if new_documents_data == []:
            return
        print(f"Processing document:{[each['document_str_id'] for each in new_documents_data]}")

        # obtain company id
        for each in new_documents_data:
            company_id = self._text_db.get_company_id_by_windcode(each['windcode'])
            if company_id is None:
                company_id = self._text_db.insert_company(
                    each['windcode'], each['company_name_en'], each['company_name_cn'])
            copyright_id = self._text_db._get_copyright_id_by_name(each['copyright'])
            if copyright_id is None:
                copyright_id=self._text_db.insert_copyright(each['copyright'])
            each['copyright_id'] = copyright_id
            each['company_id'] = company_id
            each['datatype_id'] = self._text_db.get_datatype_id_by_name(each['datatype'])

        # need modification for table data
        start_time = time.time()
        with futures.ThreadPoolExecutor(max_workers=new_documents_data[0]['num_workers']) as executor:
            future_to_chunk = {}
            for each in new_documents_data:
                future=executor.submit(self._text_processor.preprocess, each['company_name_en'], each['text'], each['chunk_texts'])
                future_to_chunk[future] = each
            
            batch_embeddings_cnt=0

            for future in tqdm(futures.as_completed(future_to_chunk)):
                each = future_to_chunk[future]
                each['embeddings'], each['chunk_texts']= future.result()
                batch_embeddings_cnt=batch_embeddings_cnt+len(each['embeddings'])

        print(f"- split chunks and get {batch_embeddings_cnt} embeddings, time:", 
            time.time() - start_time, "s")
        
        if batch_embeddings_cnt > 9000:
            raise ValueError(f"! embeddings count exceeds limit. {batch_embeddings_cnt}/9000")
        
        # insert chunks into text db
        start_time = time.time()
        chunk_ids = self._text_db.insert_batch_doc_chunks(new_documents_data)
        print(f"- insert embeddings into text db needs {time.time()-start_time} s, number of embeddings:", 
            self._text_db.get_number_of_chunks())
        # insert into vec db
        self._vec_db.insert(ids=chunk_ids,
                            embeddings=[each['embeddings'][i] for each in new_documents_data for i in range(len(each['embeddings']))],
                            months=[each['month'] for each in new_documents_data for _ in range(len(each['embeddings']))],
                            company_ids=[each['company_id'] for each in new_documents_data for _ in range(len(each['embeddings']))],
                            datatypes=[each['datatype_id'] for each in new_documents_data for _ in range(len(each['embeddings']))],
                            copyrights=[each['copyright_id'] for each in new_documents_data for _ in range(len(each['embeddings']))])
        
        begin=0
        for each in new_documents_data:
            each['chunk_ids']=chunk_ids[begin:begin+len(each['embeddings'])]
            begin=begin+len(each['embeddings'])

        # insert document into text db
        start_time = time.time()
        self._text_db.insert_batch_document(new_documents_data)
        print(f"- insert documents into text db needs {time.time()-start_time}s")