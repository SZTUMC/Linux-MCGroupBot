import os
import json
import requests
import threading
from flask import Flask, request, jsonify

import time

from utils import mylog

from langchain.embeddings.openai import OpenAIEmbeddings
from langchain.chains import RetrievalQA
from langchain.chat_models import ChatOpenAI
from langchain.vectorstores import Chroma

from FuncPack.getDailyColdKnowledge import getDailyColdKnowledge
from FuncPack.getGPTresponseFunc import getGPTresponse
from FuncPack.checkMCServerFunc import checkMCServer
from FuncPack.getBiliLiveStatusFunc import getLiveStatus

token = os.environ["TOKEN"]

GROUP_NAME = "深技大mc群(原夹总后援团)"

# 加载LLM
chat = ChatOpenAI(temperature=0)

# 初始化 openai 的 embeddings 对象
embeddings = OpenAIEmbeddings()

# 加载知识库
docsearch = Chroma(embedding_function=embeddings, persist_directory='mcdb')

# 创建问答对象
qa = RetrievalQA.from_chain_type(
    llm=chat, chain_type="stuff", retriever=docsearch.as_retriever(), return_source_documents=True
)

history_context = []

help_msg = "\n\ntips：输入/help获取命令表"

logger = mylog.log_init(path='logs/')

app = Flask(__name__)


def logger_wrapper(func):
    global logger

    def wrapper(*args, **kwargs):
        try:
            logger.info(f'{func.__name__} running... args: {args}, kwargs: {kwargs}')
            func(*args, **kwargs)
        except Exception as e:
            logger.error(f'{func.__name__} failed: {e}')

    return wrapper


# api接收消息的回调函数
@app.route('/api/recv', methods=['POST'])
def get_recv_msg() -> None:
    global logger
    try:
        form = request.form
        context_type = form.get('type')

        # 文件与图片部分
        if context_type != 'text':

            if context_type != 'file':
                logger.warning("recv unknown type:" + form.get('type'))
                return 'failed', 500

            file = request.files['content']
            pic_name = file.filename
            logger.info("recv file:" + pic_name)
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
            logger.info(f'{name} in room {roomName} say: "{content}"')
            reply = process_group_recv_msg(name, content)

            logger.info(f'reply: "{reply}"')

            response_data = {
                "success": True,
                "data": {
                    'type': 'text',
                    'content': reply
                }
            }

            if isMentioned == "1":
                logger.info(name + "@me")
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
            logger.info(f'{name} send to you: "{content}"')
            return response_data

        return 'error', 400

    except Exception as e:
        logger.error(e)
        # 处理异常情况
        response_data = {
            "success": False,
            "message": str(e)
        }

        return jsonify(response_data), 500


# 发送消息
@logger_wrapper
def send_mc_group_msg(content: str, data_type: str = "text"):
    global token, logger
    url = f"http://wxBotWebhook:3001/webhook/msg/v2?token={token}"

    payload = {
        "to": GROUP_NAME,
        "isRoom": True,
        "data": {
            "type": data_type,
            "content": content
        }
    }

    headers = {
        'User-Agent': 'Apifox/1.0.0 (https://apifox.com)',
        'Content-Type': 'application/json',
        'Accept': '*/*',
        'Host': 'localhost:3001',
        'Connection': 'keep-alive'
    }

    response = requests.request("POST", url, headers=headers, data=payload)
    logger.info(response.text)


# 处理群聊接收的消息，生成回复
@logger_wrapper
def process_group_recv_msg(name: str, context: str) -> str:
    global logger, history_context
    sendmsg = ''

    # 迎新助手
    if context.find('加入了群聊') != -1:
        with open('text/join.txt', mode='r', encoding='utf-8') as f:
            sendmsg = f.read()

    # 命令功能
    if context[0] == '/':

        if context == '/mcs':
            logger.info('发送服务器状态')
            sendmsg = checkMCServer()

        elif context == '/live':
            logger.info('发送直播状态')
            status = getLiveStatus()
            sendmsg += f'深圳技术大学Minecraft社直播间：\n直播状态：{status}\n直播间地址：https://live.bilibili.com/31149017'

        # 本地知识库
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
                    sendmsg = f.read()

            except FileNotFoundError:
                logger.error(f'未知命令: {context}')
                sendmsg = '未知命令'

    # 请求GPT
    if context[:4] == "@Bot":
        if len(context) > 5:
            asker = name
            send_mc_group_msg('正在思考中，回复完成前不会有响应')
            new_msg = f'玩家{asker}说:' + context[5:] + '\n回复简短，限制在100字以内，用文言文回复'
            history_context = getGPTresponse(history_context, new_msg)
            answer = history_context[-1]["content"]
            sendmsg += f'@{asker}{context[4]}{answer}'

    # 发送查询结果
    if sendmsg:
        if context != '/help':
            sendmsg += help_msg

    return sendmsg


# 定时类消息
class ScheduledArea:
    def __init__(self):
        self.last_status = '未开播'

        # 延时刻，防止短时间高频触发
        self.tick = 0
        self.last_tick = 0

    @logger_wrapper
    def process_scheduled_msg(self):
        global logger
        sendmsg = ''
        hour, min, sec = time.strftime('%H %M %S', time.localtime(time.time())).split(' ')
        # print('time:', hour, min, sec, end='\r')

        if self.tick - self.last_tick > 50:
            # 早睡助手
            if hour == '00' and min == '00' and sec == '00':
                logger.info('发送早睡提醒')
                with open('text/tips.txt', mode='r', encoding='utf-8') as f:
                    sendmsg = f.read()
                self.last_tick = self.tick

            # 开播检测
            if (min == '00' or min == '30') and sec == '30':
                logger.info('检测直播状态')
                status = getLiveStatus()
                if status == '直播中' and self.last_status != '直播中':
                    sendmsg += '检测到官号开播：\n深圳技术大学Minecraft社直播间\n直播间地址：https://live.bilibili.com/31149017'
                    self.last_status = '直播中'

                if status == '未开播' and self.last_status == '直播中':
                    self.last_status == '未开播'

                self.last_tick = self.tick

            # 每日冷知识
            if hour == '15' and min == '45' and sec == '00':
                logger.info('发送冷知识')
                newMsg, file_url = getDailyColdKnowledge()
                newMsg += '\n--转自东南大学Minecraft社B站动态'
                newMsg += help_msg
                send_mc_group_msg(newMsg)
                send_mc_group_msg(file_url, data_type='fileUrl')
                self.last_tick = self.tick
                return
            
        # 如果有消息，发送消息
        if sendmsg:
            send_mc_group_msg(sendmsg)

    def scheduled_loop(self):
        while True:
            self.process_scheduled_msg()
            time.sleep(0.1)
            self.tick += 1


if __name__ == "__main__":
    scheduler = ScheduledArea()
    scheduled_loop_thread = threading.Thread(target=scheduler.scheduled_loop, daemon=True)
    app.run(host='0.0.0.0', port=4994)

