import requests
import json
import traceback
from typing import List


def getGPTresponse(
        base_url: str,
        history_context: List,
        new_message: str
) -> List:
    """
    封装gptapi，可以发送文本提问，返回文本回答

    :params history_context 上次历史消息记录
    :params new_message 提问的消息
    :return history_context 合并后的历史消息记录
    """

    api_key = os.environ["OPENAI_API_KEY"]

    # 读取系统提示词
    with open('text/system_prompt.txt', mode='r', encoding='utf-8') as f:
        sys_context = f.read()

    # 系统提示词
    sys_prompt = [
        {
            "role": "system",
            "content": sys_context
        }
    ]

    # 用户新提问
    new_prompt = [
        {
            "role": "user",
            "content": new_message
        }
    ]

    # 防止过长超max_token, 超过十个进行裁剪
    if len(history_context) > 10:
        history_context = history_context[5:]

    # 组成新消息
    messages = sys_prompt + history_context + new_prompt

    payload = json.dumps({
        "model": "gpt-3.5-turbo",
        "messages": messages
    })

    # 日志记录
    print('sendtoGPT!')

    # 发送请求
    response = requests.request("POST",
                                url=base_url + "/v1/chat/completions",
                                headers={
                                    'Accept': 'application/json',
                                    'Authorization': 'Bearer ' + api_key,
                                    'User-Agent': 'Apifox/1.0.0 (https://apifox.com)',
                                    'Content-Type': 'application/json',
                                    'Host': 'api.nextapi.fun',
                                    'Connection': 'keep-alive'
                                },
                                data=payload
                                )

    # 组成新的历史总表
    result = response.json()
    ans = result["choices"][0]["message"]
    history_context = messages + [ans]

    # 每次保存结果
    with open(file='text/historyGPT.txt', mode='a', encoding='utf-8') as f:
        f.write(str(history_context) + '\n')

    return history_context
