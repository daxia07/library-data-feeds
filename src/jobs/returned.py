from datetime import datetime

import scrapy
from itemloaders.processors import MapCompose
from scrapy_splash import SplashRequest
from scrapy.crawler import CrawlerProcess
from jobs.utils import DefaultItemLoader, login, BaseItem, load_concise_book, convert_date
from jobs import START_URL, ACCOUNTS, LOGIN_SCRIPT, \
    BROWSER, SETTINGS, EVAL_JS_SCRIPT, ACCOUNT_URL, READER


class ReturnedItem(BaseItem):
    checked_out = scrapy.Field()
    returned = scrapy.Field()
    media = scrapy.Field()


class ReturnedItemLoader(DefaultItemLoader):
    checked_out_in = MapCompose(convert_date)
    returned_in = MapCompose(convert_date)


class ReturnedSpider(scrapy.Spider):
    name = 'history'
    start_urls = [START_URL]
    custom_settings = {
        'ITEM_PIPELINES': {
            'jobs.pipelines.DBPipeline': 100
        }
    }

    def start_requests(self):
        for req in login(LOGIN_SCRIPT, self.__getattribute__('username'),
                         self.__getattribute__('password'),
                         self.start_urls, self.parse):
            yield req

    def parse(self, response, **kwargs):
        row_path = '//table[contains(@class, "checkoutsHistoryList")]//tr[@class="checkoutsHistoryLine"]'
        rows = response.xpath(row_path)
        if not rows:
            return
        for idx in range(len(rows)):
            # fetch each item and attach data to the request meta
            # item to parse
            checked_out = rows[idx].xpath('.//td[3]/text()').get()
            returned = rows[idx].xpath('.//td[4]/text()').get()
            data = {'checked_out': checked_out, 'returned': returned}
            yield SplashRequest(
                ACCOUNT_URL,
                self.parse_detail,
                endpoint='execute',
                args={
                    'lua_source': EVAL_JS_SCRIPT,
                    'ua': BROWSER,
                    'line': """document.querySelectorAll("table.checkoutsHistoryList tr.checkoutsHistoryLine a")"""
                            f"""[{idx}].click()""",
                },
                cache_args=['lua_source'],
                headers={'X-My-Header': 'value'},
                meta={'expect_xpath': '//div[contains(@class, "text-p INITIAL_TITLE_SRCH")]/a/@title',
                      'data': data
                      }
            )

    def parse_detail(self, response):
        tab = response.xpath('//div[@class="detail_main"]')
        loader = ReturnedItemLoader(ReturnedItem(), selector=tab, response=response)
        loader.add_value('account', self.__getattribute__('nickname'))
        loader.add_value('reader', READER)
        load_concise_book(loader)
        if loader.get_output_value('isbn'):
            media = 'book'
            loader.add_xpath('isbn', '//div[contains(@class, "text-p ISBN")]/text()')
        else:
            media = 'CD'
            loader.add_value('isbn', loader.get_output_value('title'))
        loader.add_value('media', media)
        data = response.request.meta.get('data')
        for k in data.keys():
            loader.add_value(k, data[k])
        yield loader.load_item()


if __name__ == '__main__':
    process = CrawlerProcess(settings=SETTINGS)
    # TODO: use different user and switch active user
    username, password, nickname = ACCOUNTS[0]
    process.crawl(ReturnedSpider, username=username, password=password, nickname=nickname)
    process.start()
