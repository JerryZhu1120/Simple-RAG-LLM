from data_update import DataUpdate
import time
import json
data_update_instance = DataUpdate('../config.json')
company_list = ['7267.T']
# # 9984.T 7203.T 4911.T 6594.T 8316.T 8411.T 8035.T 6758.T 8591.T "0027.HK",
version = '0122'
# data_update_instance.update_all(version=version,target_company_code=company_list,force_skip=False,batch_size=5)
data_update_instance.update_all(version=version, force_skip=True, batch_size=50, num_workers=4)