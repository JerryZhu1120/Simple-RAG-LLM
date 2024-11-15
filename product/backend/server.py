import json
from flask import Flask, request, jsonify
from flask_cors import CORS

from vecdb.vecdb import VecDB
from textdb.textdb import TextDB
from textdb.text_preprocess import TextPreprocesser
from respondent.respondent import Respondent
from respondent.api import API
from document.document import Document

# init flask app
app = Flask(__name__)
CORS(app)

# init for query
with open("../config.json") as f:
    config = json.load(f)
with open('openai.key') as f:
    openai_key = f.read().strip()

# Create instances
vecdb_instance = VecDB(config)
textdb_instance = TextDB(config)
text_preprocess_instance = TextPreprocesser(config, openai_key)
respondent_instance = Respondent(config, vecdb_instance, textdb_instance, text_preprocess_instance, openai_key)
api_instance = API(config, vecdb_instance, textdb_instance, openai_key)
document_instance = Document(config, textdb_instance, vecdb_instance, text_preprocess_instance)


@app.route('/get_meta', methods=['GET'])
def get_meta():
    try:
        model_names = respondent_instance.get_model_names()
        company_ids_and_names =textdb_instance.get_company_ids_and_names()
        datatype_ids_and_names = textdb_instance.get_datatype_ids_and_names()
        months = textdb_instance.get_months()

        return jsonify({
            "Status": "Success",
            "Message": "",
            "model_names": model_names,
            "company_ids_and_names": company_ids_and_names,
            "datatype_ids_and_names": datatype_ids_and_names,
            "months": months
        })
    except Exception as e:
        print('!', e)
        return jsonify({
            "Status": "Fail",
            "Message": str(e)
            })


@app.route('/query', methods=['POST'])
def query():
    try:
        query_input = request.get_json()
        print('-', query_input)

        # necessary
        user_query_text = query_input["query_text"]
        chat_id = query_input["chat_id"]
        
        # optional
        answer_language = 'auto'
        model_names = ["gpt-4-1106-preview"]
        auto_filter = True
        top_k = -1
        # copyrights = ["public"]
        copyrights = ['public', 'bernste', 'neoubs', 'aletheia', 'marquee', 'jefferies', 'jpmorgan', 'yipit', 'cicc']
        company_ids = []
        datatype_ids = []
        months = []
        if 'model_names' in query_input:
            model_names = query_input["model_names"]
        if 'auto_filter' in query_input:
            auto_filter = query_input["auto_filter"]
        if 'top_k' in query_input:
            top_k = query_input["top_k"]
        if 'copyrights' in query_input:
            copyrights = query_input["copyrights"]
        if 'company_ids' in query_input:
            company_ids = query_input["company_ids"]
        if 'datatype_ids' in query_input:
            datatype_ids = query_input["datatype_ids"]
        if 'months' in query_input:
            months = query_input["months"]

        result = respondent_instance.query(user_query_text, model_names, answer_language,
                                           copyrights, company_ids, datatype_ids, months, chat_id, 
                                           auto_filter, product_mode=True, top_k=top_k)
        return jsonify(result)
    except Exception as e:
        print('! Execution query failed:', e)
        return jsonify({
            "Status": "Fail",
            "Message": str(e)
            })
    

@app.route('/query_with_doc_ids', methods=['POST'])
def query_with_doc_ids():
    try:
        query_input = request.get_json()
        print('-', query_input)

        # necessary
        user_query_text = query_input["query_text"]
        chat_id = query_input["chat_id"]
        doc_str_ids = query_input["doc_str_ids"]
        
        # optional
        answer_language = 'auto'
        model_names = ["gpt-4-1106-preview"]
        top_k = -1
        # copyrights = ["public"]
        copyrights = ['public', 'bernste', 'neoubs', 'aletheia', 'marquee', 'jefferies', 'jpmorgan', 'yipit', 'cicc']
        if 'model_names' in query_input:
            model_names = query_input["model_names"]
        if 'top_k' in query_input:
            top_k = query_input["top_k"]
        if 'copyrights' in query_input:
            copyrights = query_input["copyrights"]

        result = respondent_instance.query_with_doc_ids(user_query_text, model_names, doc_str_ids, answer_language, copyrights, chat_id, top_k=top_k)
        return jsonify(result)
    except Exception as e:
        print('! Execution query failed:', e)
        return jsonify({
            "Status": "Fail",
            "Message": str(e)
            })
    

