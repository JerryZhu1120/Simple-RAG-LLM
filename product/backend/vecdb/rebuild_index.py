import json
from vecdb import VecDB

with open('../../config.json') as f:
    config = json.load(f)

vecdb = VecDB(config)

vecdb.rebuild_index()

