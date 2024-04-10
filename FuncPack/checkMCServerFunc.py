import socket
import traceback
from mcstatus import JavaServer

# 参数
servers = {
    "sztumc.cn": 25565,
    "sztumc.cn": 25567,
    "sztumc.top": 25566,
}
private_ip = "10.108.0.209"


def search_minecraft_server(host, port):
    try:
        # 初始化变量
        status, protocol, version, title, numplayers, maxplayers = \
            "未知状态", "\000", "\000", "\000", "\000", "\000"

        # 向服务器发送请求
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.connect((host, port))
        s.sendall(b'\xFE\x01')

        # 把接受到的数据中00 00 之间的数据进行隔段操作以方便对数据操作
        data = s.recv(1024).split(b'\x00\x00')

        # 结束请求
        s.close()

        # 检查data是否为空数据,可以使用print(data)查看数据结构
        if len(data) >= 3:
            packet_id = data[0][0]
            if packet_id == 255:
                status = "在线"
                protocol = data[1].decode('utf-8', 'ignore').replace("\x00", "")
                version = data[2].decode('utf-8', 'ignore').replace("\x00", "")
                title = data[3].decode('utf-8', 'ignore').replace("\x00", "")
                numplayers = data[4].decode('utf-8', 'ignore').replace("\x00", "")
                maxplayers = data[5].decode('utf-8', 'ignore').replace("\x00", "")
            else:
                status = "未知状态"
        else:
            status = "未知状态"

        return status, protocol, version, title, numplayers, maxplayers

    except Exception as e:
        print("Error:", e)
        return "离线", "\000", "\000", "\000", "\000", "\000"


def checkMCServer() -> str:
    """
    获取服务器状态

    :return sendmsg获取的结果格式化文本
    """
    sendmsg = '检测到服务器：'
    for host, port in servers.items():
        server = JavaServer.lookup(host)

        sendmsg += '\n'

        status, protocol, version, title, numplayers, maxplayers \
            = search_minecraft_server(host, port)

        if status == "在线":
            sendmsg += f"""{title}:
服务器ip(外网): {host}
内网(校园网): {private_ip}:{port}
服务器状态:{status}
游戏版本:{version}
当前玩家数:{numplayers}"""
            try:
                names = server.query().players.names
                if len(names) > 0:
                    sendmsg += '\n玩家列表：'
                    for name in names:
                        sendmsg += f'\n{name}'
                sendmsg += '\n'
            except:
                traceback.print_exc()
        else:
            sendmsg += f"""离线服务器:
服务器ip(外网): {host}
内网(校园网): {private_ip}:{port}
"""
    return sendmsg[:-1]
