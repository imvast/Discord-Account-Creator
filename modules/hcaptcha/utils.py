from base64 import b64encode, b64decode
from urllib.parse import urljoin
import json
import random
import string
import threading
from .. import xrequests as requests

def cache_forever():
    cache = None
    is_set = False
    def _cache_forever(func):
        def cached(*args, **kwargs):
            nonlocal cache
            nonlocal is_set
            if is_set:
                return cache
            cache = func(*args, **kwargs)
            is_set = True
            return cache
        return cached
    return _cache_forever

captcha_version = None
captcha_version_lock = threading.Lock()
def get_captcha_version():
    global captcha_version
    with captcha_version_lock:
        if captcha_version is None:
            resp = None
            url = "https://hcaptcha.com/1/api.js"
            while True:
                resp = requests.get(url)
                if "location" in resp.headers:
                    url = urljoin(url, resp.headers["location"])
                else:
                    break
            captcha_version = resp.text.split("v1/", 1)[1].split("/", 1)[0]
        return captcha_version

def random_widget_id():
    widget_id = "".join(random.choices(
        string.ascii_lowercase + string.digits,
        k=random.randint(10, 12)
    ))
    return widget_id

def parse_jsw(req):
    fields = req.split(".")
    return {
        "header": json.loads(b64decode(fields[0])),
        "payload": json.loads(b64decode(fields[1] + ("=" * ((4 - len(fields[1]) % 4) % 4)))),
        "signature": b64decode(fields[2].replace("_", "/").replace("-", "+")  + ("=" * ((4 - len(fields[1]) % 4) % 4))),
        "raw": {
            "header": fields[0],
            "payload": fields[1],
            "signature": fields[2]
        }
    }
    
def parse_proxy_string(proxy_str):
    if not proxy_str:
        return

    proxy_str = proxy_str.rpartition("://")[2]
    auth, _, fields = proxy_str.rpartition("@")
    fields = fields.split(":", 2)

    if len(fields) == 2:
        hostname, port = fields
        if auth:
            auth = "Basic " + b64encode(auth.encode()).decode()
        addr = (hostname.lower(), int(port))
        print(f"[$] PROXY : {auth}, {addr}")
        return auth, addr

    elif len(fields) == 3:
        hostname, port, auth = fields
        auth = "Basic " + b64encode(auth.encode()).decode()
        addr = (hostname.lower(), int(port))
        print(f"[$] PROXY : {auth}, {addr}")
        return auth, addr
    
    raise Exception(f"Unrecognized proxy format: {proxy_str}")