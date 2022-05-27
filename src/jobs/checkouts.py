import json
import scrapy
from scrapy_splash import SplashRequest
from jobs import START_URL, ACCOUNTS, LOGIN_SCRIPT,\
    BROWSER, SETTINGS, EVAL_JS_SCRIPT, ACCOUNT_URL, READER, DELAY
from scrapy.crawler import CrawlerProcess
from scrapy import Item, Field
from scrapy.loader import ItemLoader
from itemloaders.processors import Join, MapCompose, TakeFirst
import time
from scrapy.downloadermiddlewares.retry import RetryMiddleware
from scrapy.utils.response import response_status_message


class CustomRetryMiddleware(RetryMiddleware):

    def process_response(self, request, response, spider):
        if request.meta.get('dont_retry', False):
            return response
        if response.status in self.retry_http_codes:
            reason = response_status_message(response.status)
            return self._retry(request, reason, spider) or response

        # assert that title should show up in the page
        if response.status == 200 and not response.xpath(spider.retry_xpath):
            return self._retry(request, 'response got xpath "{}"'.format(spider.retry_xpath), spider) or response
        return response


class CheckoutItem(Item):
    title = Field()
    cover = Field()
    isbn = Field()
    author = Field()
    reader = Field()
    account = Field()


class JsonWriterPipeline:
    def __init__(self):
        self.file = open('items.jl', 'w')

    def process_item(self, item, spider):
        line = json.dumps(dict(item)) + "\n"
        self.file.write(line)
        return item


class CheckoutSpider(scrapy.Spider):

    name = 'checkout'
    start_urls = [START_URL]
    # TODO: use different user and switch active user
    username, password, nickname = ACCOUNTS[0]
    active_user = nickname
    retry_item = dict()
    retry_xpath = '//div[contains(@class, "text-p INITIAL_TITLE_SRCH")]/a/@title'

    def start_requests(self):
        script = LOGIN_SCRIPT.replace('$username', self.username)\
            .replace('$password', self.password)
        for url in self.start_urls:
            yield SplashRequest(
                url,
                self.parse,
                endpoint='execute',
                args={
                    'lua_source': script,
                    'ua': BROWSER
                },
                cache_args=['lua_source'],
                headers={'X-My-Header': 'value'},
                meta={'dont_retry': True},
            )

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
            time.sleep(DELAY)
            yield SplashRequest(
                ACCOUNT_URL,
                self.parse_checkout,
                endpoint='execute',
                args={
                    'lua_source': EVAL_JS_SCRIPT,
                    'ua': BROWSER,
                    # 'line': "console.log('Hi)"
                    'line': f"""document.querySelectorAll(".myCheckouts td.checkoutsBookInfo a")[{idx}].click()""",
                    'book': book_name,
                    'idx_id': idx
                },
                cache_args=['lua_source'],
                headers={'X-My-Header': 'value'},
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
        loader.add_value('account', self.nickname)
        yield loader.load_item()


if __name__ == '__main__':
    dl_middleware = SETTINGS['DOWNLOADER_MIDDLEWARES']
    dl_middleware['__main__.CustomRetryMiddleware'] = 550
    process = CrawlerProcess(settings={**SETTINGS,
                                       "ITEM_PIPELINES": {
                                           '__main__.JsonWriterPipeline': 100
                                       }})
    process.crawl(CheckoutSpider)
    process.start()
    # process.stop()
