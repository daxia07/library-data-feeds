import scrapy
from scrapy_splash import SplashRequest
from jobs import START_URL, ACCOUNTS, LOGIN_SCRIPT, BROWSER, SETTINGS, EVAL_JS_SCRIPT, ACCOUNT_URL
from scrapy.crawler import CrawlerProcess


class CheckoutSpider(scrapy.Spider):

    start_urls = [START_URL]
    # TODO: use different user
    username, password = ACCOUNTS[0]
    name = 'checkout'

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
            # book_name = href.xpath('text()').get()
            # print(book_name)
            pass
        yield SplashRequest(
            ACCOUNT_URL,
            self.parse_checkout,
            endpoint='execute',
            args={
                'lua_source': EVAL_JS_SCRIPT,
                'ua': BROWSER,
                'line': "console.log('Hi)"
                # 'line': f"""document.querySelectorAll(".myCheckouts td.checkoutsBookInfo a")[{idx}].click()"""
            },
            cache_args=['lua_source'],
            headers={'X-My-Header': 'value'},
        )

        # if next page, follow next page
        # for href in response.xpath('').extract():
        #     # next page to parse
        #     yield None

    def parse_checkout(self, response):
        print("OK")
        pass


if __name__ == '__main__':
    process = CrawlerProcess(settings=SETTINGS)
    process.crawl(CheckoutSpider)
    process.start()
    # process.stop()

