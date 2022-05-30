import scrapy
from itemloaders.processors import MapCompose
from scrapy_splash import SplashRequest
from scrapy.crawler import CrawlerProcess
from jobs.utils import DefaultItemLoader, login, BaseItem, load_detail_book
from jobs import START_URL, ACCOUNTS, LOGIN_SCRIPT, \
    BROWSER, SETTINGS, EVAL_JS_SCRIPT, BOOK_URL


class BooksItem(BaseItem):
    language = scrapy.Field()
    publication = scrapy.Field()
    physical = scrapy.Field()
    series = scrapy.Field()
    abstract = scrapy.Field()
    subject_term = scrapy.Field()
    contents = scrapy.Field()
    genre_term = scrapy.Field()
    added_title = scrapy.Field()
    general_note = scrapy.Field()
    added_author = scrapy.Field()
    available_num = scrapy.Field()
    summary = scrapy.Field()


class BooksItemLoader(DefaultItemLoader):
    subject_term_out = MapCompose(lambda x: x)
    genre_term_out = MapCompose(lambda x: x)
    available_num_in = MapCompose(int)
    summary_out = MapCompose(lambda x: x.rstrip(' (read less)'))


class BooksSpider(scrapy.Spider):
    name = 'books'
    start_urls = [START_URL]
    custom_settings = {
        'ITEM_PIPELINES': {
            'jobs.pipelines.DBPipeline': 100
        }
    }
    # limit max number of pages
    max_page = 500

    def __init__(self, *args, **kwargs):
        super(BooksSpider, self).__init__(*args, **kwargs)
        self.current_page = 1

    def start_requests(self):
        for req in login(LOGIN_SCRIPT, self.__getattribute__('username'),
                         self.__getattribute__('password'),
                         self.start_urls, self.parse,
                         next_page=BOOK_URL):
            yield req

    def parse(self, response, **kwargs):
        rows = response.xpath('//div[@class="displayDetailLink"]/a')
        if not rows:
            return
        for idx in range(len(rows)):
            yield SplashRequest(
                response.url,
                self.parse_detail,
                endpoint='execute',
                args={
                    'lua_source': EVAL_JS_SCRIPT,
                    'ua': BROWSER,
                    'line': f"""document.querySelectorAll("div.displayDetailLink a")[{idx}].click()""",
                },
                cache_args=['lua_source'],
                headers={'X-My-Header': 'value'},
                meta={'expect_xpath': '//div[contains(@class, "text-p INITIAL_TITLE_SRCH")]/a/@title'}
            )
        # if next page exists follow it
        next_page = response.xpath('//a[@id="NextPageBottom"]').extract()
        if next_page:
            # next page to parse
            self.current_page += 1
            if self.current_page <= self.max_page:
                yield SplashRequest(
                    response.url,
                    self.parse,
                    endpoint='execute',
                    args={
                        'lua_source': EVAL_JS_SCRIPT,
                        'ua': BROWSER,
                        'line': f"""document.querySelectorAll("a#NextPageBottom")[0].click()""",
                    },
                    cache_args=['lua_source'],
                    headers={'X-My-Header': 'value'},
                    meta={'expect_xpath': '//div[@id="resultsWrapper"]'}
                )

    def parse_detail(self, response):
        tab = response.xpath('//div[@class= "detail_main"]')
        loader = BooksItemLoader(BooksItem(), selector=tab, response=response)
        load_detail_book(loader)
        yield loader.load_item()


if __name__ == '__main__':
    process = CrawlerProcess(settings=SETTINGS)
    # TODO: use different user and switch active user
    username, password, nickname = ACCOUNTS[0]
    process.crawl(BooksSpider, username=username, password=password, nickname=nickname)
    process.start()
