import time
import hmac
import base64
import requests
from config import DingTalkAccessToken, DingTalkSecret

# Dingtalk robot webhook
class dingtalk():

    def __init__(self):
        self.access_token = DingTalkAccessToken
        self.secret = DingTalkSecret
        self.webhook = None

    def set_webhook(self):
        if self.secret is None:
            self.webhook = f"https://oapi.dingtalk.com/robot/send?access_token={self.access_token}"
        else:
            timestamp = str(round(time.time() * 1000))
            secret_enc = self.secret.encode('utf-8')
            string_to_sign = f"{timestamp}\n{self.secret}"
            string_to_sign_enc = string_to_sign.encode('utf-8')
            hmac_code = hmac.new(secret_enc, string_to_sign_enc, digestmod='sha256').digest()
            sign = base64.b64encode(hmac_code).decode('utf-8')
            # set webhook
            self.webhook = f"https://oapi.dingtalk.com/robot/send?access_token={self.access_token}&timestamp={timestamp}&sign={sign}"
    
    def post(self, send_body):
        if self.webhook is None:
            self.set_webhook()
        return requests.post(self.webhook, json=send_body)