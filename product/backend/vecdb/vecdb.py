import json
import time
from pymilvus import connections, FieldSchema, CollectionSchema, DataType, Collection, utility
from tqdm import tqdm

class VecDB:
    """
    Interaction with vector db
    """

    def __init__(self, config):
        """
        start the vector db service
        """

        # set params
        self._config = config["vecdb"]
        self._topk = self._config["topk"]
        self._index_param = {
            "index_type": self._config["index_type"],
            "params": self._config["index_params"],
            "metric_type": self._config["metric_type"]
            }
        self._search_param = {
            "metric_type": self._config["metric_type"], 
            "params": self._config["search_params"]
            }

        # start vector db service
        print("Starting Vector DB service...")
        connection_retries = self._config["connection_retries"]
        for i in range(connection_retries+1):
            try:
                connections.connect(host=self._config["host"], port=self._config["port"])
                print("- Connected to:", connections.list_connections())
                break
            except:
                if i == connection_retries:
                    raise Exception(f"! Error: cannot connect vector db service with {connection_retries} retries!")
                else:
                    print("- Warning: Failed to connect vector db service, retrying...")

        self._create_collection()
        print("- Done")

    
    def _create_collection(self):

        # create collection if not exists
        if utility.has_collection(self._config["collection_name"]):
            self._collection = Collection(self._config["collection_name"])
        else:
            id_field = FieldSchema(name='id', dtype=DataType.INT64, description="id_int64", is_primary=True)
            embedding_field = FieldSchema(name='embedding', dtype=DataType.FLOAT_VECTOR, description="embedding_floatvector", dim=self._config["dimension"], is_primary=False)
            month_field = FieldSchema(name='month', dtype=DataType.INT64, description="month_int64", is_primary=False)
            company_field = FieldSchema(name='company', dtype=DataType.INT64, description="company_int64", is_primary=False)
            datatype_field = FieldSchema(name='datatype', dtype=DataType.INT64, description="datatype_int64", is_primary=False)
            copyright_field = FieldSchema(name='copyright', dtype=DataType.INT64, description="copyright_int64", is_primary=False)
            schema = CollectionSchema(fields=[id_field, embedding_field, month_field, company_field, datatype_field, copyright_field], description="storing all data")
            self._collection = Collection(name=self._config["collection_name"], data=None, schema=schema, properties={"collection.ttl.seconds": 2**31-1})
            print("- Created collection:", self._collection.name)
        print("- Current collections:", utility.list_collections())

        # create index if not exists
        if not self._collection.has_index():
            self._collection.create_index(field_name="embedding", index_params=self._index_param)
            print("- Created index:", self._collection.indexes)

        # load collection
        self._collection.load()
        print("- Loaded collection, num of vector:", self._collection.num_entities)


    def query(self, query_vector, query_filter, limit=-1):
        """
        return results for the query vector under filter constraints
        """
        if limit == -1:
            limit = self._topk
        if "ef" in self._search_param["params"]:
            if self._search_param["params"]["ef"] < limit:
                raise Exception(f"! Warning: the specified top_k={limit} exceeds maximum={self._search_param['params']['ef']}")
        result = self._collection.search(data=[query_vector],
                                         anns_field='embedding',
                                         param=self._search_param,
                                         limit=limit,
                                         expr=query_filter,
                                         output_fields=["id", "month", "company", "datatype"])
        return [each.to_dict() for each in result[0]]


    def insert(self, ids, embeddings, months, company_ids, datatypes, copyrights):
        """
        insert data into vector db
        data consists of ids, embeddings, months, company_ids, datatypes
        """
        start_time = time.time()
        assert len(ids) == len(embeddings) == len(months) == len(company_ids) == len(datatypes) == len(copyrights)
        data = [ids, embeddings, months, company_ids, datatypes, copyrights]
        self._collection.insert(data)
        self._collection.flush()
        print(f"- inserted {len(ids)} vectors needs {time.time()-start_time}s, current num of vectors in db: {self._collection.num_entities}")


    def delete_by_ids(self, ids):
        """
        delete data from vector db by ids
        """
        assert isinstance(ids, list) and len(ids) > 0
        self._collection.delete(f"id in {str(ids)}")
        self._collection.flush()
        print("- deleted", len(ids), "vectors, current num of vectors in db:", self._collection.num_entities)


    def remove_all_data(self, rebuild_collection=True):
        """
        remove all data from vector db
        """
        print("Removing all data from vector db")
        self._collection.release()
        self._collection.drop_index()
        self._collection.drop()
        if rebuild_collection:
            self._create_collection()
        print("- Done")


    def disconnect(self):
        connections.remove_connection("default")


    def compact_data(self):
        """
        compact data in vector db
        """
        print("Compacting data in vector db")
        self._collection.compact()
        print("- Submitted compaction task")


    def show_compact_status(self):
        print(self._collection.get_compaction_state())


    def rebuild_index(self):
        """
        rebuild index in vector db
        """
        print("Rebuilding index in vector db")
        if self._collection.has_index():
            self._collection.release()
            self._collection.drop_index()
            # self._collection.create_index(field_name="month")
            # self._collection.create_index(field_name="company")
            # self._collection.create_index(field_name="datatype")
            self._collection.create_index(field_name="embedding", index_params=self._index_param)
            print("- Summitted index building task")
        else:
            print("- No index found")


    def show_index_build_status(self):
        print(utility.index_building_progress(self._config["collection_name"]))


    def batch_embedding_search(self, query_vector, limit, filter):
        """
        query by embedding
        """
        if limit == -1:
            limit = self._topk
        search_param = self._search_param
        if "ef" in search_param["params"]:
            if search_param["params"]["ef"] < 8 * limit:
                search_param["params"]["ef"] = 8 * limit

        result = self._collection.search(data=query_vector,
                                         anns_field='embedding',
                                         param=search_param,
                                         limit=limit,
                                         expr=filter,
                                         output_fields=["id"])        
        # [result1, result2]
        # result1 = {"ids": [1, 2], "distances": [0, 1]}
        if len(result) != len(query_vector):
            raise Exception("! Warning: batch embedding search failed, len(result) != len(query_vector)")
        ret = []
        for i in range(len(query_vector)):
            ret.append({"ids": result[i].ids, "distances": result[i].distances})
        return ret
    

    def get_vec_ids(self, offset=0, limit=None):
        """
        get all ids of vectors
        """
        vec_ids=[]
        for i in tqdm(range(475, self._collection.num_entities // 10000 + 1)):
            arr = [j for j in range(i*10000, (i+1)*10000)]
            res = self._collection.query(expr=f"id in {arr}", output_fields=["id"])
            sorted_res = sorted(res, key=lambda x: x['id'])
            vec_ids.extend([each['id'] for each in sorted_res])
        i = self._collection.num_entities // 10000 + 1
        while(True):
            arr = [j for j in range(i*10000, (i+1)*10000)]
            res = self._collection.query(expr=f"id in {arr}", output_fields=["id"])
            if len(res) == 0:
                break
            sorted_res = sorted(res, key=lambda x: x['id'])
            vec_ids.extend([each['id'] for each in sorted_res])
            i = i + 1
        return vec_ids
    