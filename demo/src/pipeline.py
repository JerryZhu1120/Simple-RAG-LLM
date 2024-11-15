import openai
import numpy as np
from time import time
from src.data import Data
from src.vectorindex import VectorIndex
from src.respondent import Respondent


class IndexPipeline:
    def __init__(self, data_filename, db_path, openai_key) -> None:
        self.data_filename = data_filename
        self.openai_key = openai_key
        self.db_path = db_path

    def run(self, text_level, use_product_name):
        data_source = Data(self.data_filename, self.db_path, text_level, use_product_name)
        data_source.extract_data()
        data_source.create_embeddings(self.openai_key)
        vectorindex = VectorIndex(self.db_path)
        vectorindex.build_index()
        

class QueryPipeline:
    def __init__(self, db_paths, openai_key):
        self.db_paths = db_paths
        self.openai_key = openai_key
        self.vectorindexs = []
        self.respondent = None
        openai.api_key = openai_key

    def prepare(self):
        for db_path in self.db_paths:
            vectorindex = VectorIndex(db_path)
            vectorindex.prepare_search()
            self.vectorindexs.append(vectorindex)
        self.respondent = Respondent(self.openai_key)

    def get_num_docs(self):
        return [each.get_num_docs() for each in self.vectorindexs]

    def query(self, query_text, k=8, db_ids=[], model_ids=[]):
        if len(db_ids) == 0 or len(set(db_ids) - set(range(len(self.db_paths)))) > 0:
            return None, None, None, None, None
        if len(self.vectorindexs)==0 or self.respondent is None:
            self.prepare()

        start_time = time()
        emb_model_id = "text-embedding-ada-002"
        query_vector = np.array([openai.Embedding.create(input=query_text, model=emb_model_id)['data'][0]['embedding']])
        encode_time = time() - start_time
        
        search_results, protected_results, total_search_time = [], [], 0
        for i in db_ids:
            search_result, search_time = self.vectorindexs[i].search(query_vector, k)
            if i >= 3: 
                search_results += search_result[1:]
                protected_results += [search_result[0]]
            else:
                search_results += search_result
            total_search_time += search_time
        search_results = sorted(search_results, key=lambda x: x["distance"])[:k-len(protected_results)]
        search_results = sorted(protected_results + search_results, key=lambda x: x["distance"])

        start_time = time()
        prompt = self.respondent.prompt(query_text, search_results)
        outputs = self.respondent.summary(prompt, model_ids)
        respond_time = time() - start_time

        return outputs, search_results, encode_time, total_search_time, respond_time