import json
from datetime import datetime

import pymongo
from itemadapter import ItemAdapter
from scrapy.exceptions import DropItem

from jobs import MONGO_URL, MONGO_DB


class DBPipeline:

    def __init__(self, collection):
        self.collection = collection
        self.mongo_uri = MONGO_URL
        self.mongo_db = MONGO_DB
        self.failure_count = 0
        self.client = None
        self.unique_keys = []
        self.total = 0

    @classmethod
    def from_crawler(cls, crawler):
        return cls(
            crawler.spider.name
        )

    def open_spider(self, spider):
        self.client = pymongo.MongoClient(self.mongo_uri)
        self.mongo_db = self.client[self.mongo_db]
        index_info = self.mongo_db[self.collection].index_information()
        indexes = [i for i in index_info.keys() if 'unique' in index_info[i].keys()]
        assert len(indexes) == 1
        key = index_info[indexes[0]]['key']
        self.unique_keys = [x[0] for x in key]
        assert len(self.unique_keys) > 0

    def close_spider(self, spider):
        # check total again
        # do clean up accordingly
        if self.collection in ['holds', 'checkouts']:
            # remove items that are not found in this process
            pass
        self.client.close()

    def process_item(self, item, spider):
        # find filter
        document = ItemAdapter(item).asdict()
        index = dict(filter(lambda i: i[0] in self.unique_keys, document.items()))
        # add timestamp
        try:
            self.mongo_db[self.collection].replace_one(index,
                                                       {
                                                           **document,
                                                           "last_modified": datetime.utcnow()
                                                       }, True)
            return item
        except pymongo.errors.DuplicateKeyError:
            self.failure_count += 1
            if self.failure_count > 3:
                spider.close_down = True
                raise DropItem(f"Duplicate item found: {item}")


class JsonWriterPipeline:
    def __init__(self):
        self.file = open('items.jl', 'w')

    def process_item(self, item, spider):
        line = json.dumps(dict(item)) + "\n"
        self.file.write(line)
        return item
