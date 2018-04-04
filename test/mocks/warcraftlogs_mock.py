from src.api.warcraftlogs import WarcraftLogs


# noinspection PyCompatibility
class WarcraftLogsMock(WarcraftLogs):
    def __init__(self, reports_response, all_parses_response):
        super().__init__("")

        self.reports_response = reports_response
        self.all_parses_response = all_parses_response

    def warcraftlogs_request(self, req_func, *args, **kwargs):
        """
        Mock API call with provided response instead
        Check the API call by inspecting the URL passed as first arg
        """

        url = args[0]

        if "reports" in url:
            return self.reports_response
        elif "parses" in url:
            return self.all_parses_response
        else:
            raise Exception("Unable to mock endpoint %s" % url)
