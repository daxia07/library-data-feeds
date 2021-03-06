import scrapy
from itemloaders.processors import MapCompose
from scrapy_splash import SplashRequest
from scrapy.crawler import CrawlerProcess
from jobs.utils import DefaultItemLoader, login, BaseItem, load_concise_book, convert_date
from jobs import START_URL, ACCOUNTS, LOGIN_SCRIPT, \
    BROWSER, SETTINGS, EVAL_JS_SCRIPT, ACCOUNT_URL, READER


class CheckoutItem(BaseItem):
    renewed = scrapy.Field()
    due_date = scrapy.Field()


class CheckoutItemLoader(DefaultItemLoader):
    renewed_in = MapCompose(int)
    due_date_in = MapCompose(convert_date)


class CheckoutSpider(scrapy.Spider):
    name = 'checkouts'
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
        # 1. find all element and loop over each item
        # 2. new splash page to render item
        # 3. yield item in callback
        # expect 40 items
        book_path = '//div[contains(@class, "myCheckouts")]//tr[@class="checkoutsLine"]'
        rows = response.xpath(book_path)
        if not rows:
            return
        for idx in range(len(rows)):
            renewed = rows[idx].xpath('.//td[@class="checkoutsRenewCount"]/text()').get()
            due_date = rows[idx].xpath('.//td[@class="checkoutsDueDate"]/text()').get()
            data = {'renewed': int(renewed), 'due_date': due_date}
            yield SplashRequest(
                ACCOUNT_URL,
                self.parse_detail,
                endpoint='execute',
                args={
                    'lua_source': EVAL_JS_SCRIPT,
                    'ua': BROWSER,
                    'line': f"""document.querySelectorAll(".myCheckouts td.checkoutsBookInfo a")[{idx}].click()""",
                },
                cache_args=['lua_source'],
                headers={'X-My-Header': 'value'},
                meta={'expect_xpath': '//div[contains(@class, "text-p INITIAL_TITLE_SRCH")]/a/@title',
                      'data': data
                      }
            )

    def parse_detail(self, response):
        tab = response.xpath('//div[@class= "detail_main"]')
        loader = CheckoutItemLoader(CheckoutItem(), selector=tab, response=response)
        loader.add_value('account', self.__getattribute__('nickname'))
        loader.add_value('reader', READER)
        load_concise_book(loader)
        data = response.request.meta.get('data')
        for k in data.keys():
            loader.add_value(k, data[k])
        yield loader.load_item()


if __name__ == '__main__':
    process = CrawlerProcess(settings=SETTINGS)
    # TODO: use different user and switch active user
    username, password, nickname = ACCOUNTS[0]
    process.crawl(CheckoutSpider, username=username, password=password, nickname=nickname)
    process.start()
