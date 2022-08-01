from .utils import cache_forever
import imagehash, base64
from PIL import Image
from io import BytesIO

class Task:
    def __init__(self, task_obj, challenge=None):
        self.challenge = challenge
        self.key = task_obj["task_key"]
        self.url = task_obj["datapoint_uri"]
    
    def _request(self, url, method="GET", http_client=None):
        http_client = http_client if http_client is not None \
                      else self.challenge.http_client
        return http_client.request(
            method,
            url,
            headers={"Accept-Encoding": "gzip, deflate, br"}
        )
    
    #@cache_forever()
    def content(self, **kw) -> bytes:
        resp = self._request(self.url, **kw)
        return resp.content
    
    #@cache_forever()
    def image(self, raw=False, encoded=False, **kw) -> Image.Image:
        content = self.content(**kw)
        if raw: return content
        if encoded: return base64.b64encode(content)
        return Image.open(BytesIO(content))

    #@cache_forever()
    def phash(self, size=16, **kw) -> str:
        image = self.image(**kw)
        phash = str(imagehash.phash(image, size))
        self._phash = phash
        return phash