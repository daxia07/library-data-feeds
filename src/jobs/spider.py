import scrapy
from scrapy_splash import SplashRequest
from jobs import START_URL, ACCOUNTS
from scrapy.crawler import CrawlerProcess


class BookSpider(scrapy.Spider):

    start_urls = [START_URL]
    username, password = ACCOUNTS[0]
    name = 'book'

    def start_requests(self):
        script = """
        function wait_for_element(splash, css, maxwait)
          -- Wait until a selector matches an element
          -- in the page. Return an error if waited more
          -- than maxwait seconds.
          if maxwait == nil then
              maxwait = 10
          end
          return splash:wait_for_resume(string.format([[
            function main(splash) {
              var selector = '%s';
              var maxwait = %s;
              var end = Date.now() + maxwait*1000;
        
              function check() {
                if(document.querySelector(selector)) {
                  splash.resume('Element found');
                } else if(Date.now() >= end) {
                  var err = 'Timeout waiting for element';
                  splash.error(err + " " + selector);
                } else {
                  setTimeout(check, 200);
                }
              }
              check();
            }
          ]], css, maxwait))
        end
         
        
        function main(splash)
            assert(splash:go(splash.args.url))
            assert(splash:wait(2))
            wait_for_element(splash, "a.loginLink")
            local login_button = splash:select('a.loginLink')
            login_button.click()
            splash:set_viewport_full()
            assert(splash:wait(1))
            wait_for_element(splash, "a.loginLink")
            local search_input = splash:select('input[name=j_username]')   
            search_input:send_text("$username")
            local search_input = splash:select('input[name=j_password]')
            search_input:send_text("$password")
            assert(splash:wait(1))
            wait_for_element(splash, "input#submit_0")
            local submit_button = splash:select('input#submit_0')
            submit_button:click()
            wait_for_element(splash, "input#submit_0")
            assert(splash:wait(2))
            return splash:html()
        end
        """
        script = script.replace('$username', self.username)\
            .replace('$password', self.password)
        for url in self.start_urls:

            yield SplashRequest(
                url,
                self.parse_result,
                endpoint='execute',
                args={
                    'lua_source': script,
                    'ua': "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/51.0.2704.106 Safari/537.36"
                }
            )

    def parse(self, response, **kwargs):
        pass

    def parse_result(self, response):
        pass


if __name__ == '__main__':
    process = CrawlerProcess(settings={
        "FEEDS": {
            "items.json": {"format": "json"},
        },
        "SPLASH_URL": "http://0.0.0.0:8050",
        "DOWNLOADER_MIDDLEWARES": {
            'scrapy_splash.SplashCookiesMiddleware': 723,
            'scrapy_splash.SplashMiddleware': 725,
            'scrapy.downloadermiddlewares.httpcompression.HttpCompressionMiddleware': 810,
        },
        "SPIDER_MIDDLEWARES": {
            'scrapy_splash.SplashDeduplicateArgsMiddleware': 100,
        },
        "DUPEFILTER_CLASS": 'scrapy_splash.SplashAwareDupeFilter',
        "HTTPCACHE_STORAGE": 'scrapy_splash.SplashAwareFSCacheStorage'
    })

    process.crawl(BookSpider)
    process.start()
