import json
import pymongo
from itemloaders.processors import MapCompose, TakeFirst, Join
from scrapy import Item, Field
from scrapy.downloadermiddlewares.retry import RetryMiddleware
from scrapy.loader import ItemLoader
from scrapy.utils.response import response_status_message
from scrapy_splash import SplashRequest
from jobs import BROWSER, MONGO_URL, MONGO_DB
from itemadapter import ItemAdapter
from scrapy.exceptions import DropItem
from datetime import datetime


class CustomRetryMiddleware(RetryMiddleware):

    def process_response(self, request, response, spider):
        if request.meta.get('dont_retry', False):
            return response
        if response.status in self.retry_http_codes:
            reason = response_status_message(response.status)
            return self._retry(request, reason, spider) or response

        # assert that title should show up in the page
        if response.status == 200:
            if request.meta.get('expect_xpath', False) and not response.xpath(request.meta.get('expect_xpath')):
                return self._retry(request, 'response did not have xpath "{}"'
                                   .format(request.meta.get('expect_xpath')), spider) or response
            if request.meta.get('unexpect_xpath', False) and response.xpath(request.meta.get('unexpect_xpath')):
                return self._retry(request, 'response did not have xpath "{}"'
                                   .format(request.meta.get('unexpect_xpath')), spider) or response
        return response


def login(login_script, username, password, urls, callback):
    script = login_script.replace('$username', username) \
        .replace('$password', password)
    for url in urls:
        yield SplashRequest(
            url,
            callback,
            endpoint='execute',
            args={
                'lua_source': script,
                'ua': BROWSER
            },
            cache_args=['lua_source'],
            headers={'X-My-Header': 'value'},
            meta={'expect_xpath': '//*[@id="libInfoContainer"]/span[contains(@class, "welcome")]'},
        )


class JsonWriterPipeline:
    def __init__(self):
        self.file = open('items.jl', 'w')

    def process_item(self, item, spider):
        line = json.dumps(dict(item)) + "\n"
        self.file.write(line)
        return item


class DefaultItemLoader(ItemLoader):
    default_input_processor = MapCompose(str.strip)
    default_output_processor = TakeFirst()
    desc_out = Join()


class BookItem(Item):
    title = Field()
    cover = Field()
    isbn = Field()
    author = Field()
    account = Field()
    reader = Field()


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
