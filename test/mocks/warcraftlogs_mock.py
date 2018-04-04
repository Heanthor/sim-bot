from src.api.warcraftlogs import WarcraftLogs


# noinspection PyCompatibility
class WarcraftLogsMock(WarcraftLogs):
    def __init__(self, reports_response, all_parses_response):
        """
        :param reports_response: RAW JSON response
        :param all_parses_response: RAW JSON response
        """
        super().__init__("")

        self.reports_response = reports_response
        self.all_parses_response = all_parses_response

    def warcraftlogs_request(self, req_func, *args, **kwargs):
        """
        Mock API call with provided response instead
        Check the API call by inspecting the URL passed as first arg
        """

        url = args[0]

        # approximate a Requests response object
        def ret_obj(data_in):
            def json():
                return data_in

            def status_code():
                return 200

        if "reports" in url:
            return ret_obj(self.reports_response)
        elif "parses" in url:
            return ret_obj(self.all_parses_response)
        else:
            raise Exception("Unable to mock endpoint %s" % url)
