import socket
import traceback
import pickle
import json
import logging
from mcstatus import JavaServer
from FuncPack.severListPing import generate_server


# 参数
# servers = [
#     ("SZTU build and guess Game", "sztumc.cn", 25571),
#     ("A TerraFirma: Rebirth Official Server Pack", "sztumc.cn", 25572)
# ]
with open('FuncPack/mcserver.json', 'r', encoding='utf-8') as f:
    servers : dict = json.load(f)

private_ip = "10.108.0.209"

def checkMCServer(logger: logging.Logger) -> str:
    """
    获取服务器状态

    :return sendmsg获取的结果格式化文本
    """
    sendmsg = '''
幽匿感测体服务器小助手：

检测到在线服务器：'''
    sendmsg_behind = '\n离线服务器:'
    have_offline_server = False

    for server_json in servers:
        url = server_json['public_url'] + ":" + str(server_json['port'])
        create_time = server_json['create_time']

        server = JavaServer.lookup(url)

        try:
            title = server.query().motd.raw
            version = server.query().software.version
            names = server.query().players.names
            sendmsg += f'服务器标题：{title}'
            sendmsg += f'\n- 开档日期：{create_time}'
            if server_json['public_url'].endswith("sztumc.cn"):
                sendmsg += f"\n- 内网(校园网): {private_ip}:{server_json['port']}"
            sendmsg += f'\n- 公网地址：{url}'
            sendmsg += f'\n- 版本：{version}'
            sendmsg += f'\n- 在线玩家人数：{len(names)}'
            if len(names) > 0:
                sendmsg += '\n- 玩家列表：'
                for name in names:
                    sendmsg += f'\n    {name}'

            sendmsg += '\n' # 分隔空行

        except TimeoutError as timeout_error:
            try:
                sendmsg += generate_server(
                    logger=logger, server_config=server_json
                )
            except:
                have_offline_server = True

                # 起始已包含一个回车
                sendmsg_behind += \
f"""
- 上次服务器标题：{server_json['motd']}
- 公网地址: {url}"""
                if server_json['public_url'].endswith("sztumc.cn"):
                    sendmsg_behind += f"\n- 内网(校园网): {private_ip}:{server_json['port']}"
                
                sendmsg_behind += "\n"
        except:
            
            traceback.print_exc()

    if have_offline_server:
        sendmsg += sendmsg_behind

    return sendmsg[:-1]


def getImportantNotice():
    return """重要提示：
1.有学校内网优先连内网ip，是公网速率的20倍（200M，1ms以内延时），在外请连公网ip
2.高速跑图吃带宽，公网延迟暴增多是因为有人鞘翅或航海跑图，所以跑图尽量一起
3.经数据统计周目包平均存活时间为两周，看到在线人数为0的多数是过了这个期限，反之则是新出的
4.有标注ipv6支持的可以开手机流量然后热点连接，三大运营商基本支持ipv6，校园网暂不公开ipv6
5.如无特殊情况，节假日出新周目，可以提前推荐新包，以便安排排期
---- 更新于 2024年5月29日 by Mick4994
"""