@app.route('/query_full_mode', methods=['POST'])
def query_full_mode():
    try:
        query_input = request.get_json()
        print('-', query_input)

        # necessary
        user_query_text = query_input["query_text"]
        chat_id = query_input["chat_id"]
        
        # optional
        answer_language = 'auto'
        model_names = ["gpt-4-1106-preview"]
        auto_filter = True
        top_k = -1
        copyrights = ['public', 'bernste', 'neoubs', 'aletheia', 'marquee', 'jefferies', 'jpmorgan', 'yipit', 'cicc']
        company_ids = []
        datatype_ids = []
        months = []
        if 'model_names' in query_input:
            model_names = query_input["model_names"]
        if 'auto_filter' in query_input:
            auto_filter = query_input["auto_filter"]
        if 'top_k' in query_input:
            top_k = query_input["top_k"]
        if 'copyrights' in query_input:
            copyrights = query_input["copyrights"]
        if 'company_ids' in query_input:
            company_ids = query_input["company_ids"]
        if 'datatype_ids' in query_input:
            datatype_ids = query_input["datatype_ids"]
        if 'months' in query_input:
            months = query_input["months"]

        result = respondent_instance.query(user_query_text, model_names, answer_language,
                                           copyrights, company_ids, datatype_ids, months, chat_id, 
                                           auto_filter, product_mode=False, top_k=top_k)
        return jsonify(result)
    except Exception as e:
        print('! Execution query failed:', e)
        return jsonify({
            "Status": "Fail",
            "Message": str(e)
            })
    

@app.route('/get_embeddings_by_doc_str_ids', methods=['POST'])
def get_embeddings_by_doc_str_ids():
    print("Call /get_embeddings_by_doc_str_ids")
    try:
        query_input = request.get_json()
        doc_str_ids = query_input["doc_str_ids"]
        print("- query doc ids:", doc_str_ids)

        results = textdb_instance.get_embeddings_by_doc_str_ids(doc_str_ids)

        return jsonify({
            "Status": "Success",
            "Message": "",
            "Embeddings": results
        })
    except Exception as e:
        print('! Execution get_embeddings_by_doc_str_ids failed:', e)
        return jsonify({
            "Status": "Fail",
            "Message": str(e)
        })
    

@app.route('/add_documents', methods=['POST'])
def add_documents():
    try:
        query_input = request.get_json()
        documents_data = query_input["documents_data"]
        document_instance.add_batch_document(documents_data)
        return jsonify({
            "Status": "Success"
        })

    except Exception as e:
        print('! Add documents failed:', e)
        return jsonify({
            "Status": "Fail",
            "Message": str(e)
            })


@app.route('/delete_documents', methods=['POST'])
def delete_documents():
    try:
        query_input = request.get_json()
        documents_data = query_input["documents_data"]
        document_instance.delete_private_documents(documents_data)
        return jsonify({
            "Status": "Success"
        })

    except Exception as e:
        print('! Delete documents failed:', e)
        return jsonify({
            "Status": "Fail",
            "Message": str(e)
            })

@app.route('/get_doc_str_ids', methods=['POST'])
def get_doc_str_ids():
    try:
        doc_str_ids = textdb_instance.get_doc_str_id_set()
        doc_str_ids = list(doc_str_ids)
        return jsonify({
            "Status": "Success",
            "doc_str_ids": doc_str_ids
        })

    except Exception as e:
        print('! Add documents failed:', e)
        return jsonify({
            "Status": "Fail",
            "Message": str(e)
            })


@app.route('/batch_embedding_search', methods=['POST'])
def batch_embedding_search():
    try:
        query_input = request.get_json()
        embeddings = query_input["embeddings"]
        
        # optional
        top_k = -1
        copyright_names = []
        company_windcodes = []
        datatype_names = []
        months = []
        if 'top_k' in query_input:
            top_k = query_input["top_k"]
        if 'copyright_names' in query_input:
            copyright_names = query_input["copyright_names"]
        if 'company_windcodes' in query_input:
            company_windcodes = query_input["company_windcodes"]
        if 'datatype_names' in query_input:
            datatype_names = query_input["datatype_names"]
        if 'months' in query_input:
            months = query_input["months"]

        result = api_instance.batch_embedding_search(embeddings, copyright_names, company_windcodes, datatype_names, months, top_k)
        return jsonify(result)
    except Exception as e:
        print('! Execution query using embedding failed:', e)
        return jsonify({
            "Status": "Fail",
            "Message": str(e)
            })


@app.route('/get_embeddings_ids_by_time', methods=['POST'])
def get_embeddings_ids_by_time():
    print("Call /get_embeddings_ids_by_time")
    try:
        query_input = request.get_json()
        start_time = query_input["start_time"]
        end_time = query_input["end_time"]
        datatype = query_input["datatype"]
        print("- query time:", start_time, end_time)

        results = textdb_instance.get_embeddings_ids_by_time(start_time, end_time, datatype)
        return jsonify(results)
    except Exception as e:
        print('! Execution get_embeddings_ids_by_time failed:', e)
        return jsonify({
            "Status": "Fail",
            "Message": str(e)
        })


@app.route('/get_ids_by_datatype', methods=['POST'])
def get_ids_by_datatype():
    print("Call /get_ids_by_datatype")
    try:
        query_input = request.get_json()
        datatype = query_input["datatype"]
        results = textdb_instance.get_ids_by_datatype(datatype)
        return jsonify(results)
    except Exception as e:
        print('! Execution get_embeddings_ids_by_time failed:', e)
        return jsonify({
            "Status": "Fail",
            "Message": str(e)
        })


if __name__ == '__main__':
    # app.run("0.0.0.0", port=5000)
    app.run("0.0.0.0", port=63001)