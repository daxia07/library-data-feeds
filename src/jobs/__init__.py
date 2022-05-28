import os

from dotenv import load_dotenv
try:
    load_dotenv()
except IOError:
    pass

READER = os.environ.get("READER")
DELAY = int(os.environ.get("DELAY", "10"))
ACCOUNTS = [i.split(":") for i in os.environ.get("ACCOUNTS").split(" ")]
START_URL = os.environ.get("START_URL")
ACCOUNT_URL = START_URL.replace('mylists', 'account')
BROWSER = "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/51.0.2704.106 Safari/537.36"
LOGIN_SCRIPT = """
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
            splash:init_cookies(splash.args.cookies)
            assert(splash:go{
                splash.args.url,
                headers=splash.args.headers,
                http_method=splash.args.http_method,
                body=splash.args.body,
                })
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
            splash:runjs('document.querySelector("a.loginLink").click()')
            assert(splash:wait(5))
            local entries = splash:history()
            local last_response = entries[#entries].response
            return {
                url = splash:url(),
                headers = last_response.headers,
                http_status = last_response.status,
                cookies = splash:get_cookies(),
                html = splash:html(),
            }
        end
"""

EVAL_JS_SCRIPT = """
        function main(splash)
            splash:init_cookies(splash.args.cookies)
            assert(splash:go{
                splash.args.url,
                headers=splash.args.headers,
                http_method=splash.args.http_method,
                body=splash.args.body,
                })
            assert(splash:wait(2))
            splash:runjs(splash.args.line)
            assert(splash:wait(5))
            local entries = splash:history()
            local last_response = entries[#entries].response
            return {
                url = splash:url(),
                headers = last_response.headers,
                http_status = last_response.status,
                cookies = splash:get_cookies(),
                html = splash:html(),
            }
        end
"""

SETTINGS = {
    "SPLASH_URL": "http://0.0.0.0:8050",
    "DOWNLOADER_MIDDLEWARES": {
        'scrapy_splash.SplashCookiesMiddleware': 723,
        'scrapy_splash.SplashMiddleware': 725,
        'scrapy.downloadermiddlewares.httpcompression.HttpCompressionMiddleware': 810,
        'jobs.utils.CustomRetryMiddleware': 550,
    },
    "SPIDER_MIDDLEWARES": {
        'scrapy_splash.SplashDeduplicateArgsMiddleware': 100,
    },
    "DUPEFILTER_CLASS": 'scrapy_splash.SplashAwareDupeFilter',
    "HTTPCACHE_STORAGE": 'scrapy_splash.SplashAwareFSCacheStorage',
    'RETRY_TIMES': 5,
    # "DOWNLOAD_DELAY": 2,
    "AUTOTHROTTLE_ENABLED": True,
    # "AUTOTHROTTLE_START_DELAY": 2,
    # "SPLASH_COOKIES_DEBUG": True
    "AUTOTHROTTLE_TARGET_CONCURRENCY": 3
}


__all__ = ['READER', 'ACCOUNTS', 'START_URL', 'ACCOUNT_URL', 'BROWSER',
           'LOGIN_SCRIPT', 'EVAL_JS_SCRIPT', 'SETTINGS', 'DELAY', ]
