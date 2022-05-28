import scrapy
from scrapy_splash import SplashRequest
from scrapy.crawler import CrawlerProcess
from jobs.utils import DefaultItemLoader, login, BookItem
from jobs import START_URL, ACCOUNTS, LOGIN_SCRIPT, \
    BROWSER, SETTINGS, EVAL_JS_SCRIPT, ACCOUNT_URL, READER


class CheckoutItem(BookItem):
    renewed = scrapy.Field()
    due_date = scrapy.Field()


class CheckoutSpider(scrapy.Spider):
    name = 'checkout'
    start_urls = [START_URL]
    custom_settings = {
        'ITEM_PIPELINES': {
            'jobs.utils.JsonWriterPipeline': 100
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
            data = {'renewed': renewed, 'due_date': due_date}
            yield SplashRequest(
                ACCOUNT_URL,
                self.parse_checkout,
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

    def parse_checkout(self, response):
        tab = response.xpath('//div[@class= "detail_main"]')
        loader = DefaultItemLoader(CheckoutItem(), selector=tab, response=response)
        loader.add_xpath('cover', '//div[@class= "detail_main"]//img/@src')
        loader.add_xpath('title', '//div[contains(@class, "text-p INITIAL_TITLE_SRCH")]/a/@title')
        loader.add_xpath('isbn', '//div[contains(@class, "text-p ISBN")]/text()')
        loader.add_xpath('author', '//div[contains(@class, "text-p PERSONAL_AUTHOR")]/a/@title')
        loader.add_value('reader', READER)
        loader.add_value('account', self.__getattribute__('nickname'))
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
