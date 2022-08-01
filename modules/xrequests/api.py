from . import sessions

def request(method, url, **kwargs):
    with sessions.Session() as session:
        return session.request(method=method, url=url, **kwargs)

def get(url, **kwargs):
    return request("GET", url, **kwargs)

def post(url, **kwargs):
    return request("POST", url, **kwargs)

def options(url, **kwargs):
    return request("OPTIONS", url, **kwargs)

def head(url, **kwargs):
    return request("HEAD", url, **kwargs)

def put(url, **kwargs):
    return request("PUT", url, **kwargs)

def patch(url, **kwargs):
    return request("PATCH", url, **kwargs)

def delete(url, **kwargs):
    return request("DELETE", url, **kwargs)
