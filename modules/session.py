from modules.cloudfare import Cloudfare
from modules.discord import DiscordApi
import httpx

class HttpSession:
    def __init__(self, proxy: str = None):
        self.base_headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/102.0.5005.61 Safari/537.36',
            'sec-ch-ua': '".Not/A)Brand";v="99", "Google Chrome";v="103", "Chromium";v="103"',
            'accept-language': 'en-US,en;q=0.9',
            'content-type': 'application/json',
            'referer': 'https://discord.com/',
            'origin': 'https://discord.com',
            'sec-ch-ua-platform': 'Windows',
            'sec-fetch-site': 'same-origin',
            'sec-ch-ua-mobile': '?0',
            'sec-fetch-dest': 'empty',
            'sec-fetch-mode': 'cors',
            'accept': '*/*',
        }
        self.proxies = {
            "http://": f"{proxy}",
            "https://": f"{proxy}",
        }
        self.http_client = httpx.Client(proxies=self.proxies, headers=self.base_headers, timeout=30)

    def get_cookies(self):
        response = self.http_client.get('https://discordapp.com/api/v9/experiments')
        r, m = Cloudfare().Get_CFParams(self.http_client)

        self.__cf_bm = Cloudfare().Get_CfBm(self.http_client, r, m)
        self.__dcfduid = response.cookies.get('__dcfduid')
        self.__sdcfduid = response.cookies.get('__sdcfduid')

        cookies = httpx.Cookies()
        cookies.set('locale', 'en', domain='discord.com')
        cookies.set('__cf_bm', self.__cf_bm, domain='.discord.com')
        cookies.set('__dcfduid', self.__dcfduid, domain='discord.com')
        cookies.set('__sdcfduid', self.__sdcfduid, domain='discord.com')
        self.http_client.cookies = cookies

        self.http_client.headers['x-fingerprint'] = response.json()['fingerprint']
        self.http_client.headers['cookie'] = f'__dcfduid={self.__dcfduid}; __sdcfduid={self.__sdcfduid}; locale=en; __cf_bm={self.__cf_bm}'

        DiscordApi.submit_trackers(self.http_client)
        
        #mdresp = self.http_client.get("https://discord.com/api/v9/auth/location-metadata")