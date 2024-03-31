import requests
import json
import time
import random
from FuncPack.UserAgentList import agent_list


def getDailyColdKnowledge(arg_uid) -> tuple[str, str]:
    """
    获取东南大学Minecraft社b站号的【每日冷知识】动态

    :return (
            content: str -每日冷知识文本内容，以标题与描述内容组成
            img_url: str -每日冷知识的配图链接
            )
    @Deprecated
    :return (
            content: str -每日冷知识文本内容，以标题与描述内容组成
            img_filename: str -保存该动态配图的文件路径
            )
    """
    # 请求头
    headers = {
       'User-Agent': random.choice(agent_list),
       'Accept': '*/*',
       'Host': 'api.vc.bilibili.com',
       'Connection': 'keep-alive'
    }

    request_url = f"https://api.vc.bilibili.com/dynamic_svr/v1/dynamic_svr/space_history?host_uid={arg_uid}"
    response = requests.request("GET", request_url, headers=headers, data={})

    # 解析需要的字段
    root_result = response.json()
    extract_required_fields = root_result['data']['cards'][0]['card']
    extract_required_fields_dict = json.loads(
        extract_required_fields
    )

    # 提取文本和图片链接
    content = extract_required_fields_dict['item']['description']
    img_url = extract_required_fields_dict['item']['pictures'][0]['img_src']

    # # 存图片
    # img_filename = time.strftime('%Y_%m_%d',
    #                              time.localtime(time.time())
    #                              )
    # img_filename = './DailyColdKnowledgeImgData/' + img_filename + '.png'
    # img_file = requests.get(img_url)
    # with open(img_filename, 'wb') as f:
    #     f.write(img_file.content)

    return content, img_url
