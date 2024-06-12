import json
import requests
from utils.mylog import global_logger, global_logUtil
from config import *
from FuncPack.getGPTresponseFunc import getGPTresponse
from FuncPack.checkMCServerFunc import checkMCServer
from FuncPack.getBiliLiveStatusFunc import getLiveStatus
from FuncPack.getHypPlayerInfo import get_hyp_player_info
from flask import Flask, request, jsonify, send_from_directory

app = Flask(__name__)

# api接收消息的回调函数
@app.route('/api/recv', methods=['POST'])
def get_recv_msg() -> None:
    try:
        form = request.form
        context_type = form.get('type')

        # 文件与图片部分
        if context_type != 'text':

            if context_type != 'file':
                if context_type == 'system_event_push_notify':
                    return 'bot send', 200
                
                global_logger.warning("recv unknown type:" + context_type)
                return 'failed', 500

            file = request.files['content']
            pic_name = file.filename
            global_logger.info("recv file:" + pic_name)
            return 'ok', 200

        # 文本部分
        source = form.get('source')
        content = form.get('content')

        source_dict = json.loads(source)

        # 在群聊中
        if source_dict['room']:
            name = source_dict["from"]["payload"]["name"]
            roomName = source_dict["room"]["payload"]["topic"]
            isMentioned = form.get('isMentioned')
            global_logger.info(f'{name} in room {roomName} say: "{content}"')
            reply = process_group_recv_msg(name, content)

            global_logger.info(f'content:\n"{content}"\nreply:\n"{reply}"')

            response_data = {
                "success": True,
                "data": {
                    'type': 'text',
                    'content': reply
                }
            }

            if isMentioned == "1":
                global_logger.info(name + "@me")
            
            return response_data

        # 私信部分
        if source_dict['to']:
            name = source_dict["from"]["payload"]["name"]
            response_data = {
                "success": True,
                "data": {
                    'type': 'text',
                    'content': '@me!'
                }
            }
            global_logger.info(f'{name} send to you: "{content}"')
            return response_data

        return 'error', 400

    except Exception as e:
        global_logger.error('get_recv_msg error', e)
        # 处理异常情况
        response_data = {
            "success": False,
            "message": str(e)
        }

        return jsonify(response_data), 500


# 发送文件需处理成http url
@app.route('/<filename>')
def download(filename):
    return send_from_directory('weekdays_img', filename, as_attachment=True)


# 发送消息
@global_logUtil.logger_wrapper
def send_mc_group_msg(content: str, data_type: str = "text"):
    url = f"http://wxBotWebhook:3001/webhook/msg/v2?token={token}"

    payload = {
        "to": GROUP_NAME,
        "isRoom": True,
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
    global_logger.info(response.text)


# 发送给自己消息
@global_logUtil.logger_wrapper
def send_test_msg(content: str, data_type: str = "text"):
    url = f"http://wxBotWebhook:3001/webhook/msg/v2?token={token}"

    payload = {
        "to": TEST_PERSON,
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
    global_logger.info(response.text)


# 处理群聊接收的消息，生成回复
@global_logUtil.logger_wrapper
def process_group_recv_msg(name: str, context: str) -> str:
    global history_context
    sendmsg = ''

    # 迎新助手
    if context.find('加入了群聊') != -1:
        with open('text/join.txt', mode='r', encoding='utf-8') as f:
            sendmsg = f.read()

    # 命令功能
    if context[0] == '/':

        if context == '/mcs':
            global_logger.info('发送服务器状态')
            sendmsg = checkMCServer(logger=logger)

        elif context == '/live':
            global_logger.info('发送直播状态')
            status = getLiveStatus(arg_roomid=31149017)
            sendmsg += f'深圳技术大学Minecraft社直播间：\n直播状态：{status}\n直播间地址：https://live.bilibili.com/31149017'

        elif context[:5] == '/qhyp':
            if len(context) > 6:
                result = get_hyp_player_info(context[6:])
                if(result):
                    sendmsg += f"玩家id：{context[6:]}"
                    sendmsg += ("\n\n大厅信息：\n大厅等级："+result[0][0]+"\n在线状态："+result[0][1]+"\n上次登录时间："+result[0][2])
                    sendmsg += ("\n\n起床战争统计：\n起床等级："+result[1][0]+"\n击杀死亡比："+result[1][1]+"\n胜负比："+result[1][2]+"\n床破坏数："+result[1][3])
                    sendmsg += "\n\n————感谢WGtian的技术支持"
                else:
                    sendmsg = "查询失败，请重新查询或检查玩家id是否拼写正确"
            else:
                sendmsg = "查询失败，请重新查询或检查玩家id是否拼写正确"

        # fixme: 实际缺失某些文件导致查不到本地文档，本地知识库
        elif context[:6] == '/agent':
            if len(context) > 7:
                send_mc_group_msg('正在查询与整理中，思考完成前不会有响应')
                result = qa({"query": context[7:]})
                localMsg = result['result'] + '\n'
                for index, source in enumerate(result['source_documents']):
                    localMsg += (f'\n来源{index + 1}:' + source.dict()['metadata']['source'])

                context = '/agent'
                sendmsg = localMsg

        else:
            # 查询已有的命令
            try:
                with open('cmd' + context + '.txt', mode='r', encoding='utf-8') as f:
                    global_logger.info("load cmd:" + context)
                    sendmsg = f.read()
                    global_logger.info("have load msg:\n" + sendmsg)

            except FileNotFoundError:
                global_logger.error(f'未知命令: {context}')
                sendmsg = '未知命令'

    #todo: 提示词优化，记忆优化，请求GPT
    if context[:4] == "@Bot":
        if len(context) > 5:
            asker = name
            send_mc_group_msg('正在思考中，回复完成前不会有响应')
            new_msg = f'玩家{asker}说:' + context[5:] + '\n回复简短，限制在100字以内'
            history_context = getGPTresponse(
                base_url=OPENAI_API_BASE,
                history_context=history_context, 
                new_message=new_msg
            )
            answer = history_context[-1]["content"]
            sendmsg += f'@{asker}{context[4]}{answer}'

    # 发送查询结果
    if sendmsg:
        global_logger.info("sendmsg:\n"+sendmsg)
        if context != '/help':
            sendmsg += help_msg
        else:
            global_logger.info("help指令")

    return sendmsg