import scrapy
from scrapy_splash import SplashRequest
from scrapy.crawler import CrawlerProcess
from jobs.utils import DefaultItemLoader, login, BookItem
from jobs import START_URL, ACCOUNTS, LOGIN_SCRIPT, \
    BROWSER, SETTINGS, EVAL_JS_SCRIPT, ACCOUNT_URL, READER


class HoldsItem(BookItem):
    status = scrapy.Field()
    location = scrapy.Field()
    expire_date = scrapy.Field()
    rank = scrapy.Field()
    media = scrapy.Field()


class HoldsSpider(scrapy.Spider):
    name = 'holds'
    start_urls = [START_URL]
    custom_settings = {
        'ITEM_PIPELINES': {
            'jobs.utils.DBPipeline': 100
        }
    }

    def start_requests(self):
        for req in login(LOGIN_SCRIPT, self.__getattribute__('username'),
                         self.__getattribute__('password'),
                         self.start_urls, self.parse):
            yield req

    def parse(self, response, **kwargs):
        # expect 10 items
        row_path = '//table[contains(@class, "holdsList")]//tr[@class="pickupHoldsLine"]'
        rows = response.xpath(row_path)
        if not rows:
            return
        for idx in range(len(rows)):
            # fetch each item and attach data to the request meta
            # item to parse
            status = rows[idx].xpath('.//td[@class="holdsStatus"]/text()').get()
            location = rows[idx].xpath('.//td[@class="holdsPickup"]/text()').get()
            expire_date = rows[idx].xpath('.//td[@class="holdsDate"]/text()').get()
            rank = rows[idx].xpath('.//td[@class="holdsRank"]/text()').get()
            data = {'status': status, 'location': location,
                    'expire_date': expire_date, 'rank': rank}
            yield SplashRequest(
                ACCOUNT_URL,
                self.parse_checkout,
                endpoint='execute',
                args={
                    'lua_source': EVAL_JS_SCRIPT,
                    'ua': BROWSER,
                    'line': f"""document.querySelectorAll("table.holdsList td.holdsID a")[{idx}].click()""",
                },
                cache_args=['lua_source'],
                headers={'X-My-Header': 'value'},
                meta={'expect_xpath': '//div[contains(@class, "text-p INITIAL_TITLE_SRCH")]/a/@title',
                      'data': data
                      }
            )

    def parse_checkout(self, response):
        tab = response.xpath('//div[@class= "detail_main"]')
        loader = DefaultItemLoader(HoldsItem(), selector=tab, response=response)
        loader.add_xpath('cover', '//div[@class= "detail_main"]//img/@src')
        loader.add_xpath('title', '//div[contains(@class, "text-p INITIAL_TITLE_SRCH")]/a/@title')
        loader.add_xpath('isbn', '//div[contains(@class, "text-p ISBN")]/text()')
        loader.add_xpath('author', '//div[contains(@class, "text-p PERSONAL_AUTHOR")]/a/@title')
        loader.add_value('account', self.__getattribute__('nickname'))
        if loader.get_output_value('isbn'):
            loader.add_value('media', 'book')
        else:
            loader.add_value('media', 'CD')
        data = response.request.meta.get('data')
        loader.add_value('reader', READER)
        for k in data.keys():
            loader.add_value(k, data[k])
        yield loader.load_item()


if __name__ == '__main__':
    process = CrawlerProcess(settings=SETTINGS)
    # TODO: use different user and switch active user
    username, password, nickname = ACCOUNTS[0]
    process.crawl(HoldsSpider, username=username, password=password, nickname=nickname)
    process.start()
