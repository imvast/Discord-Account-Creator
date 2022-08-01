class RequestException(Exception):
    pass

class UnsupportedScheme(RequestException):
    pass

class EmptyResponse(RequestException):
    pass

class UnsupportedEncoding(RequestException):
    pass