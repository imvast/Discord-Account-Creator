from colorama import Fore, init;init()
import os, redisc, threading, time, json, keyboard, datetime, discord
from pystyle import *

config = json.load(open("./data/config.json"))
lock = threading.Lock()

class Console:
    _generated, _verified, _locked, _unlocked, _proxy_err, _cap_worker, _hcap_solved = 0, 0, 0, 0, 0, 0, 0

    @staticmethod
    def debug(content: str):
        if config['debug'] == True:
            if "429" in str(content): content = None; Console._proxy_err += 1
            if '"pass":false' in str(content): content = None#'[-] Exception worker: hsw-unsuccessful'
            if '"success":false' in str(content): content = None#'[-] Exception worker: hsw-unsuccessful'
            if content != None:
                content = content.replace('[+]', f'[{Fore.LIGHTGREEN_EX} + {Fore.RESET}]{Fore.CYAN}').replace('[*]', f'[{Fore.LIGHTMAGENTA_EX} * {Fore.RESET}]{Fore.CYAN}').replace('[/]', f'[{Fore.CYAN} / {Fore.RESET}]{Fore.CYAN}').replace('[-]', f'[{Fore.RED} - {Fore.RESET}]{Fore.CYAN}')
                lock.acquire()
                print(f'[{Fore.CYAN}{datetime.datetime.fromtimestamp(time.time()).strftime("%H:%M:%S")}{Fore.RESET}] [{Fore.CYAN}DEBUG{Fore.RESET}] {Fore.BLUE}〢{Fore.RESET} {content}{Fore.RESET}', flush=True)
                lock.release()
            else: pass
            
    @staticmethod
    def info(content: str):
        lock.acquire()
        content = content.replace('[+]', f'[{Fore.LIGHTGREEN_EX} + {Fore.RESET}]{Fore.CYAN}').replace('[*]', f'[{Fore.LIGHTMAGENTA_EX} * {Fore.RESET}]{Fore.CYAN}').replace('[/]', f'[{Fore.CYAN} / {Fore.RESET}]{Fore.CYAN}').replace('[-]', f'[{Fore.RED} - {Fore.RESET}]{Fore.CYAN}')
        print(f'[{Fore.CYAN}{datetime.datetime.fromtimestamp(time.time()).strftime("%H:%M:%S")}{Fore.RESET}] [{Fore.CYAN}INFO{Fore.RESET}]  {Fore.BLUE}〢{Fore.RESET} {content}{Fore.RESET}', flush=True)
        lock.release()

    @staticmethod
    def printf(content: str):
        lock.acquire()
        print(content.replace('[+]', f'[{Fore.LIGHTGREEN_EX} + {Fore.RESET}]').replace('[*]', f'[{Fore.LIGHTYELLOW_EX} * {Fore.RESET}]').replace('[/]', f'[{Fore.CYAN} / {Fore.RESET}]').replace('[-]', f'[{Fore.RED} ✘ {Fore.RESET}]'))
        lock.release()

    @staticmethod
    def title_thread():
        start_time = time.time()
        while True:
            time.sleep(0.1)
            work_token_min = round(Console._generated / ((time.time() - start_time) / 60))
            all_token_min = round(Console._generated + Console._locked / ((time.time() - start_time) / 60))
            cap_solve_rate = round(Console._hcap_solved / ((time.time() - start_time) / 60))
            ctime = round(time.time() - start_time, 1)
            os.system(f'title [VTG - vast#6969] Stats: [L: {Console._locked} / U: {Console._unlocked}] - Verified: {Console._verified} - Unchecked: {Console._generated - (Console._locked + Console._unlocked)} | CapSolvd: {Console._hcap_solved} @ {cap_solve_rate}/m | ProxyERR: {Console._proxy_err} | Workers: {Console._cap_worker} - Threads: {threading.active_count()} | {all_token_min}/m - {work_token_min}V/m | Elapsed: {ctime}s'.replace('|', '^|'))

    @staticmethod
    def print_logo():
        os.system('cls' if os.name == 'nt' else 'clear')
        banner = f"""
  {Fore.CYAN}
  {Fore.CYAN} ██▒   █▓▄▄▄█████▓  ▄████ 
  {Fore.CYAN}▓██░   █▒▓  ██▒ ▓▒ ██▒ ▀█▒
  {Fore.CYAN} ▓██  █▒░▒ ▓██░ ▒░▒██░▄▄▄░                  {Fore.BLUE}vast#6969
  {Fore.CYAN}  ▒██ █░░░ ▓██▓ ░ ░▓█  ██▓          {Fore.BLUE}https://github.com/imvast
  {Fore.CYAN}   ▒▀█░    ▒██▒ ░ ░▒▓███▀▒
  {Fore.CYAN}   ░ ▐░    ▒ ░░    ░▒   ▒                 {Fore.RED}DEBUG: {config["debug"]}
  {Fore.CYAN}   ░ ░░      ░      ░   ░ 
  {Fore.CYAN}     ░░    ░      ░ ░   ░ 
  {Fore.CYAN}      ░                 ░ 
  {Fore.CYAN}     ░                    
""" + Fore.RESET
        print(banner)
