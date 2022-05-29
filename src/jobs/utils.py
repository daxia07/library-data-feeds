from itemloaders.processors import MapCompose, TakeFirst, Join
from scrapy import Item, Field
from scrapy.downloadermiddlewares.retry import RetryMiddleware
from scrapy.loader import ItemLoader
from scrapy.utils.response import response_status_message
from scrapy_splash import SplashRequest
from jobs import BROWSER


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


def input_processor(line):
    if isinstance(line, str):
        return line.strip()
    return line


class DefaultItemLoader(ItemLoader):
    default_input_processor = MapCompose(input_processor)
    default_output_processor = TakeFirst()
    desc_out = Join()


class BookItem(Item):
    title = Field()
    cover = Field()
    isbn = Field()
    author = Field()
    account = Field()
    reader = Field()

