import json
import pymongo
from tqdm import tqdm
from vecdb import VecDB

with open('../../config.json') as f:
    config = json.load(f)


# define the api class
class TextDBforDump:
    def __init__(self) -> None:
        client = pymongo.MongoClient('mongodb://localhost:27017/')
        self._textdb = client['textdb']

        document_data = self._textdb['document'].find({}, {"document_str_id":1, "month":1, "company_id":1, "datatype_id":1, "copyright_id":1})
        self._str_ids_to_infos = {each["document_str_id"]: {"month":each["month"], "company_id":each["company_id"], 
                                                            "datatype_id":each["datatype_id"], "copyright_id":each["copyright_id"]} for each in document_data}
        # {'a': {'month':1, 'company_id':1, 'datatype_id':1}}
    

    def get_all_vector_cursor(self):
        return self._textdb['chunk'].find({})
    
    
    def transform(self, chunk_data):
        ids = [each['chunk_id'] for each in chunk_data]
        embeddings = [each['embedding'] for each in chunk_data]
        months = [self._str_ids_to_infos[each['document_str_id']]["month"] for each in chunk_data]
        company_ids = [self._str_ids_to_infos[each['document_str_id']]["company_id"] for each in chunk_data]
        datatypes = [self._str_ids_to_infos[each['document_str_id']]['datatype_id'] for each in chunk_data]
        copyrights = [self._str_ids_to_infos[each['document_str_id']]['copyright_id'] for each in chunk_data]
        return ids, embeddings, months, company_ids, datatypes, copyrights

# init
textdb_for_dump = TextDBforDump()
vecdb = VecDB(config)
# vecdb.remove_all_data()

# insert data
cur_chunk_data = []
for each in tqdm(textdb_for_dump.get_all_vector_cursor()):
    cur_chunk_data.append(each)
    if len(cur_chunk_data) == 10000:
        ids, embeddings, months, company_ids, datatypes, copyrights = textdb_for_dump.transform(cur_chunk_data)
        vecdb.insert(ids, embeddings, months, company_ids, datatypes, copyrights)
        cur_chunk_data = []

if len(cur_chunk_data) > 0:
    ids, embeddings, months, company_ids, datatypes, copyrights = textdb_for_dump.transform(cur_chunk_data)
    vecdb.insert(ids, embeddings, months, company_ids, datatypes, copyrights)