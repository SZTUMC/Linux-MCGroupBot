import requests
import random
from FuncPack.UserAgentList import agent_list


def getLiveStatus(arg_roomid) -> str:
    """
    获取直播间状态的接口

    :return status_description 有四种状态['未知'，'未开播'，'直播中'，'轮播中']
    """
    response = requests.request("GET",
        url=f"https://api.live.bilibili.com/room/v1/Room/room_init?id={arg_roomid}",
        headers={
        'User-Agent': random.choice(agent_list),
        'Accept': '*/*',
        'Host': 'api.live.bilibili.com',
        'Connection': 'keep-alive',
        'Cookie': 'LIVE_BUVID=AUTO4617024351366173'
    }, data={})

    result = response.json()
    live_status = result['data']['live_status']
    status_description = '未知'
    if live_status == 0:
        status_description = '未开播'

    if live_status == 1:
        status_description = '直播中'

    if live_status == 2:
        status_description = '轮播中'

    return status_description
