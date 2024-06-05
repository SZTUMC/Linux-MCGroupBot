import os
import pickle
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service

from langchain.embeddings.openai import OpenAIEmbeddings
from langchain.chains import RetrievalQA
from langchain.chat_models import ChatOpenAI
from langchain.vectorstores import Chroma
from selenium import webdriver
from utils.mylog import global_logger

# ===========全局静态区============
token = os.environ["TOKEN"]
OPENAI_API_BASE = os.environ["OPENAI_API_BASE"]
GROUP_NAME = "深技大mc群(原夹总后援团)"
TEST_PERSON = "水滴火熵"
help_msg = "\n\ntips：输入/help获取命令表"

# ===========全局动态区============
# 加载LLM
chat = ChatOpenAI(temperature=0)

# 初始化 openai 的 embeddings 对象
embeddings = OpenAIEmbeddings()

# 加载知识库
docsearch = Chroma(embedding_function=embeddings, persist_directory='LLM_data/mcdb')

# 浏览器式爬虫初始化
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

# GPT历史对话数组，持久化
try:
    with open('historyGPT.data', mode='rb') as f:
        history_context = pickle.load(f)
except FileNotFoundError as e:
    global_logger.info('GPT history not found, will create new data')
    

traceback_msg = ''
last_traceback_msg = 'none'