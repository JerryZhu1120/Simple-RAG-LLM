import json
from vecdb import VecDB

with open('../../config.json') as f:
    config = json.load(f)

vecdb = VecDB(config)

import time
for i in range(30):
    vecdb.show_index_build_status()
    time.sleep(1)