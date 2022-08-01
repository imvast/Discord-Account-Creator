import uuid, time, json, random
from . import temp
from .models import Task
from .exceptions import HCaptchaError, ApiError
from .agents import random_agent
from .structures import FakeTime, Pe
from .utils import parse_proxy_string, random_widget_id, get_captcha_version
from .curves import gen_mouse_move
from urllib.parse import urlparse, urlencode
from requests import Session as HttpClient

FRAME_SIZE = (400, 600)
TASKS_PER_PAGE = 9
TASKS_PER_ROW = 3
TASK_IMAGE_SIZE = (123, 123)
TASK_IMAGE_START_POS = (11, 130)
TASK_IMAGE_PADDING = (5, 6)
VERIFY_BTN_POS = (314, 559)

class Challenge:
    base_url = "https://hcaptcha.com"
    frame_base_url = "https://newassets.hcaptcha.com"

    def __init__(self,
                 sitekey, page_url, http_proxy: str = None,
                 invisible=None, widget_id=None, version=None,
                 agent=None, http_client=None):
        invisible = invisible if invisible is not None else None
        widget_id = widget_id if widget_id is not None else random_widget_id()
        version = version if version is not None else get_captcha_version()
        agent = agent if agent is not None else random_agent()
        http_client = http_client if http_client is not None else HttpClient()

        self.sitekey = sitekey
        self.page = urlparse(page_url)
        self.version = version
        self.invisible = invisible
        self.widget_id = widget_id
        self.http_client = http_client
        self.agent = agent
        self._http_proxy = http_proxy #parse_proxy_string(http_proxy)

        self.key = None
        self.type = None
        self.question = None
        self.tasks = []
        self.token = None
        self._spec = None
        self._cookies = {}

        self._time = FakeTime()
        self._top = Pe(self._time)
        self._frame = Pe(self._time)
        
        self._set_identity()
        self._check_config()
        self._get_captcha()
        self._frame.set_data("dct", self._frame._manifest["st"])

    def solve(self, answers):
        if self.token:
            return self.token

        self._simulate_solve(answers)

        resp = self._request(
            method="POST",
            url=f"{self.base_url}/checkcaptcha/{self.key}?s={self.sitekey}",
            headers={
                "Host": "hcaptcha.com",
                "Connection": "keep-alive",
                "User-Agent": self.agent.user_agent,
                "Content-Type": "application/json;charset=UTF-8",
                "Accept": "*/*",
                "Origin": f"{self.frame_base_url}",
                "Referer": f"{self.frame_base_url}/",
                "Accept-Encoding": "gzip, deflate, br",
                "Accept-Language": "en-US,en;q=0.9"
            },
            data=json.dumps({
                "answers": {
                    task.key: "true" if task.key in answers or task in answers \
                              else "false"
                    for task in self.tasks
                },
                "c": json.dumps(self._spec, separators=(",", ":")) \
                     if self._spec is not None else "null",
                "job_mode": self.type,
                "motionData": json.dumps({
                    **self._frame.get_data(),
                    "topLevel": self._top.get_data(),
                    "v": 1
                }, separators=(",", ":")),
                "n": self._get_proof() if self._spec is not None else "",
                "serverdomain": self.page.hostname,
                "sitekey": self.sitekey,
                "v": self.version
            }, separators=(",", ":"))
        )
        data = resp.json()
        self.token = data["generated_pass_UUID"]
        return self.token

    def _request(self, method, url, headers=None, data=None, json=None):
        headers = headers if headers is not None else {}
        if 0 and self._cookies:
            headers["Cookie"] = "; ".join(f"{k}={v}" for k,v in self._cookies.items())
        resp = self.http_client.request(method, url, headers=headers, data=data, proxies={"http": f"http://{self._http_proxy}", "https": f"http://{self._http_proxy}"})

        if resp.status_code == 429:
            raise ApiError(resp.status_code, resp.text)

        if resp.headers["content-type"].startswith("application/json"):
            data = resp.json()

            if data.get("pass") == False or data.get("success") == False:
                raise ApiError(resp.status_code, resp.text)
                
            if "c" in data:
                self._spec = data["c"]
                
        if "set-cookie" in resp.headers:
            if isinstance(resp.headers["set-cookie"], str):
                resp.headers["set-cookie"] = [resp.headers["set-cookie"]]
            for cookie in resp.headers["set-cookie"]:
                key, value = cookie.split(";")[0].split("=", 1)
                self._cookies[key] = value
        
        return resp

    def _check_config(self):
        self._request(
            method="POST",
            url=f"{self.base_url}/checksiteconfig?host={self.page.hostname}&sitekey={self.sitekey}&sc=1&swa=1",
            headers={
                "Host": "hcaptcha.com",
                "Connection": "keep-alive",
                "Cache-Control": "no-cache",
                "User-Agent": self.agent.user_agent,
                "Content-Type": "application/json; charset=utf-8",
                "Accept": "*/*",
                "Origin": f"{self.frame_base_url}",
                "Referer": f"{self.frame_base_url}/",
                "Accept-Encoding": "gzip, deflate, br",
                "Accept-Language": "en-US,en;q=0.9"
            }
        )

    def _get_captcha(self):
        resp = self._request(
            method="POST",
            url=f"{self.base_url}/getcaptcha?s={self.sitekey}",
            headers={
                "Host": "hcaptcha.com",
                "Connection": "keep-alive",
                "Accept": "application/json",
                "User-Agent": self.agent.user_agent,
                "Content-Type": "application/x-www-form-urlencoded",
                "Origin": f"{self.frame_base_url}",
                "Referer": f"{self.frame_base_url}/",
                "Accept-Encoding": "gzip, deflate, br",
                "Accept-Language": "en-US,en;q=0.9"
            },
            data=urlencode({
                "v": self.version,
                "sitekey": self.sitekey,
                "host": self.page.hostname,
                "hl": "en",
                "motionData": json.dumps({
                    **self._frame.get_data(),
                    "v": 1,
                    "topLevel": self._top.get_data(),
                    "session": [],
                    "widgetList": [self.widget_id],
                    "widgetId": self.widget_id,
                    "href": self.page.geturl(),
                    "prev": {
                        "escaped": False,
                        "passed": False,
                        "expiredChallenge": False,
                        "expiredResponse": False
                    }
                }, separators=(",", ":")),
                "n": self._get_proof() if self._spec is not None else "",
                "c": json.dumps(self._spec, separators=(",", ":")) \
                     if self._spec is not None else "null"
            })
        )
        data = resp.json()
        
        if "generated_pass_UUID" in data:
            self.token = data["generated_pass_UUID"]
            return
        
        self.key = data["key"]
        self.type = data["request_type"]
        self.question = data["requester_question"]["en"]
        self.tasks = [Task(t, self) for t in data["tasklist"]]
        

    def _get_proof(self):
        if self._spec["type"] == "hsw":
            return temp.get_hsw(self._spec["req"])
        if self._spec["type"] == "hsl":
            return temp.get_hsl(self._spec["req"])
        raise HCaptchaError(
            f"Unknown proof type '{self._spec['type']}'")


    def _set_identity(self):
        self._top.record()
        self._time.sleep(random.uniform(1, 2))
        self._frame.record()
        self._top.set_data("sc", {
            "availWidth": self.agent.avail_width,
            "availHeight": self.agent.avail_height,
            "width": self.agent.width,
            "height": self.agent.height,
            "colorDepth": self.agent.color_depth,
            "pixelDepth": self.agent.pixel_depth,
            "availLeft": 0,
            "availTop": 0
        })
        self._top.set_data("nv", {
            "vendorSub": self.agent.vendor_sub,
            "productSub": self.agent.product_sub,
            "vendor": self.agent.vendor,
            "maxTouchPoints": self.agent.max_touch_points,
            "userActivation": {},
            "doNotTrack": self.agent.do_not_track,
            "geolocation": {},
            "connection": {},
            "webkitTemporaryStorage": {},
            "webkitPersistentStorage": {},
            "hardwareConcurrency": self.agent.hardware_concurrency,
            "cookieEnabled": True,
            "appCodeName": self.agent.app_code_name,
            "appName": self.agent.app_name,
            "appVersion": self.agent.app_version,
            "platform": self.agent.platform,
            "product": self.agent.product,
            "userAgent": self.agent.user_agent,
            "language": self.agent.language,
            "languages": self.agent.languages,
            "onLine": self.agent.on_line,
            "webdriver": self.agent.webdriver,
            "serial": {},
            "scheduling": {},
            "mediaCapabilities": {},
            "permissions": {},
            "locks": {},
            "wakeLock": {},
            "usb": {},
            "mediaSession": {},
            "clipboard": {},
            "credentials": {},
            "keyboard": {},
            "mediaDevices": {},
            "storage": {},
            "serviceWorker": {},
            "deviceMemory": self.agent.device_memory,
            "hid": {},
            "presentation": {},
            "userAgentData": {},
            "bluetooth": {},
            "xr": {},
            "plugins": self.agent.plugins
        })
        self._top.set_data("dr", f"https://{self.page.hostname}/")
        self._top.set_data("inv", False)
        self._top.set_data("exec", False)
        self._top.circ_buff_push("wn", [
            2844,
            1478,
            1, # devicePixelRatio
            self._time.ms_time()
        ])
        self._top.circ_buff_push("xy", [
            0, # scrollX
            0, # scrollY
            1, # document.documentElement.clientWidth / window.innerWidth
            self._time.ms_time()
        ])

    def _simulate_solve(self, answers):
        total_pages = max(1, int(len(self.tasks)/TASKS_PER_PAGE))
        cursor_pos = (
            random.randint(1, 5),
            random.randint(300, 350)
        )

        for page in range(total_pages):
            page_tasks = self.tasks[page*TASKS_PER_PAGE:(page+1)*TASKS_PER_PAGE]
            for task_index, task in enumerate(page_tasks):
                if not task.key in answers and not task in answers:
                    continue
                task_pos = (
                    (TASK_IMAGE_SIZE[0] * int(task_index % TASKS_PER_ROW))
                        + TASK_IMAGE_PADDING[0] * int(task_index % TASKS_PER_ROW)
                        + random.randint(10, TASK_IMAGE_SIZE[0])
                        + TASK_IMAGE_START_POS[0],
                    (TASK_IMAGE_SIZE[1] * int(task_index / TASKS_PER_ROW))
                        + TASK_IMAGE_PADDING[1] * int(task_index / TASKS_PER_ROW)
                        + random.randint(10, TASK_IMAGE_SIZE[1])
                        + TASK_IMAGE_START_POS[1],
                )
                for event in gen_mouse_move(cursor_pos, task_pos, self._time,
                        offsetBoundaryX=0, offsetBoundaryY=0, leftBoundary=0,
                        rightBoundary=FRAME_SIZE[0], upBoundary=FRAME_SIZE[1],
                        downBoundary=0):
                    self._frame.record_event("mm", event)
                # TODO: add time delay for mouse down and mouse up
                self._frame.record_event("md", event)
                self._frame.record_event("mu", event)
                cursor_pos = task_pos
            
            # click verify/next/skip btn
            btn_pos = (
                VERIFY_BTN_POS[0] + random.randint(5, 50),
                VERIFY_BTN_POS[1] + random.randint(5, 15),
            )
            for event in gen_mouse_move(cursor_pos, btn_pos, self._time,
                        offsetBoundaryX=0, offsetBoundaryY=0, leftBoundary=0,
                        rightBoundary=FRAME_SIZE[0], upBoundary=FRAME_SIZE[1],
                        downBoundary=0):
                self._frame.record_event("mm", event)
            # TODO: add time delay for mouse down and mouse up
            self._frame.record_event("md", event)
            self._frame.record_event("mu", event)
            cursor_pos = btn_pos
