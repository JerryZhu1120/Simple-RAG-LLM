import os
import json
import faiss
import openai
from time import time
import numpy as np


class VectorIndex:
    def __init__(self, db_path):
        self.db_path = db_path
        self.index_filename = f'{self.db_path}/faiss.index'
        self.index = self.raw_data = self.idx_to_doc_text_idx = None
        print(f"db path:'{self.db_path}'")

    def build_index(self):
        """
        build vector index using faiss
        """
        if os.path.exists(self.index_filename):
            print(f"File '{self.index_filename}' exists, skip build index.")
            return
    
        with open(f'{self.db_path}/embeddings.json', encoding='utf8') as f:
            data = json.loads(f.read())
        embeddings = []
        for each in data:
            embeddings.append(each["embedding"])
        embeddings = np.array(embeddings, dtype=np.float32)

        print(f"Start build index ...")
        index = faiss.IndexFlatL2(embeddings.shape[1])
        index.add(embeddings)

        print(f"- Done. Embeddings cnt: {embeddings.shape[0]}, write to '{self.index_filename}'.")
        faiss.write_index(index, self.index_filename)

    def prepare_search(self):
        """
        prepare metadata, rawdata and index for search
        """
        print("Prepare metadata, rawdata and index for search ...")
        self.idx_to_doc_text_idx = []
        with open(f'{self.db_path}/embeddings.json', encoding='utf8') as f:
            data = json.loads(f.read())
        for each in data:
            self.idx_to_doc_text_idx.append((each["doc_id"], each["text_id"]))

        with open(f'{self.db_path}/extracted_data.json', encoding='utf-8') as f:
            self.raw_data = json.loads(f.read())
        self.index = faiss.read_index(self.index_filename)
        print(f"- Done. Doc cnt: {len(self.raw_data)}")

    def search(self, query_vector, k):
        """
        search vector index using faiss
        """
        if self.index==None or self.raw_data==None or self.idx_to_doc_text_idx==None:
            self.prepare_search()
        
        start_time = time()
        distances, indices = self.index.search(query_vector, k)
        res = []
        for distance, idx in zip(distances[0], indices[0]):
            doc_id, text_id = self.idx_to_doc_text_idx[idx]
            res.append({
                "id": self.raw_data[doc_id]["id"],
                "title": self.raw_data[doc_id]["title"],
                "chunk_text": self.raw_data[doc_id]["chunk_texts"][text_id],
                "start_index": self.raw_data[doc_id]["start_indexs"][text_id],
                "url": self.raw_data[doc_id]["url"],
                "publishOn": self.raw_data[doc_id]["publishOn"],
                "distance": distance,
            })
        search_time = time() - start_time
        return res, search_time
    
    def get_num_docs(self):
        return len(self.raw_data)