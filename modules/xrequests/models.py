class Response:
    def __init__(self, status, message, headers, content):
        self.status_code = status
        self.reason = message
        self.headers = headers
        self.content = content

    def __repr__(self):
        return '<Response [{}]>'.format(self.status_code)
    
    def json(self):
        return __import__('json').loads(self.content)
    
    @property
    def text(self, method='UTF-8'):
        return self.content.decode(method, errors="ignore")
