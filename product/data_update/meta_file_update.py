import json
from pymongo import MongoClient


# Update StockPool.summarySource.json
client = MongoClient('mongodb://47.106.236.106:28039/')
db = client['StockPool']
collection = db['summarySource']
query = {'id': 'information_datas'}
result = collection.find(query)[0]['value']
meta = []
client.close()
for i in range(len(result)):
    if result[i]['datatype'] in ["research", "transcripts", "Press Releases", "news", "tables"]:
        meta.append(result[i])
with open("StockPool.summarySource.json", "w", encoding='utf-8') as f:
    json.dump(meta, f, indent=4)
