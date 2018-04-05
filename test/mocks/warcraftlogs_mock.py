from src.api.warcraftlogs import WarcraftLogs


# noinspection PyCompatibility
from test.mocks.RequestMock import RequestMock


class WarcraftLogsMock(WarcraftLogs):
    def __init__(self, reports_response, all_parses_responses):
        """
        :param reports_response: RAW JSON response
        :param all_parses_responses: ARRAY OF RAW JSON responses, one per player
        """
        super().__init__("")

        self.reports_response = reports_response
        self.all_parses_responses = all_parses_responses

        # each time a parse is requested, return a different one and increment the count
        self._parse_call_count = 0

    def warcraftlogs_request(self, req_func, *args, **kwargs):
        """
        Mock API call with provided response instead
        Check the API call by inspecting the URL passed as first arg
        """

        url = args[0]

        if "reports" in url:
            return RequestMock(self.reports_response)
        elif "parses" in url:
            to_return = self.all_parses_responses[self._parse_call_count]
            self._parse_call_count += 1

            return RequestMock(to_return)
        else:
            raise Exception("Unable to mock endpoint %s" % url)
