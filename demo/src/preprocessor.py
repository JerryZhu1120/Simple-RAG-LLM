import os
import json
import urllib.request
from tqdm import tqdm
from pymongo import MongoClient
from langchain.document_loaders import PyPDFLoader



class PreProcessor:
    def __init__(self, meta_filename, target_company_code):
        self.all_data = {
            "research": [],
            "transcripts": [],
            "Press Releases": [],
            "news": [],
            "tables": []
        }
        self.meta_filename = meta_filename
        self.target_company_code = target_company_code
        
    def collect_data(self, save_path):
        """
        download data from MongoDB
        """
        self.save_path = save_path
        if os.path.exists(self.save_path):
            print(f"Warning: Path '{self.save_path}' exists, re-collect data again.")
        else:
            os.mkdir(self.save_path)
        print('Will download to:', self.save_path)

        with open(self.meta_filename, encoding='utf8') as f:
            meta_infos = json.loads(f.read())
        client = MongoClient('mongodb://47.106.236.106:28039/') 
        query = {'windCode': self.target_company_code}

        for each in meta_infos:
            data_type, db_name, collection_name = each["datatype"], each["website"], each["dbset"]
            print('Collecting:', data_type, '->', db_name, '->', collection_name)
            db = client[db_name]
            collection = db[collection_name]
            results = collection.find(query)
            self.all_data[data_type] += list(results)
        client.close()

        for data_type in self.all_data:
            print(data_type, "num_docs:", len(self.all_data[data_type]))

        print('Collecting research pdfs ...')
        pdf_path = os.path.join(self.save_path, 'pdf')
        if not os.path.exists(pdf_path):
            os.makedirs(pdf_path)
        for each in self.all_data['research']:
            url = each["local_path"].replace("C:\\virtualD\\work\\project\\download", "http://8.129.218.237:8011/pdfs")
            id = each["id"]
            if os.path.exists(f"{pdf_path}/{id}.pdf"):
                continue
            try:
                urllib.request.urlretrieve(url, f"{pdf_path}/{id}.pdf")
            except Exception as e:
                print(f"! Cannot download the file: {str(e)}\n  Please downlaod manually by {url}, and save to {pdf_path}/{id}.pdf")
        print("Finish.")

    def transform_and_save(self, force_skip=False):
        """
        save transformed data to json files
        """
        absent_ids = set()
        for each in self.all_data['research']:
            url = each["local_path"].replace("C:\\virtualD\\work\\project\\download", "http://8.129.218.237:8011/pdfs")
            id = each["id"]
            if not os.path.exists(f"{self.save_path}/pdf/{id}.pdf"):
                print(f"! Please downlaod file manually by {url}, and save to {self.save_path}/pdf/{id}.pdf")
                absent_ids.add(id)
        
        if len(absent_ids) > 0:
            if force_skip:
                print("! Warning: some files are not downloaded, skip them.")
            else:
                print("! Not saved, please download above files manually, then retry.")
                return

        research_data = []
        for each in tqdm(self.all_data['research']):
            id = each["id"]
            if id in absent_ids:
                continue
            loader = PyPDFLoader(f"{self.save_path}/pdf/{id}.pdf")
            each["_id"] = str(each["_id"])
            try:
                pages = loader.load_and_split()
                each["full_text"] = [page.page_content for page in pages]
                research_data.append(each)
            except Exception as e:
                print(f"! Error in processing {id}.pdf, skip it:")
                print(e)
        with open(f"{self.save_path}/research.json", "w", encoding='utf8') as f:
            json.dump(research_data, f)

        news_data = []
        for each in self.all_data['news']:
            each["_id"] = str(each["_id"])
            news_data.append(each)
        with open(f"{self.save_path}/news.json", "w", encoding='utf8') as f:
            json.dump(news_data, f)

        transcripts_data = []
        for each in self.all_data['transcripts']:
            each["_id"] = str(each["_id"])
            transcripts_data.append(each)
        with open(f"{self.save_path}/transcripts.json", "w", encoding='utf8') as f:
            json.dump(transcripts_data, f)

        press_data = []
        for each in self.all_data['Press Releases']:
            each["_id"] = str(each["_id"])
            press_data.append(each)
        with open(f"{self.save_path}/press.json", "w", encoding='utf8') as f:
            json.dump(press_data, f)

    def process_table(self, table_filenames, target_db_path, update_time):
        """
        注意：这里需要预处理表格为csv格式，且每一块内容都需要人工换行分割开
        """
        print("Processing tables ...")
        extracted_data = []
        for table_filename in table_filenames:
            with open(table_filename, 'r', encoding='utf8') as f:
                lines = f.readlines()
            data = []
            cur = []
            for line in lines:
                line = line.strip()
                if line == '':
                    data.append('\n'.join(cur))
                    cur = []
                else:
                    cur.append(line)
            data.append('\n'.join(cur))
            for i in range(1,len(data)):
                data[i] = data[0]+"\n"+data[i]

            extracted_data.append({
                "id": "table_"+table_filename,
                "title": table_filename,
                "text": ''.join(lines),
                "publishOn": update_time,
                "url": "",
                "productName": "",
                "chunk_texts": data[1:],
                "start_indexs": list(range(0, len(data[1:]))),
            })  

        table_path = os.path.join(target_db_path, 'table.full_text')
        print("Writing to", table_path)
        if not os.path.exists(table_path):
            os.makedirs(table_path)
        with open(os.path.join(table_path, "extracted_data.json"), 'w', encoding='utf8') as f:
            json.dump(extracted_data, f, ensure_ascii=False, indent=4)

    def get_data_filenames(self):
        return [
            f"{self.save_path}/research.json",
            f"{self.save_path}/news.json",
            f"{self.save_path}/transcripts.json",
            f"{self.save_path}/press.json",
            f"{self.save_path}/table.json"
        ]
    
    def get_text_levels(self):
        return [
            "full_text",
            "summaryText",
            "summaryText",
            "summaryText",
            "full_text"
        ]
    
    def get_db_paths(self, target_db_path):
        folder_names = [
            "research.full_text",
            "news.summaryText",
            "transcripts.summaryText",
            "press.summaryText",
            "table.full_text"
        ]
        return [
            os.path.join(target_db_path, each) for each in folder_names
        ]