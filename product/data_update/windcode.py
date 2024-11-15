import json
from pymongo import MongoClient
from tqdm import tqdm
from stockpool import getStockName

client = MongoClient('mongodb://47.106.236.106:28039/')
meta_filename = "product/data_update/StockPool.summarySource.json"

windcode_json = []
with open(meta_filename, encoding='utf8') as f:
    meta_infos = json.loads(f.read())
with open('product/data_update/company.json', 'r', encoding='utf-8') as f:
    windcode_json=json.load(f)
windcodes = []
for each in tqdm(meta_infos):
    data_type, db_name, collection_name = each["datatype"], each["website"], each["dbset"]
    db = client[db_name]
    collection = db[collection_name]
    cursor = collection.find({}, {"windCode": 1})
    for data in cursor:
        if 'windCode' not in data.keys():
            continue
        else:
            if data['windCode'] not in windcodes:
                windcodes.append(data['windCode'])
client.close()
max_id = windcode_json[-1]['company_id']
print('all windcodes from source:', len(windcodes))
bad_windcodes = ['UNMAPPED','ffV.N','ALCC.S','WISE.LN']
absent_windcodes = []
for each in windcode_json:
    if each['windcode'] not in windcodes:
        absent_windcodes.append(each['windcode'])
print('missing windcodes:', len(absent_windcodes))
print(absent_windcodes)


absent_windcodes = []
for windcode in tqdm(windcodes):
    if windcode in bad_windcodes:
        continue
    for each in windcode_json:
        if windcode == each['windcode']:
            flag=1
            break
    if flag==1:
        flag=0
        continue
    else:
        stock=getStockName([windcode])
        if len(stock)==0:
            absent_windcodes.append(windcode)
            data = {'company_id': max_id+1, 'windcode': windcode,
                'company_name_en': '', 'company_name_cn': ''}
        else:
            data = {'company_id': max_id+1, 'windcode': windcode,
                    'company_name_en': stock[0]['enName'], 'company_name_cn': stock[0]['zhName']}
        max_id = max_id + 1
        windcode_json.append(data)
print('new windcodes:', len(windcode_json))
print('windcodes unregistered:', len(absent_windcodes))
print(absent_windcodes)
with open('product/data_update/company.json', 'w', encoding='utf-8') as f:
    json.dump(windcode_json, f, indent=4,ensure_ascii=False)

# stock_list=[
#     {"5108.T":"Bridgestone Corp"},
#     {"4519.T":"Chugai Pharmaceutical Co Ltd"},
#     {"4901.T":"Fujifilm Holdings Corp"},
#     {"6702.T":"Fujitsu Ltd"},
#     {"4543.T":"Terumo Corp"},
#     {"6201.T":"Toyota Industries Corp"},
#     {"9434.T":"SoftBank Corp"},
#     {"4568.T":"Daiichi Sankyo Co Ltd"},
#     {"6178.T":"Japan Post Holdings Co Ltd"},
#     {"6501.T":"Hitachi Ltd"},
#     {"8001.T":"Itochu Corp"},
#     {"6301.T":"Komatsu Ltd"},
#     {"6503.T":"Mitsubishi Electric Corp"},
#     {"6902.T":"Denso Corp"},
#     {"6967.T":"Shinko Electric Industries Co Ltd"},
#     {"4005.T":"Sumitomo Chemical Co Ltd"},
#     {"4661.T":"Oriental Land Co Ltd"}
# ]
# for each in tqdm(stock_list):
#     for windcode in windcode_json:
#         if windcode['windcode'] in each.keys():
#             windcode['company_name_en']=each[windcode['windcode']]
#             break