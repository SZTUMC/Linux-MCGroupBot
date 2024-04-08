import os
import json
import requests
import threading
import pickle
import time
import traceback

from io import StringIO
from flask import Flask, request, jsonify

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service

from langchain.embeddings.openai import OpenAIEmbeddings
from langchain.chains import RetrievalQA
from langchain.chat_models import ChatOpenAI
from langchain.vectorstores import Chroma

from utils import mylog

from FuncPack.getGPTresponseFunc import getGPTresponse
from FuncPack.checkMCServerFunc import checkMCServer
from FuncPack.getBiliLiveStatusFunc import getLiveStatus

# todo: 全局参数等待规范化为config文件

token = os.environ["TOKEN"]

OPENAI_API_BASE = os.environ["OPENAI_API_BASE"]

GROUP_NAME = "深技大mc群(原夹总后援团)"

# 加载LLM
chat = ChatOpenAI(temperature=0)

# 初始化 openai 的 embeddings 对象
embeddings = OpenAIEmbeddings()

# 加载知识库
docsearch = Chroma(embedding_function=embeddings, persist_directory='mcdb')

chrome_options = Options()
chrome_options.add_argument("--mute-audio") 
chrome_options.add_argument('--no-sandbox')
chrome_options.add_argument('--disable-dev-shm-usage')
chrome_options.add_argument('--remote-debugging-port=9222')
chrome_options.add_argument('--single-process')
chrome_options.add_argument("--headless")
chrome_options.add_argument("--disable-gpu")
service = Service(executable_path='./chromedriver-linux64/chromedriver')
browser = webdriver.Chrome(options=chrome_options, service=service)

# 创建问答对象
qa = RetrievalQA.from_chain_type(
    llm=chat, chain_type="stuff", retriever=docsearch.as_retriever(), return_source_documents=True
)

history_context = []

logger = mylog.log_init(path='logs/')

try:
    with open('historyGPT.data', mode='rb') as f:
        history_context = pickle.load(f)
except FileNotFoundError as e:
    logger.info('GPT history not found, will create new data')
    
help_msg = "\n\ntips：输入/help获取命令表"

app = Flask(__name__)

traceback_msg = ''

last_traceback_msg = 'none'


