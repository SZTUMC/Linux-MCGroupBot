import requests
import json
import config

# 发送给自己消息
def send_test_msg(content: str, data_type: str = "text"):
    url = f"http://wxBotWebhook:3001/webhook/msg/v2?token={config.token}"

    payload = {
        "to": config.TEST_PERSON,
        "isRoom": False,
        "data": {
            "type": data_type,
            "content": content
        }
    }

    payload = json.dumps(payload)

    headers = {
        'User-Agent': 'Apifox/1.0.0 (https://apifox.com)',
        'Content-Type': 'application/json',
        'Accept': '*/*',
        'Host': 'wxBotWebhook:3001',
        'Connection': 'keep-alive'
    }

    response = requests.request("POST", url, headers=headers, data=payload)