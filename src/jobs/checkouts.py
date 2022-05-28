import scrapy
from scrapy_splash import SplashRequest
from jobs import START_URL, ACCOUNTS, LOGIN_SCRIPT,\
    BROWSER, SETTINGS, EVAL_JS_SCRIPT, ACCOUNT_URL, READER
from scrapy.crawler import CrawlerProcess
from scrapy import Item, Field
from scrapy.loader import ItemLoader
from itemloaders.processors import Join, MapCompose, TakeFirst


class CheckoutItem(Item):
    title = Field()
    cover = Field()
    isbn = Field()
    author = Field()
    reader = Field()
    account = Field()


class CheckoutSpider(scrapy.Spider):

    name = 'checkout'
    start_urls = [START_URL]
    custom_settings = {
        'ITEM_PIPELINES': {
            'jobs.utils.JsonWriterPipeline': 100
        }
    }

    def start_requests(self):
        from jobs.utils import login
        for req in login(LOGIN_SCRIPT, self.__getattribute__('username'),
                         self.__getattribute__('password'),
                         self.start_urls, self.parse):
            yield req

    def parse(self, response, **kwargs):
        # 1. find all element and loop over each item
        # 2. new splash page to render item
        # 3. create item
        # //div[contains(@class, 'Test')]
        book_path = '//div[contains(@class, "myCheckouts")]//td[contains(@class, "checkoutsBookInfo")]//a'
        links = response.xpath(book_path)
        if not links:
            return
        for idx in range(len(links)):
            # item to parse
            # click_id = href.xpath('@id').get()
            book_name = links[idx].xpath('text()').get()
            self.logger.info(f'Fetching data for {book_name}')
            # print(book_name)
            yield SplashRequest(
                ACCOUNT_URL,
                self.parse_checkout,
                endpoint='execute',
                args={
                    'lua_source': EVAL_JS_SCRIPT,
                    'ua': BROWSER,
                    # 'line': "console.log('Hi)"
                    'line': f"""document.querySelectorAll(".myCheckouts td.checkoutsBookInfo a")[{idx}].click()""",
                },
                cache_args=['lua_source'],
                headers={'X-My-Header': 'value'},
                meta={'expect_xpath': '//div[contains(@class, "text-p INITIAL_TITLE_SRCH")]/a/@title'}
            )

        # if next page, follow next page
        # for href in response.xpath('').extract():
        #     # next page to parse
        #     yield None

    def parse_checkout(self, response):
        tab = response.xpath('//div[@class= "detail_main"]')
        loader = ItemLoader(CheckoutItem(), selector=tab, response=response)
        loader.default_input_processor = MapCompose(str.strip)
        loader.default_output_processor = TakeFirst()
        loader.desc_out = Join()
        loader.add_xpath('cover', '//div[@class= "detail_main"]//img/@src')
        loader.add_xpath('title', '//div[contains(@class, "text-p INITIAL_TITLE_SRCH")]/a/@title')
        loader.add_xpath('isbn', '//div[contains(@class, "text-p ISBN")]/text()')
        loader.add_xpath('author', '//div[contains(@class, "text-p PERSONAL_AUTHOR")]/a/@title')
        loader.add_value('reader', READER)
        loader.add_value('account', self.__getattribute__('nickname'))
        yield loader.load_item()


if __name__ == '__main__':
    process = CrawlerProcess(settings=SETTINGS)
    # TODO: use different user and switch active user
    username, password, nickname = ACCOUNTS[0]
    process.crawl(CheckoutSpider, username=username, password=password, nickname=nickname)
    process.start()
    # process.stop()
