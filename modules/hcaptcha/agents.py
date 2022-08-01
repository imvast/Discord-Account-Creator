class Agent:
    def __init__(self):
        self.user_agent = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/102.0.5005.61 Safari/537.36"
        self.product_sub = "20030107"
        self.vendor_sub = ""
        self.vendor = "Google Inc."
        self.max_touch_points = 0
        self.do_not_track = None
        self.hardware_concurrency = 16
        self.cookie_enabled = True
        self.app_code_name = "Mozilla"
        self.app_name = "Netscape"
        self.app_version = "5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/102.0.5005.61 Safari/537.36"
        self.platform = "Win32"
        self.product = "Gecko"
        self.language = "en-US"
        self.languages = ["en-US"]
        self.on_line = True
        self.webdriver = False
        self.device_memory = 8
        self.plugins = [
            "internal-pdf-viewer",
            "mhjfbmdgcfjbbpaeojofohoefgiehjai",
            "internal-nacl-plugin"
        ]

        self.width = 2560
        self.height = 1440
        self.avail_width = 2560
        self.avail_height = 1400
        self.color_depth = 24
        self.pixel_depth = 24

def random_agent():
    return Agent()