from .utils import parse_jsw
from datetime import datetime
from os.path import dirname
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
import atexit, math ,hashlib, subprocess, time, random, threading
#import undetected_chromedriver as webdriver

wd_opt = Options()
wd_opt.headless = True
wd_opt.add_argument("--no-sandbox")
wd_opt.add_argument("--headless")
wd_opt.add_argument("--disable-gpu")
wd_opt.add_argument("--disable-software-rasterizer") 
wd_opt.add_experimental_option("excludeSwitches", ["enable-automation"])
wd_opt.add_experimental_option('useAutomationExtension', False)
wd = webdriver.Chrome(executable_path="./data/chromedriver.exe", chrome_options=wd_opt, service_args=['--verbose'], service_log_path=None)
atexit.register(lambda *_: wd.quit())

with open(dirname(__file__) + "/js/hsw.js") as fp:
    wd.execute_script(fp.read() + "; window.hsw = hsw")

hsw_time = 0
hsw_last = None
hsw_lock = threading.Lock()
def get_hsw(req):
    global hsw_time
    global hsw_last
    with hsw_lock:
        if time.time()-hsw_time > 5:
            proof = wd.execute_async_script(
                "window.hsw(arguments[0]).then(arguments[1])",
                req)
            hsw_last = proof
            hsw_time = time.time()
        else:
            proof = hsw_last + "".join(random.choices("ghijklmnopqrstuvwxyz", k=5))
    return proof

def get_hsl(req):
    x = "0123456789/:abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ"
    req = parse_jsw(req)

    def a(r):
        for t in range(len(r) - 1, -1, -1):
            if r[t] < len(x) - 1:
                r[t] += 1
                return True
            r[t] = 0
        return False

    def i(r):
        t = ""
        for n in range(len(r)):
            t += x[r[n]]
        return t

    def o(r, e):
        n = e
        hashed = hashlib.sha1(e.encode())
        o = hashed.hexdigest()
        t = hashed.digest()
        e = None
        n = -1
        o = []
        for n in range(n + 1, 8 * len(t)):
            e = t[math.floor(n / 8)] >> n % 8 & 1
            o.append(e)
        a = o[:r]
        def index2(x,y):
            if y in x:
                return x.index(y)
            return -1
        return 0 == a[0] and index2(a, 1) >= r - 1 or -1 == index2(a, 1)
    
    def get():
        for e in range(25):
            n = [0 for i in range(e)]
            while a(n):
                u = req["payload"]["d"] + "::" + i(n)
                if o(req["payload"]["s"], u):
                    return i(n)
                
    result = get()
    hsl = ":".join([
        "1",
        str(req["payload"]["s"]),
        datetime.now().isoformat()[:19] \
            .replace("T", "") \
            .replace("-", "") \
            .replace(":", ""),
        req["payload"]["d"],
        "",
        result
    ])
    return hsl