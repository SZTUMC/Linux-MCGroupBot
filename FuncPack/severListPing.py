import socket
import struct
import logging
import json
import traceback
from io import StringIO

def unpack_varint(s):
    d = 0
    for i in range(5):
        b = ord(s.recv(1))
        d |= (b & 0x7F) << 7*i
        if not b & 0x80:
            break
    return d

def pack_varint(d):
    o = b""
    while True:
        b = d & 0x7F
        d >>= 7
        o += struct.pack("B", b | (0x80 if d > 0 else 0))
        if d == 0:
            break
    return o

def pack_data(d):
    h = pack_varint(len(d))
    if type(d) == str:
        d = bytes(d, "utf-8")
    return h + d

def pack_port(i):
    return struct.pack('>H', i)

def get_info(host='localhost', port=25565):

    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.connect((host, port))

    s.send(pack_data(b"\x00\x00" + pack_data(host.encode('utf8')) + pack_port(port) + b"\x01"))
    s.send(pack_data("\x00"))

    unpack_varint(s)     # Packet length
    unpack_varint(s)     # Packet ID
    l = unpack_varint(s) # String length

    d = b""
    while len(d) < l:
        d += s.recv(1024)

    s.close()
    return json.loads(d.decode('utf8'))

def generate_server(logger: logging.Logger, server_config, trans=0):
    server_name = server_config['motd']
    port = server_config['port']
    host = server_config['public_url']
    create_time = server_config['create_time']
    
    data = ""
    try:
        data = get_info(host=host,port=port)
    # except socket.gaierror as e:
    #     raise Exception("服务器离线")
    
    except Exception as e:
        f = StringIO()
        traceback.print_exc(file=f)
        traceback_msg = f.getvalue()
        logger.error(traceback_msg)
    
    try:
        if data and data["players"]["online"] is not None:
            players_online = data["players"]["online"]
        else:
            players_online = "服务器离线"
    except Exception as e:
        players_online = "服务器离线"

    try:
        if data and data["players"]["online"] is not None and data["players"]["online"] != 0:
            players = [player["name"] for player in data["players"]["sample"]]
        else:
            players = "无"
    except Exception as e:
        players = "无"

    if trans == 1:
        for i in range(len(players)):
            if players[i] == "Anonymous Player":
                players[i] = "假人"
    
    if trans == 2:
        if players != "无":
            for i in range(len(players)):
                players[i] = "假人"

    json_data = f"服务器标题: {server_name}\n- \
        开档日期：{create_time}\n- \
        公网地址：{host}:{port}\n- \
        版本：{data['version']['name']}\n" \
            + "- 在线人数: {}\n".format(players_online)
    
    if players != "无":
        json_data = json_data + "- 玩家列表\n{}".format('\n'.join(players)) + "\n"

    return json_data