def logger_wrapper(func):
    global logger

    def wrapper(*args, **kwargs):
        try:
            logger.info(f'{func.__name__} running... args: {args}, kwargs: {kwargs}')
            return func(*args, **kwargs)
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
                if context_type == 'system_event_push_notify':
                    return 'bot send', 200
                
                logger.warning("recv unknown type:" + context_type)
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

            logger.info(f'content:\n"{content}"\nreply:\n"{reply}"')

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
        logger.error('get_recv_msg error', e)
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

    payload = json.dumps(payload)

    headers = {
        'User-Agent': 'Apifox/1.0.0 (https://apifox.com)',
        'Content-Type': 'application/json',
        'Accept': '*/*',
        'Host': 'wxBotWebhook:3001',
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
            status = getLiveStatus(arg_roomid=31149017)
            sendmsg += f'深圳技术大学Minecraft社直播间：\n直播状态：{status}\n直播间地址：https://live.bilibili.com/31149017'

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
                    logger.info("load cmd:" + context)
                    sendmsg = f.read()
                    logger.info("have load msg:\n" + sendmsg)

            except FileNotFoundError:
                logger.error(f'未知命令: {context}')
                sendmsg = '未知命令'

    #todo: 提示词优化，记忆优化，请求GPT
    if context[:4] == "@Bot":
        if len(context) > 5:
            asker = name
            send_mc_group_msg('正在思考中，回复完成前不会有响应')
            new_msg = f'玩家{asker}说:' + context[5:] + '\n回复简短，限制在100字以内，用文言文回复'
            history_context = getGPTresponse(
                base_url=OPENAI_API_BASE,
                history_context=history_context, 
                new_message=new_msg
            )
            answer = history_context[-1]["content"]
            sendmsg += f'@{asker}{context[4]}{answer}'

    # 发送查询结果
    if sendmsg:
        logger.info("sendmsg:\n"+sendmsg)
        if context != '/help':
            sendmsg += help_msg
        else:
            logger.info("help指令")

    return sendmsg


# refact: 这个类太屎山，等待重构优化
# 定时类消息
class ScheduledArea:
    def __init__(self):
        self.last_status = '未开播'

        # 延时刻，防止短时间高频触发
        self.tick = 0
        self.last_tick = 0
        self.count = 0

    def process_scheduled_msg(self):
        global logger, last_traceback_msg, traceback_msg
        sendmsg = ''
        hour, min, sec = time.strftime('%H %M %S', time.localtime(time.time())).split(' ')
        # print('time:', hour, min, sec, end='\r')
        if self.tick % 360 == 0:
            logger.info(f'scheduled time:{hour} {min} {sec} tick:{self.tick}')

        if self.tick - self.last_tick > 50:
            # 早睡助手
            if hour == '00' and min == '00' and sec == '00':
                logger.info('发送早睡提醒')
                logger = mylog.log_init(path='logs/')
                with open('text/tips.txt', mode='r', encoding='utf-8') as f:
                    sendmsg = f.read()
                self.last_tick = self.tick

            # 开播检测
            if (min == '00' or min == '30') and sec == '30':
                logger.info('检测直播状态')
                status = getLiveStatus(arg_roomid=31149017)
                if status == '直播中' and self.last_status != '直播中':
                    sendmsg += '检测到官号开播：\n深圳技术大学Minecraft社直播间\n直播间地址：https://live.bilibili.com/31149017'
                    self.last_status = '直播中'

                if status == '未开播':
                    logger.info('未在直播')
                    if self.last_status != '直播中':
                        self.last_status == '未开播'

                self.last_tick = self.tick

            # 每日冷知识
            if hour == '12' and min == '00' and sec == '00':

                self.last_tick = self.tick
                logger.info('发送冷知识')
                
                def selenium_get():
                    self.count += 1
                    browser.get("https://space.bilibili.com/1377901474/dynamic")
                    time.sleep(3)
                    logger.info(f'browser.get:{self.count}')
                    try:
                        element = WebDriverWait(browser, 10).until(
                            EC.presence_of_element_located((By.XPATH, '//*[@id="page-dynamic"]/div[1]/div/div[1]/div[2]/div/div/div[3]/div/div/div/div/div[1]/div/div/span[2]'))
                        )

                        logger.info(f"{self.count}:element.text:{element.text}")
                        newMsg = element.text
                        newMsg += '\n--转自东南大学Minecraft社B站动态'
                        newMsg += help_msg
                        send_mc_group_msg(newMsg)

                        img_element = WebDriverWait(browser, 10).until(
                            EC.presence_of_element_located((By.XPATH, '//*[@id="page-dynamic"]/div[1]/div/div[1]/div[2]/div/div/div[3]/div/div/div/div/div[2]/div/div[1]/div/div/picture/img'))
                        )

                        file_url = img_element.get_attribute("src")
                        file_url = file_url[:file_url.rfind('@')]

                        logger.info(f"{self.count}:file_url:{file_url}")

                        send_mc_group_msg(file_url, data_type='fileUrl')
                        
                    except:
                        f = StringIO()
                        traceback.print_exc(file=f)
                        traceback_msg = f.getvalue()
                        if last_traceback_msg != traceback_msg:
                            logger.error(traceback_msg)
                        last_traceback_msg = traceback_msg

                        selenium_get()

                selenium_get()

                return
            
        # 如果有消息，发送消息
        if sendmsg:
            send_mc_group_msg(sendmsg)


    def scheduled_loop(self):
        global logger, last_traceback_msg, traceback_msg
        while True:
            try:
                self.process_scheduled_msg()
            except:
                f = StringIO()
                traceback.print_exc(file=f)
                traceback_msg = f.getvalue()
                if last_traceback_msg != traceback_msg:
                    logger.error(traceback_msg)
                last_traceback_msg = traceback_msg
                self.last_tick = self.tick
            
            time.sleep(0.1)
            self.tick += 1
            if self.tick % 360 == 0:
                logger.info('scheduled_loop still running')

            if self.tick > 36000 * 24:
                self.tick = 0


if __name__ == "__main__":
    scheduler = ScheduledArea()
    scheduled_loop_thread = threading.Thread(target=scheduler.scheduled_loop, daemon=True)
    scheduled_loop_thread.start()
    app.run(host='0.0.0.0', port=4994)

