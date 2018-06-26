import json


class RequestMock:
    """
    Provide some methods and fields used as a Requests response
    """
    def __init__(self, data):
        self.data = data
        self.status_code = 200

    def json(self):
        return json.loads(self.data)
