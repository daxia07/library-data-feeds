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
        if response.status == 200:
            if request.meta.get('expect_xpath', False) and not response.xpath(request.meta.get('expect_xpath')):
                return self._retry(request, 'response did not have xpath "{}"'
                                   .format(request.meta.get('expect_xpath')), spider)\
                       or response
            if request.meta.get('unexpect_xpath', False) and response.xpath(request.meta.get('unexpect_xpath')):
                return self._retry(request, 'response did not have xpath "{}"'
                                   .format(request.meta.get('unexpect_xpath')), spider) \
                   or response

        return response
