import json
import time

from src.api.warcraftlogs import WarcraftLogs


# noinspection PyCompatibility
from test.mocks.request_mock import RequestMock


class WarcraftLogsMock(WarcraftLogs):
    def __init__(self, reports_response, all_parses_responses):
        """
        :param reports_response: RAW JSON response
        :param all_parses_responses: ARRAY OF RAW JSON responses, one per player
        """
        super().__init__("")

        self.reports_response = reports_response

        # set the parse times to the current time, so we're always in the week window
        modified = []
        for parse_response in all_parses_responses:
            decoded = json.loads(parse_response)

            for kill in decoded:
                for spec in kill["specs"]:
                    for data in spec["data"]:
                        data["start_time"] = time.time() * 1000
            modified.append(json.dumps(decoded))

        self.all_parses_responses = modified

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
            if self._parse_call_count >= len(self.all_parses_responses):
                return RequestMock("{}")

            to_return = self.all_parses_responses[self._parse_call_count]
            self._parse_call_count += 1

            return RequestMock(to_return)
        else:
            raise Exception("Unable to mock endpoint %s" % url)
