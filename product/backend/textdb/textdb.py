import time
import pymongo
from collections import defaultdict


class TextDB:
    """
    Interaction with text db
    Store full texts and meta data
    """

    def __init__(self, config):
        client = pymongo.MongoClient(config["textdb"]["mongodb_url"])
        self._mydb = client["textdb"]

        print("Starting Text DB service ...")
        self._datatype_data = self._mydb["datatype"].find({}, {"datatype_id":1, "datatype_name":1})
        # [{"datatype_id":1, "datatype_name":'a'}, {"datatype_id":2, "datatype_name":'b'}]
        self._datatype_name_to_id = {each["datatype_name"]: each["datatype_id"] for each in self._datatype_data}
        # {"a":1, "b":2}
        self._datatype_data = self._mydb["datatype"].find({}, {"datatype_id":1, "datatype_name":1})
        self._datatype_id_to_name = {each["datatype_id"]: each["datatype_name"] for each in self._datatype_data}
        
        self._company_ids_and_names = self._get_company_ids_and_names()
        # [{"id":1, "name_en":'a', "name_cn":'b'}, {"id":2, "name_en":'c', "name_cn":'d'}]

        copyright_ids_and_names = self._mydb["copyright"].find()
        # [{"copyright_id":1, "copyright_name":'a'}, {"copyright_id":2, "copyright_name":'b'}]
        self._copyright_name_to_id = {each["copyright_name"]: each["copyright_id"] for each in copyright_ids_and_names}
        # {"a":1, "b":2}
        copyright_ids_and_names = self._mydb["copyright"].find()
        # [{"copyright_id":1, "copyright_name":'a'}, {"copyright_id":2, "copyright_name":'b'}]
        self._copyright_id_to_name = {each["copyright_id"]: each["copyright_name"] for each in copyright_ids_and_names}

        doc_str_id_set = self._mydb["document"].find({}, {"document_str_id":1}) # Cursor
        # [{"document_str_id":'str_id_1'}, {"document_str_id":'str_id_2'}]
        self._doc_str_id_set = set([each['document_str_id'] for each in doc_str_id_set])

        month = self._mydb["document"].find({}, {"month":1}) # Cursor
        # [{"month":'202001'}, {"month":'202002'}]
        self._months = set([each['month'] for each in month])

        print("- Done")


    def _get_copyright_id_by_name(self, copyright_name):
        if copyright_name not in self._copyright_name_to_id.keys():
            return None
        return self._copyright_name_to_id[copyright_name]
    
    def _get_copyright_name_by_id(self, copyright_id):
        if copyright_id not in self._copyright_id_to_name.keys():
            return None
        return self._copyright_id_to_name[copyright_id]
    
    
    def get_copyright_ids(self, copyright_names):
        # copyright_names = ["a", "b"]
        # maybe contain None
        return [self._get_copyright_id_by_name(name) for name in copyright_names]


    def is_in_doc_str_id_set(self, doc_str_id):
        return doc_str_id in self._doc_str_id_set


    def get_doc_str_id_set(self):
        return self._doc_str_id_set


    def get_company_id_by_windcode(self, windcode):
        data = self._mydb["company"].find_one({"windcode":windcode}, {"company_id":1})
        # {"company_id":1} or None
        if data:
            return data["company_id"]
        return None


    def _add_data(self, table_name, datas):
        if table_name not in ["company", "chunk", "copyright"]:
            raise Exception("Table name error")
        counters = self._mydb["counters"]
        table = self._mydb[table_name] # table = self._mydb["company"]
        rt_ids = []
        for data in datas:
            id_name = table_name + "_id"
            # id_name = "company_id" / "chunk_id" / "datatype_id" / "copyright_id"
            result = counters.find_one_and_update({id_name:table_name}, 
                                                  {"$inc":{"sequence_value":1}}, 
                                                  upsert=True, 
                                                  return_document=pymongo.ReturnDocument.AFTER)
            # {id_name:table_name, "sequence_value":1}
            sequence_value = result["sequence_value"]
            data[id_name] = sequence_value
            # data = {"company_id":1, "windcode":'a', "company_name_en":'b', "company_name_cn":'c'}
            rt_ids.append(sequence_value)
            # [1, 2, 3]
        rt_data = table.insert_many(datas)
        # rt_data.inserted_ids = [ObjectId('...'), ObjectId('...'), ObjectId('...')]
        if len(rt_data.inserted_ids) != len(datas):
            raise Exception("Insert data error")
        return rt_ids


    def insert_copyright(self, copyright_name):
        """
        insert a copyright return its id
        """
        if self._get_copyright_id_by_name(copyright_name) != None:
            return self._copyright_name_to_id[copyright_name]
        datas = [{"copyright_name":copyright_name}]
        ret = self._add_data("copyright", datas)
        # ret = [1]
        copyright_id = ret[0]
        self._copyright_name_to_id[copyright_name] = copyright_id
        return copyright_id
    

    def insert_company(self, windcode, company_name_en, company_name_cn):
        """
        try to insert a company into text db
        return company id if success
        """
        if self.get_company_id_by_windcode(windcode) != None:
            return self.get_company_id_by_windcode(windcode)
        
        datas = [{
            "windcode": windcode, 
            "company_name_en":company_name_en.lower(),
            "company_name_cn":company_name_cn
            }]

        ret = self._add_data("company", datas)
        # ret = [1]
        company_id = ret[0]

        self._company_ids_and_names.append({
            "id":company_id,
            "name_en":company_name_en.lower(),
            "name_cn":company_name_cn 
        })

        return company_id
    

    def get_document_str_id(self, document_str_id):
        data = self._mydb["document"].find_one({"document_str_id":document_str_id}, {"document_str_id":1})
        # {"document_str_id":'str_id'} or None
        if data:
            return data['document_str_id']
        return None


    def insert_document(self, document_str_id, document_title, datatype_id, company_id, date, month, text, chunk_ids):
        """
        try to insert a document into text db
        return document id if success
        """
        if self.get_document_str_id(document_str_id) != None:
            return self.get_document_str_id(document_str_id)

        datas = [{
            "document_str_id": document_str_id,
            "document_title": document_title,
            "datatype_id": datatype_id,
            "company_id": company_id,
            "date": date,
            "month": month,
            "text": text, 
            "chunk_ids": chunk_ids,
        }]

        ret = self._mydb["document"].insert_many(datas)
        # ret.inserted_ids = [ObjectId('...')]
        if len(ret.inserted_ids) != len(datas):
            raise Exception("Insert document error")        
        
        self._doc_str_id_set.add(document_str_id)
        self._months.add(month)
        print("- insert document success, document str id:", document_str_id)


    def insert_batch_document(self, documents_data):
        """
        try to insert a document into text db
        return document id if success
        """
        new_documents_data=[]
        for each in documents_data:
            if self.get_document_str_id(each['document_str_id']) is None:
                new_documents_data.append(each)

        datas = [{
            "document_str_id": each['document_str_id'],
            "document_title": each['document_title'],
            "datatype_id": each['datatype_id'],
            "company_id": each['company_id'],
            "date": each['date'],
            "month": each['month'],
            "text": each['text'], 
            "chunk_ids": each['chunk_ids'],
            "url": each['url'],
            "copyright_id": each['copyright_id']
        } for each in new_documents_data]

        ret = self._mydb["document"].insert_many(datas)
        # ret.inserted_ids = [ObjectId('...')]
        if len(ret.inserted_ids) != len(datas):
            raise Exception("Insert document error")        
        
        for each in new_documents_data:
            self._doc_str_id_set.add(each['document_str_id'])
            self._months.add(each['month'])
        print(f"- insert documents success, document str id list:{[each['document_str_id'] for each in new_documents_data]}")


    def get_number_of_chunks(self):
        # return self._mydb['chunk'].count_documents({})
        return self._mydb['chunk'].estimated_document_count()
    

    def insert_batch_chunks(self, document_str_ids, chunk_texts, embeddings):
        """
        document_str_ids: ['a', 'b', 'c']
        chunk_texts: ["...", "...", "..."]
        embeddings: [[1, 2], [2, 3], [3, 2]]
        """
        if not len(chunk_texts) == len(embeddings):
            raise Exception('Length does not match')
        
        datas = [{
            "document_str_id" : document_str_ids,
            "chunk_text": chunk_texts[i],
            "embedding": embeddings[i]
        } for i in range(len(chunk_texts))]

        ret_ids = self._add_data("chunk", datas)
        # ret_ids = [1, 2, 3]
        return ret_ids


    def insert_batch_doc_chunks(self, new_documents_data):
        """
        document_str_ids: ['a', 'b', 'c']
        chunk_texts: ["...", "...", "..."]
        embeddings: [[1, 2], [2, 3], [3, 2]]
        """
        datas=[{
            'document_str_id':each['document_str_id'],
            'chunk_text':each['chunk_texts'][i],
            'embedding':each['embeddings'][i]
        } for each in new_documents_data for i in range(len(each['embeddings']))]

        ret_ids = self._add_data("chunk", datas)
        # ret_ids = [1, 2, 3]
        return ret_ids
    

    def get_datatype_id_by_name(self, datatype_name):
        if datatype_name in self._datatype_name_to_id:
            return self._datatype_name_to_id[datatype_name]
        raise Exception(f"! Error: datatype '{datatype_name}' not found!")
    
    def get_datatype_name_by_id(self, datatype_id):
        if datatype_id in self._datatype_id_to_name:
            return self._datatype_id_to_name[datatype_id]
        raise Exception(f"! Error: datatype_id '{datatype_id}' not found!")


    def remove_all_data(self):
        """
        remove all data from text db
        """
        pass
        # print("Removing all data from text db")
        # for id in getVectorData("chunk", rtcolumns={"document_str_id":1}):
        #     if len(id):
        #         delVectorData(id['document_str_id'])
        # for id in getVectorData("document", rtcolumns={"document_str_id":1}):
        #     if len(id):
        #         delVectorData(id['document_str_id'])
        # print("- Done")


    def get_grouped_texts(self, chunk_ids):
        """
        group chunk texts by document id, join the texts together
        """

        # group by document id
        data = self._mydb['chunk'].find({"chunk_id": {"$in": chunk_ids}}, {"chunk_id":1, "document_str_id":1}) # Cursor
        # [{"chunk_id":1, "document_str_id":'a'}, {"chunk_id":2, "document_str_id":'a'}, {"chunk_id":3, "document_str_id":'b'}]
        results = []

        docs = defaultdict(list)
        for each in data:
            docs[each['document_str_id']].append(each['chunk_id'])
        for doc_str_id in docs:
            docs[doc_str_id].sort()

        for doc_str_id in docs:
            doc_text = self._mydb['chunk'].find_one({"chunk_id":docs[doc_str_id][0]}, {"chunk_text":1})['chunk_text'].replace('\n', ' ')
            last_chunk_id = docs[doc_str_id][0]
            for chunk_id in docs[doc_str_id][1:]:
                if chunk_id != last_chunk_id + 1:
                    doc_text += '\n ... \n'
                doc_text += self._mydb['chunk'].find_one({"chunk_id":chunk_id}, {"chunk_text":1})['chunk_text'].replace('\n', ' ')
                last_chunk_id = chunk_id

            # format the result
            document = self._mydb['document'].find_one({"document_str_id":doc_str_id}, {"document_title":1, "datatype_id":1, "date":1, "url":1})
            datatype_name = self.get_datatype_name_by_id(document["datatype_id"])
            # 这里find_one后面不加判断，如果有问题直接就报错
            results.append({
                "doc_id": doc_str_id,
                "title": document["document_title"],
                "datatype_name": datatype_name,
                "chunk_ids": docs[doc_str_id],
                "texts": doc_text,
                "date": document["date"],
                "url":document["url"]
            })
        
        return results
    

    def get_ungrouped_texts(self, chunk_ids):
        """
        get chunk texts by chunck ids
        """

        results = []
        for chunk_id in chunk_ids:
            data = self._mydb['chunk'].find_one({"chunk_id":chunk_id}, {"chunk_text":1, "document_str_id":1})
            chunk_text = data['chunk_text'].replace('\n', ' ')
            doc_str_id = data['document_str_id']
            document = self._mydb['document'].find_one({"document_str_id":doc_str_id}, {"document_title":1, "date":1, "url":1, "datatype_id":1})
            datatype_name = self._mydb['datatype'].find_one({"datatype_id":document['datatype_id']}, {"datatype_name":1})['datatype_name']
            results.append({
                "doc_id": doc_str_id,
                "title": document["document_title"],
                "datatype_name": datatype_name,
                "chunk_ids": [chunk_id],
                "texts": chunk_text,
                "date": document["date"],
                "url":document["url"]
            })
        return results
    

    def get_company_id_range(self):
        data = self._mydb["company"].aggregate([{"$group":{"_id":None, "min":{"$min":"$company_id"}, "max":{"$max":"$company_id"}}}])
        data = list(data)
        # [{"_id":None, "min":1, "max":2}]
        if len(data) and len(data[0]):
            return (data[0]["min"], data[0]["max"])
        return None


    def get_datatype_id_range(self):
        data = self._mydb["datatype"].aggregate([{"$group":{"_id":None, "min":{"$min":"$datatype_id"}, "max":{"$max":"$datatype_id"}}}])
        data = list(data)
        # [{"_id":None, "min":1, "max":2}]
        if len(data) and len(data[0]):
            return (data[0]["min"], data[0]["max"])    
        return None
    

    def _get_company_ids_and_names(self):
        data = self._mydb["company"].find({}, {"company_id":1, "company_name_en":1, "company_name_cn":1}) # Cursor
        # [{"company_id":1, "company_name_en":'a', "company_name_cn":'b'}, {"company_id":2, "company_name_en":'c', "company_name_cn":'d'}]
        return [{
            'id': each['company_id'],
            'name_en': each['company_name_en'],
            'name_cn': each['company_name_cn']
        } for each in data]
        
    
    def get_company_ids_and_names(self):
        return self._company_ids_and_names


    def get_datatype_ids_and_names(self):
        data = self._mydb["datatype"].find({}, {"datatype_id":1, "datatype_name":1})
        return [{
            'id': each['datatype_id'], 
            'name': each['datatype_name']
        } for each in data]
    

    def get_months(self):
        return sorted(list(self._months), reverse=True)
    

    def get_company_id_by_name(self, company_name):
        company_name = company_name.lower()

        data = self._mydb["company"].find_one({"company_name_cn":company_name}, {"company_id":1})
        # {"company_id":1} or None
        if data:
            return data["company_id"]
        
        data = self._mydb["company"].find_one({"company_name_en":company_name}, {"company_id":1})
        # {"company_id":1} or None
        if data:
            return data["company_id"]
        
        return None

    
    def get_embeddings_by_doc_str_ids(self, document_str_ids, with_chunk_ids=False):
        """
        get embeddings by using document str ids
        """
        results = []
        for doc_str_id in document_str_ids:
            chunk_ids = self._mydb['document'].find_one({"document_str_id":doc_str_id}, {"chunk_ids":1})
            if chunk_ids is None:
                results.append([])
                continue
            chunk_ids = chunk_ids["chunk_ids"]
            embeddings_for_each_doc = self._mydb['chunk'].find({"chunk_id": {"$in": chunk_ids}}, {"chunk_id":1,"embedding":1})
            if with_chunk_ids:
                embeddings_for_each_doc = [(each["embedding"], each["chunk_id"]) for each in embeddings_for_each_doc]
            else:
                embeddings_for_each_doc = [each["embedding"] for each in embeddings_for_each_doc]
            results.append(embeddings_for_each_doc)
        return results
    

    def get_batch_texts(self, data):
        """
        data = [data1, data2]
        data1 = {"ids": [1, 2], "distances": [0, 1]}    

        return = [result1, result2]
        result1 = [doc1, doc2, doc3]
        doc1 = {"text":["text1", "text2"], "distance":[0, 1],
                "doc_str_id": "doc_str_id1", "date": date}
        """
        
        ret = []
        for each in data:
            id_to_distance = {each["ids"][i]: each["distances"][i] for i in range(len(each["ids"]))}
            # print(id_to_distance)
            # {1:0, 2:1}
            data = self._mydb['chunk'].find({"chunk_id": {"$in": each["ids"]}}, {"chunk_id":1, "document_str_id":1}) # Cursor
            # [{"chunk_id":1, "document_str_id":'a'}, {"chunk_id":2, "document_str_id":'a'}, {"chunk_id":3, "document_str_id":'b'}]
            result_i = []
            docs = defaultdict(list)
            for each in data:
                docs[each['document_str_id']].append(each['chunk_id'])
            for doc_str_id in docs:
                docs[doc_str_id].sort()
            # docs = {"a":[1, 2], "b":[3]}
            # print(docs)
            for doc_str_id in docs:
                chunk_data = list(self._mydb['chunk'].find({"chunk_id": {"$in": docs[doc_str_id]}}, {"chunk_text":1, "chunk_id":1})) # List
                # [{"chunk_id":1, "chunk_text":'a'}, {"chunk_id":2, "chunk_text":'b'}]
                texts = [each["chunk_text"] for each in chunk_data]
                distances = [id_to_distance[each["chunk_id"]] for each in chunk_data]
                # format the result
                date = self._mydb['document'].find_one({"document_str_id":doc_str_id}, {"date":1})
                # {"date": date}

                # 这里find_one后面不加判断，如果有问题直接就报错
                result_i.append({
                    "doc_str_id": doc_str_id,
                    "date": date["date"],
                    "texts": texts,
                    "distances": distances
                })
                # print(result_i)
            ret.append(result_i)
        return ret


    def get_embeddings_ids_by_time(self, start_time, end_time, datatype):
        datatype_id = self._mydb["datatype"].find_one({"datatype_name":datatype}, {"datatype_id":1})
        if datatype_id is None:
            raise Exception("datatype not found")
        datatype_id = datatype_id["datatype_id"]
        data = self._mydb["document"].find({"date": {"$gte": start_time, "$lte": end_time}, "datatype_id":datatype_id},
                                           {"document_str_id":1, "chunk_ids":1, "date":1})
        # [{"document_str_id":'a', "chunk_ids":[1, 2], "date":'202001'}, {"document_str_id":'b', "chunk_ids":[3, 4], "date":'202002'}]
        result = []
        for each in data:
            embeddings = self._mydb["chunk"].find({"chunk_id": {"$in": each["chunk_ids"]}}, {"embedding":1})
            result.append({
                "doc_str_id": each["document_str_id"],
                "embeddings": [each["embedding"] for each in embeddings],
                "date": each["date"]
            })
        # [{"doc_str_id":'a', "embeddings":[[1, 2], [2, 3]], "date":'2023-08-09 24:00:00'}, 
        # {"doc_str_id":'b', "embeddings":[[3, 2], [2, 1]], "date":'2023-08-09 '}]
        return result
    

    def get_chat_history_by_id(self, chat_id):
        """
        get chat history by chat id
        """
        data = self._mydb["chat"].find_one({"chat_id":chat_id}, {"chat_id":1, "chat_history":1})
        if data:
            return data["chat_history"]
        return None
    

    def update_chat_history(self, chat_id, chat_history):
        """
        add chat history by chat id
        """
        data = self._mydb["chat"].find_one({"chat_id":chat_id}, {"chat_id":1})
        if data:
            self._mydb["chat"].update_one({"chat_id":chat_id}, {"$set":{"chat_history":chat_history}})
        else:
            self._mydb["chat"].insert_one({"chat_id":chat_id, "chat_history":chat_history})


    def get_ids_by_datatype(self, datatype):
        """
        get document ids using datatype
        """
        datatype_id = self._mydb["datatype"].find_one({"datatype_name":datatype}, {"datatype_id":1})
        if datatype_id is None:
            print("datatype not found")
        else:
            datatype_id = datatype_id["datatype_id"]
            data = self._mydb["document"].find({"datatype_id":datatype_id}, {"document_str_id":1})
            # [{"document_str_id":'a'}, {"document_str_id":'b'}]
            return [each["document_str_id"] for each in data]
        

    def get_doc_to_copyright_id_map_by_doc_ids(self, doc_str_ids):
        """
        get copyright ids by document ids
        """
        data = self._mydb["document"].find({"document_str_id":{"$in":doc_str_ids}}, {"document_str_id":1, "copyright_id":1})
        # [{"document_str_id":'a', "copyright_id":1}, {"document_str_id":'b', "copyright_id":2}]
        return {each["document_str_id"]: each["copyright_id"] for each in data}
        