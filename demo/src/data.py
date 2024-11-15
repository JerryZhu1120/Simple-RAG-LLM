import os
import json
import openai
from tqdm import tqdm
from concurrent import futures
from langchain.text_splitter import RecursiveCharacterTextSplitter


class Data:
    def __init__(self, data_filename, db_path, text_level="summaryText", use_product_name=False):
        self.data_filename = data_filename
        self.data_name = self.data_filename.split('/')[-1].replace('.json', '')
        self.text_level = text_level
        self.db_path = db_path
        self.use_product_name = use_product_name
        if not os.path.exists(self.db_path):
            os.mkdir(self.db_path)
        print(f"Data source:'{self.data_filename}', data name:'{self.data_name}', db path:'{self.db_path}'")

    def extract_data(self):
        """
        extract interested data from data source
        split texts into chunks
        """
        extracted_filename = f'{self.db_path}/extracted_data.json'
        if os.path.exists(extracted_filename):
            print(f"File '{extracted_filename}' exists, skip extract data.")
            return
        print(f"Start extract data to {extracted_filename} ...")
        with open(self.data_filename, encoding='utf8') as f:
            data = json.loads(f.read())
        
        extracted_data = []
        for each in data:
            try:
                text = each[self.text_level]
                if isinstance(text, list):
                    text = ' '.join(text)
                url, productName = "", ""
                if "local_path" in each:
                    url = each["local_path"].replace('C:\\virtualD\\work\\project\\download\\', 'http://8.129.218.237:8011/pdfs/')
                elif "source_url" in each:
                    url = each["source_url"]
                if "productName" in each and self.use_product_name:
                    productName = each["productName"]
                extracted_data.append({
                    "id": each["id"],
                    "title": each["title"],
                    "text": text,
                    "publishOn": each["publishOn"],
                    "url": url,
                    "productName": productName,
                    "chunk_text": [],
                    "start_index": [],
                })
            except Exception as e:
                print(e)
        print(f"- Done. Doc cnt: {len(extracted_data)}.")

        print("Start split texts into chunks ...")
        text_splitter = RecursiveCharacterTextSplitter(
            chunk_size = 1024,
            chunk_overlap  = 128,
            length_function = len,
            add_start_index = True,
        )

        chunk_cnt = 0
        for each in extracted_data:
            texts = text_splitter.create_documents([each["text"]])
            each["chunk_texts"] = [text.page_content for text in texts]
            each["start_indexs"] = [text.metadata['start_index'] for text in texts]
            chunk_cnt += len(each["chunk_texts"])

        print(f"- Done. Chunk_cnt:{chunk_cnt}, write to '{extracted_filename}'.")
        with open(extracted_filename, 'w', encoding='utf8') as f:
            json.dump(extracted_data, f, ensure_ascii=False, indent=4)

    def create_embeddings(self, openai_key, num_workers=8):
        """
        use openai API to embed each chunk
        """
        extrated_filename = f'{self.db_path}/extracted_data.json'
        embedding_filename = f'{self.db_path}/embeddings.json'
        if os.path.exists(embedding_filename):
            print(f"File '{embedding_filename}' exists, skip create embeddings.")
            return
        openai.api_key = openai_key
        emb_model_id = "text-embedding-ada-002"  

        with open(extrated_filename, encoding='utf8') as f:
            extracted_data = json.loads(f.read())      
        
        def get_embedding(chunk_text, doc_idx, text_idx):
            if self.use_product_name:
                chunk_text = "(" + extracted_data[doc_idx]["productName"] + ")" + chunk_text
            embedding = openai.Embedding.create(input=chunk_text, model=emb_model_id)['data'][0]['embedding']
            return {
                "embedding": embedding,
                "doc_id": doc_idx,
                "text_id": text_idx,
            }

        print("Start create embeddings ...")
        embeddings = []
        with futures.ThreadPoolExecutor(max_workers=num_workers) as executor:    
            future_to_chunk = {}
            for doc_idx, doc in enumerate(extracted_data):
                for text_idx, chunk_text in enumerate(doc["chunk_texts"]):
                    future = executor.submit(get_embedding, chunk_text, doc_idx, text_idx)
                    future_to_chunk[future] = (doc_idx, text_idx)
            
            for future in tqdm(futures.as_completed(future_to_chunk)):
                doc_idx, text_idx = future_to_chunk[future]
                try:
                    embedding_result = future.result()
                    embeddings.append(embedding_result)
                except Exception as e:
                    embeddings.append({
                        "embedding": None,
                        "doc_id": doc_idx,
                        "text_id": text_idx,
                    })
                    print(f"处理文档 '{doc_idx}', 文本 '{text_idx}' 时出现错误：{e}")
                    print(extracted_data[doc_idx]["chunk_texts"][text_idx])
                    print('-' * 40)
        
        print(f"- Done. Current Embedding cnt: {len(embeddings)}, write to '{embedding_filename}'.")
        with open(embedding_filename, 'w', encoding='utf8') as f:
            json.dump(embeddings, f, ensure_ascii=False, indent=4)

        for i, each in enumerate(embeddings):
            if each["embedding"] is None:
                print(f"embedding is None, doc_id:{each['doc_id']}, text_id:{each['text_id']}")
                embeddings[i] = get_embedding(extracted_data[each['doc_id']]["chunk_texts"][each['text_id']], each['doc_id'], each['text_id'])
        
        print(f"- Done. Final Embedding cnt: {len(embeddings)}, write to '{embedding_filename}'.")
        with open(embedding_filename, 'w', encoding='utf8') as f:
            json.dump(embeddings, f, ensure_ascii=False, indent=4)