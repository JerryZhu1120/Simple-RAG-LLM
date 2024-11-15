import os
import json
import requests
import urllib.request
from tqdm import tqdm
from pymongo import MongoClient
from langchain.document_loaders import PyPDFLoader, UnstructuredHTMLLoader
from pdfminer.pdfparser import PDFParser
from pdfminer.pdfdocument import PDFDocument

class DataUpdate():
    """
    update data from MongoDB
    """

    def __init__(self, config):
        """
        init connections with MongoDB, textdb and vecdb
        """
        with open(config, encoding='utf-8') as f:
            config = json.load(f)
        self._config = config["data"]
        self._mongo_client = MongoClient(self._config["mongodb_url"])
        self._meta_file = '../data_update/StockPool.summarySource.json'
        with open(self._meta_file, encoding='utf8') as f:
            self._meta_infos = json.load(f)
        self._url = "http://localhost:63001/"
        with open('research_list.json') as f:
            research_list = json.load(f)
        self.research_list = research_list['research_list']


    def update_test_data(self):
        """
        update for test data for debugging
        """
        
        with open('../data/test_data.json') as f:
            test_data = json.load(f)
        for each in test_data:

            # document_str_id: the 'id' field in MongoDB
            document_str_id = each['id']

            # document_title: the 'title' field in MongoDB
            document_title = each['title']

            # datatype: the 'dataType' field in MongoDB
            datatype = each['dataType']

            # windcode: the 'windCode' field in MongoDB
            windcode = each['windCode']

            company_name_en = "Microsoft"

            company_name_cn = "微软"

            # date: the 'publishOn' field in MongoDB
            date = each['publishOn']

            # month: from the 'publishOn' field in MongoDB
            month = 202306

            # text: the 'summaryText' field in MongoDB
            text = each['summaryText']
            if isinstance(text, list):
                text = ' '.join(text)

            # add the document by sending post request
            self._add_one_document(document_str_id, document_title, datatype, windcode, 
                                   company_name_en, company_name_cn, date, month, 
                                   text=text, chunk_texts=None)

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
        
    def _add_one_document(self, document_str_id, document_title, datatype,
                          windcode, company_name_en, company_name_cn,
                          date, month, text, chunk_texts):
        """
        add one document by sending post request
        """
        # format the data
        data = {"documents_data": [{
                        "document_str_id": document_str_id,
                        "document_title": document_title,
                        "datatype": datatype,
                        "windcode": windcode,
                        "company_name_en": company_name_en,
                        "company_name_cn": company_name_cn,
                        "date": date,
                        "month": month,
                        "text": text,
                        "chunk_texts": chunk_texts
                }]}

        # send post request to add the document
        response = requests.post(self._url + "add_documents", json=data)
        if response.status_code == 200:
            resp = response.json()
            if resp['Status']=="Success":
                print(f"- Insert document {document_str_id} successfully")
            else:
                raise Exception("! Error when adding documents in server:", resp['Message'])
        else:
            raise Exception("! Error when sending post request to server:", response.status_code)

    def _add_batch_document(self, documents_data):
        """
        add documents by sending post request
        """
        # send post request to add the document
        data={"documents_data": documents_data}
        response = requests.post(self._url + "add_documents", json=data)
        if response.status_code == 200:
            resp = response.json()
            if resp['Status']=="Success":
                print(f"- Insert document {[each['document_str_id'] for each in documents_data]} successfully")
            else:
                raise Exception("! Error when adding documents in server:", resp['Message'])
        else:
            raise Exception("! Error when sending post request to server:", response.status_code)

    def update_all(self, version, target_company_code='all', force_skip=False, batch_size=10, num_workers=4):
        """
        update for all kinds of data
        """
        # get all existing document str ids
        response = requests.post(self._url + "get_doc_str_ids")
        if response.status_code == 200:
            resp = response.json()
            if resp['Status']=="Success":
                doc_str_ids = set(resp['doc_str_ids'])
            else:
                raise Exception("! Error when getting doc_str_ids in server:", resp['Message'])
        else:
            raise Exception("! Error when sending post request to server:", response.status_code)

        # get company infos
        with open('company.json', encoding='utf-8') as f:
            company_info = json.load(f)
        # update by company codes
        if target_company_code == 'all':
            windcode_list = []
            i=0
            for company in company_info:
                # i=i+1
                # if i<686:
                #     continue
                windcode_list.append(company['windcode'])
                
            print(len(windcode_list))
            self.update_all(version, windcode_list, force_skip, batch_size, num_workers)
        else:
            documents_data=[]
            error_url=[]
            for windcode in tqdm(target_company_code):
                self._collect_data(windcode, doc_str_ids)
                for each in tqdm(self.all_data['research']):
                    url = each["local_path"].replace(
                        "C:\\virtualD\\work\\project\\download", "../data/public_doc").replace('\\','/')
                    id = each["id"]
                    if not os.path.exists(url):
                        error_url.append(url)
                        print(f"! Absent file: {url}")
                        if force_skip:
                            print("Skip it")
                            continue
                        else:
                            print("Please check the file and run again")
                            return
                    copyright = each['copyright']
                    if id in doc_str_ids:
                        print(f"- document {id} is absent or already exists, skip it")
                        continue
                    if url[-3:] == 'pdf':
                        if self.is_valid_pdf(url):
                            loader = PyPDFLoader(url)
                            doc_type = 'pdf'
                        else:
                            print(f"! Warning: the pdf file {url} is invalid, skip it")
                            continue
                    elif url[-4:] == 'html':
                        loader = UnstructuredHTMLLoader(
                            url, mode="elements", strategy="fast",
                        )
                        doc_type = 'html'
                    else:
                        print(f"Unsupported file type. File path: {url}")
                        if force_skip:
                            continue
                        else:
                            return
                    try:
                        pages = loader.load_and_split()
                        text = [page.page_content for page in pages]
                        if isinstance(text, list):
                            text = ' '.join(text)
                    except Exception as e:
                        print(f"! Error in processing {id}.{doc_type}, skip it:")
                        print(e)
                    if 'mastCode' in each:
                        windcode = each['mastCode'][0]
                    else:
                        windcode = each['windCode']
                    flag = 0
                    for company in company_info:
                        if company['windcode'] == windcode:
                            company_name_en = company['company_name_en']
                            company_name_cn = company['company_name_cn']
                            flag=1
                            break
                    if flag == 0:
                        raise Exception("! Error when getting company info in server:", windcode)
                    data = {
                        "document_str_id": id,
                        "document_title": each['title'],
                        "datatype": 'research',
                        "windcode": windcode,
                        "company_name_en": company_name_en,
                        "company_name_cn": company_name_cn,
                        "date": each['publishOn'],
                        "month": int(each['publishOn'][:4]+each['publishOn'][5:7]),
                        "text": text,
                        "chunk_texts": None,
                        "num_workers": num_workers,
                        "url": each["local_path"].replace(
                        "C:\\virtualD\\work\\project\\download", "http://8.129.218.237:8011/pdfs"),
                        'copyright': copyright
                    }
                    documents_data.append(data)

                    if len(documents_data) == batch_size:
                        with open('research_list.json', 'w') as f:
                            json.dump({'research_list': self.research_list}, f, ensure_ascii=False, indent=4)
                        self._add_batch_document(documents_data)
                        documents_data = []

                for each in tqdm(self.all_data['news']):
                    document_str_id = each['id']
                    if document_str_id in doc_str_ids:
                        print(f"- document {document_str_id} already exists, skip it")
                        continue
                    windcode = each['windCode']
                    for company in company_info:
                        if company['windcode'] == windcode:
                            company_name_en = company['company_name_en']
                    for company in company_info:
                        if company['windcode'] == windcode:
                            company_name_cn = company['company_name_cn']
                    text = each['summaryText']
                    if isinstance(text, list):
                        text = ' '.join(text)
                    data = {
                        "document_str_id": document_str_id,
                        "document_title": each['title'],
                        "datatype": 'news',
                        "windcode": windcode,
                        "company_name_en": company_name_en,
                        "company_name_cn": company_name_cn,
                        "date": each['publishOn'],
                        "month": int(each['publishOn'][:4]+each['publishOn'][5:7]),
                        "text": text,
                        "chunk_texts": None,
                        "num_workers": num_workers,
                        "url": each['source_url'],
                        'copyright': 'public'
                    }
                    documents_data.append(data)

                    if len(documents_data) == batch_size:
                        self._add_batch_document(documents_data)
                        documents_data = []

                for each in tqdm(self.all_data['transcripts']):
                    document_str_id = each['id']
                    if document_str_id in doc_str_ids:
                        print(f"- document {document_str_id} already exists, skip it")
                        continue
                    windcode = each['windCode']
                    for company in company_info:
                        if company['windcode'] == windcode:
                            company_name_en = company['company_name_en']
                    for company in company_info:
                        if company['windcode'] == windcode:
                            company_name_cn = company['company_name_cn']
                    text = each['summaryText']
                    if isinstance(text, list):
                        text = ' '.join(text)
                    print(document_str_id)
                    data = {
                        "document_str_id": document_str_id,
                        "document_title": each['title'],
                        "datatype": 'transcripts',
                        "windcode": windcode,
                        "company_name_en": company_name_en,
                        "company_name_cn": company_name_cn,
                        "date": each['publishOn'],
                        "month": int(each['publishOn'][:4]+each['publishOn'][5:7]),
                        "text": text,
                        "chunk_texts": None,
                        "num_workers": num_workers,
                        "url": each['source_url'],
                        'copyright': 'public'
                    }
                    documents_data.append(data)

                    if len(documents_data) == batch_size:
                        self._add_batch_document(documents_data)
                        documents_data = []

                for each in tqdm(self.all_data['Press Releases']):
                    document_str_id = each['id']
                    if document_str_id in doc_str_ids:
                        print(f"- document {document_str_id} already exists, skip it")
                        continue
                    windcode = each['windCode']
                    for company in company_info:
                        if company['windcode'] == windcode:
                            company_name_en = company['company_name_en']
                    for company in company_info:
                        if company['windcode'] == windcode:
                            company_name_cn = company['company_name_cn']
                    text = each['summaryText']
                    if isinstance(text, list):
                        text = ' '.join(text)
                    data = {
                        "document_str_id": document_str_id,
                        "document_title": each['title'],
                        "datatype": 'Press Releases',
                        "windcode": windcode,
                        "company_name_en": company_name_en,
                        "company_name_cn": company_name_cn,
                        "date": each['publishOn'],
                        "month": int(each['publishOn'][:4]+each['publishOn'][5:7]),
                        "text": text,
                        "chunk_texts": None,
                        "num_workers": num_workers,
                        "url": each['source_url'],
                        'copyright': 'public'
                    }
                    documents_data.append(data)

                    if len(documents_data) == batch_size:
                        self._add_batch_document(documents_data)
                        documents_data = []
                
            if len(documents_data) > 0:
                self._add_batch_document(documents_data)
                documents_data = []

            with open("error_url.txt", "w") as f:
                f.write("\n".join(error_url))


    def remove_all_vecdb_data(self):
        """
        remove all data from vecdb
        """
        pass
        # self._vec_db.remove_all_data()


    def remove_all_textdb_data(self):
        """
        remove all data from textdb
        """
        pass
        # self._text_db.remove_all_data()


    def _collect_data(self, windcode, doc_str_ids):
        """
        download data from MongoDB
        """
        self.all_data = {
            "research": [],
            "transcripts": [],
            "Press Releases": [],
            "news": [],
            "tables": []
        }

        client = MongoClient('mongodb://47.106.236.106:28039/')
        query = {'windCode': windcode}
        print('Windcode:', windcode)
        for each in self._meta_infos:
            data_type, db_name, collection_name = each["datatype"], each["website"], each["dbset"]
            print('Collecting:', data_type, '->',
                  db_name, '->', collection_name)
            db = client[db_name]
            collection = db[collection_name]
            results = collection.find(query, {'id':1})
            for each in results:
                if each['id'] not in doc_str_ids:
                    result = collection.find_one({'id': each['id']})
                    if data_type=='research':
                        if collection_name == 'east':
                            collection_name = 'public'
                        result['copyright'] = collection_name
                    self.all_data[data_type].append(result)
        client.close()

        for data_type in self.all_data:
            print(data_type, "num_docs:", len(self.all_data[data_type]))

        # print('Collecting research pdfs/htmls ...')
        # pdf_path = os.path.join(self.save_path, 'pdf')
        # html_path = os.path.join(self.save_path, 'html')
        # if not os.path.exists(pdf_path):
        #     os.makedirs(pdf_path)
        # if not os.path.exists(html_path):
        #     os.makedirs(html_path)
        # for each in self.all_data['research']:
        #     url = each["local_path"].replace(
        #         "C:\\virtualD\\work\\project\\download", "http://8.129.218.237:8011/pdfs")
        #     id = each["id"]
        #     if os.path.exists(f"{pdf_path}/{id}.pdf") or os.path.exists(f"{html_path}/{id}.html"):
        #         continue
        #     url = urllib.parse.quote(url, safe=':/')
        #     try:
        #         if (url[-3:] == 'pdf'):
        #             urllib.request.urlretrieve(url, f"{pdf_path}/{id}.pdf")
        #         else:
        #             if (url[-4:] == 'html'):
        #                 urllib.request.urlretrieve(
        #                     url, f"{html_path}/{id}.html")
        #             else:
        #                 print(f"Unsupported file type. File path: {url}")
        #     except Exception as e:
        #         print(
        #             f"! Cannot download the file: {str(e)}\n  Please download manually by {url}, and save to {self.save_path}/pdf/{id}.pdf or {self.save_path}/html/{id}.html(depending on the file type)")
        # print("Finish.")