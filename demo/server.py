import os
import json
from flask import Flask, request, jsonify
from flask_cors import CORS
from src.pipeline import QueryPipeline

app = Flask(__name__)
CORS(app)

with open('openai.key') as f:
    openai_key = f.read().strip()

db_path_prefix = "D:/vecDBsearch/server/back/db"
db_path_suffixs = [
            "research.full_text", 
            "news.summaryText",
            "transcripts.summaryText",
            "press.summaryText",
            "table.full_text"
            ]
db_names = [
            "研报",
            "新闻",
            "业绩电话会议",
            "业绩公告",
            "最新数据"
]

with open(os.path.join(db_path_prefix, 'config.json'), encoding='utf8') as f:
    db_meta_infos = json.loads(f.read())
query_pipelines = []
for i, each in enumerate(db_meta_infos):
    symbol = each["symbol"]
    version = each["version"]
    print("Processing", symbol, version)
    db_paths = [f"{db_path_prefix}/{symbol}_{version}/{suffix}" for suffix in db_path_suffixs]
    query_pipeline = QueryPipeline(db_paths, openai_key)
    query_pipeline.prepare()
    query_pipelines.append(query_pipeline)
    db_meta_infos[i]["dbs"] = [{
            "id": i,
            "name": f"{db_name}({num_docs})"
        } for db_name, num_docs in zip(db_names, query_pipeline.get_num_docs())]
    print('-'*40)


@app.route('/query', methods=['POST'])
def query():

    try:
        query_input = request.get_json()
        print(query_input)
        query_text = query_input["query_text"]
        company_id = int(query_input["company_id"])
        db_ids = query_input["db_ids"]
        model_ids = query_input["model_ids"]

        if query_text == '':
            return jsonify({'message': 'Empty query'}), 400
        if company_id not in range(len(query_pipelines)):
            return jsonify({'message': 'Invalid company'}), 400
        query_pipeline = query_pipelines[company_id]
        outputs, search_results, encode_time, search_time, respond_time = query_pipeline.query(query_text, 8, db_ids, model_ids)
        
        references = []
        for i, each in enumerate(search_results):
            references.append({
                'ref_id': i+1,
                'title': each["title"],
                'id': each["id"],
                'text': each["chunk_text"].replace('\n', ''),
                'url': each["url"],
                "publishOn": each["publishOn"]
            })

        response = {
            'message': 'Success', 
            'summaries': outputs,
            'references': references,
            'encode_time': encode_time,
            'search_time': search_time,
            'respond_time': respond_time,
        }  
        return jsonify(response)
    except Exception as e:
        print(e)
        return jsonify({'message': str(e)}), 400
    

@app.route('/get_meta', methods=['POST'])
def get_meta():
    try:
        response = {
            'message': 'Success', 
            'meta_data': db_meta_infos,
        }  
        return jsonify(response)
    except Exception as e:
        print(e)
        return jsonify({'message': str(e)}), 400
    

if __name__ == '__main__':
    app.run("0.0.0.0", port=5000)
    # app.run("0.0.0.0", port=63001)