import json, time, httpx, cv2, os, json, base64
import tensorflow as tf
from keras.models import load_model
tf.debugging.disable_traceback_filtering()
import numpy as np
from . import hcaptcha
from .console import Console


model = load_model('./data/data.h5')
config = json.load(open("./data/config.json"))

class CaptchaSolver:
    @staticmethod
    def get_captcha_key_by_hand() -> str:
        return input('Captcha-key: ')

    @staticmethod
    def get_captcha_key(static_proxy: str, proxy: str, site_key: str = str(config['site_key'])) -> str:
        task_payload = {
            'clientKey': config['captcha_key'],
            'task': {
                'userAgent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/102.0.5005.61 Safari/537.36',
                'websiteKey': site_key,
                'websiteURL': 'https://discord.com',
                'type': 'HCaptchaTask',

                'proxyPassword': static_proxy.split('@')[0].split(':')[1],
                'proxyAddress': static_proxy.split('@')[1].split(':')[0],
                'proxyLogin': static_proxy.split('@')[0].split(':')[0],
                'proxyPort': int(static_proxy.split('@')[1].split(':')[1]),
                'proxyType': 'http',
            }
        }
        key = None
        print(task_payload)

        with httpx.Client(proxies=f'http://{proxy}',
                          headers={'content-type': 'application/json', 'accept': 'application/json'},
                          timeout=30) as client:
            try:
                task_id = client.post(f'https://api.{config["captcha_api"]}/createTask', json=task_payload).json()[
                    'taskId']

                print('captcha task -->', task_id)

                get_task_payload = {
                    'clientKey': config['captcha_key'],
                    'taskId': task_id
                }

                while key is None:
                    try:
                        response = client.post(f'https://api.{config["captcha_api"]}/getTaskResult',
                                               json=get_task_payload,
                                               timeout=30).json()

                        print(response)
                        if 'ERROR_PROXY_CONNECT_REFUSED' in str(response):
                            return 'ERROR'

                        if 'ERROR' in str(response):
                            return 'ERROR'

                        if response['status'] == 'ready':
                            key = response['solution']['gRecaptchaResponse']
                        else:
                            time.sleep(3)
                    except Exception as e:

                        if 'ERROR_PROXY_CONNECT_REFUSED' in str(e):
                            key = 'ERROR'
                        else:
                            pass
                return key

            except Exception as e:
                return e

    @staticmethod
    def get_captcha_by_ai(proxy: str, client = None):
        Console.debug("[*] SOLVING...")
        ch = hcaptcha.Challenge(
            sitekey="4c672d35-0701-42b2-88c3-78380b0db560",
            page_url="https://discord.com",
            http_proxy=proxy
        )

        if ch.token:
            return ch.token
        
        answers = []
        for tile in ch.tasks:
            image = tile.image(raw=True)
            img = cv2.imdecode(np.fromstring(image, np.uint8), cv2.IMREAD_COLOR)
            img = cv2.resize(img,(config['image_size'],config['image_size']))
            img = np.expand_dims(img, axis=0)
            res = np.argmax(model.predict(img, verbose=0),axis=1)

            if res == 0:
                img_type = 'airplaine'
            if res == 1:
                img_type = 'bicycle'
            if res == 2:
                img_type = 'boat'
            if res == 3:
                img_type = 'motorbus'
            if res == 4:
                img_type = 'motorcycle'
            if res == 5:
                img_type = 'seaplane'
            if res == 6:
                img_type = 'train'
            if res == 7:
                img_type = 'truck'

            if img_type in ch.question:
                answers.append(tile)

        try:
            token = ch.solve(answers)
            return token
        except hcaptcha.ApiError as e:
            Console.debug(f"[-] ApiError: {e}")

            
