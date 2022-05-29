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


def login(login_script, username, password, urls, callback, next_page=''):
    script = login_script.replace('$username', username) \
        .replace('$password', password)
    for url in urls:
        yield SplashRequest(
            url,
            callback,
            endpoint='execute',
            args={
                'lua_source': script,
                'ua': BROWSER,
                'next_page': next_page
            },
            cache_args=['lua_source'],
            headers={'X-My-Header': 'value'},
            meta={'expect_xpath': '//*[@id="libInfoContainer"]/span[contains(@class, "welcome")]'},
        )


def remove_whitespace(line):
    if isinstance(line, str):
        return line.strip()
    return line


class DefaultItemLoader(ItemLoader):
    default_input_processor = MapCompose(remove_whitespace)
    default_output_processor = TakeFirst()
    desc_out = Join()


class BaseItem(Item):
    title = Field()
    cover = Field()
    isbn = Field()
    author = Field()
    account = Field()
    reader = Field()


def load_concise_book(loader):
    loader.add_xpath('cover', '//div[@class="detail_main"]//img/@src')
    loader.add_xpath('title', '//div[contains(@class, "text-p INITIAL_TITLE_SRCH")]/a/@title')
    loader.add_xpath('author', '//div[contains(@class, "text-p PERSONAL_AUTHOR")]/a/@title')
    loader.add_xpath('isbn', '//div[contains(@class, "text-p ISBN")]/text()')


def load_detail_book(loader):
    load_concise_book(loader)
    loader.add_xpath('language', '//div[contains(@class, "text-p LANGUAGE")]/text()')
    loader.add_xpath('publication', '//div[contains(@class, "text-p PUBLICATION_INFO")]/text()')
    loader.add_xpath('physical', '//div[contains(@class, "text-p PHYSICAL_DESC")]/text()')
    loader.add_xpath('series', '//div[contains(@class, "text-p SERIES")]/a/text()')
    loader.add_xpath('abstract', '//div[contains(@class, "text-p ABSTRACT")]/text()')
    loader.add_xpath('subject_term', '//div[contains(@class, "text-p SUBJECT_TERM")]/a/text()')
    loader.add_xpath('contents', '//div[contains(@class, "text-p CONTENTS")]/text()')
    loader.add_xpath('genre_term', '//div[contains(@class, "text-p GENRE_TERM")]/a/text()')
    loader.add_xpath('added_title', '//div[contains(@class, "text-p ADDED_TITLE")]/text()')
    loader.add_xpath('general_note', '//div[contains(@class, "text-p GENERAL_NOTE")]/text()')
    loader.add_xpath('added_author', '//div[contains(@class, "text-p ADDED_AUTHOR")]/a/text()')
    loader.add_xpath('available_num', '//span[@class="totalAvailable"]/text()')
    loader.add_xpath('summary', 'normalize-space(//div[@id="unbound_summary"]/div[1]/div[1])')


def convert_date(x):
    from datetime import datetime
    try:
        x = datetime.strptime(x.strip(), '%d/%m/%y %H:%M %p')
    except ValueError:
        x = datetime.strptime(x.strip(), '%d/%m/%y')
    return x
