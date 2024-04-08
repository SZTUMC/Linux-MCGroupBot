import os
from langchain.memory import ChatMessageHistory
from langchain.chat_models import ChatOpenAI
from langchain.embeddings.openai import OpenAIEmbeddings
from langchain.vectorstores import Chroma
from langchain.text_splitter import CharacterTextSplitter
from langchain.document_loaders import TextLoader
from langchain_core.documents import Document
from langchain.chains import RetrievalQA


os.environ["OPENAI_API_BASE"] = 'https://api.nextapi.fun/openai/v1'

# 加载LLM
chat = ChatOpenAI(temperature=0)


def test():
    # 初始化 MessageHistory 对象
    history = ChatMessageHistory()
    # 给 MessageHistory 对象添加对话内容
    history.add_ai_message("你好！")
    history.add_user_message("中国的首都是哪里？")
    # 执行对话
    ai_response = chat(history.messages)
    print(ai_response)


def local():
    # # 加载文件夹中的所有txt类型的文件
    # documents = []
    # for filename in os.listdir('wiki'):
    #     loader = TextLoader('wiki/' + filename, encoding='utf-8')
    #     # 将数据转成 document 对象，每个文件会作为一个 document
    #     documents += loader.load()
    # # 初始化加载器
    # text_splitter = CharacterTextSplitter(chunk_size=100, chunk_overlap=0)
    # # 切割加载的 document
    # split_docs = text_splitter.split_documents(documents)
    # 初始化 openai 的 embeddings 对象
    embeddings = OpenAIEmbeddings()
    # 将 document 通过 openai 的 embeddings 对象计算 embedding 向量信息并临时存入 Chroma 向量数据库，用于后续匹配查询
    persist_directory = 'mcdb'
    # docsearch = Chroma.from_documents(split_docs, embedding_function=embeddings, persist_directory=persist_directory)
    docsearch = Chroma(embedding_function=embeddings, persist_directory=persist_directory)

    # docsearch.persist()

    # 创建问答对象
    qa = RetrievalQA.from_chain_type(
        llm=chat, chain_type="stuff", retriever=docsearch.as_retriever(), return_source_documents=True
    )
    # 进行问答
    result = qa({"query": "红石电路能干什么？"})

    # with open('result.txt', 'w', encoding='utf-8') as f:
    #     f.write(result['result'])

    # with open('source.txt', 'w', encoding='utf-8') as f:
    #     for source in result['source_documents']:
    #         f.writelines(source.dict()['metadata']['source'])

    print(result['result'])

    print(result['source_documents'])

if __name__ == "__main__":
    local()
    # from langchain_community.utilities import SearxSearchWrapper

    # 创建一个SearxSearchWrapper实例，指定Searx服务器的主机地址
    # search = SearxSearchWrapper(searx_host="http://172.19.111.179:8888")
    # search = SearxSearchWrapper(searx_host="http://127.0.0.1:8888")

    # 运行搜索查询，例如查询“法国的首都是什么”
    # result = search.run("法国")
    # print(result)
    # test()
    # a = ''
    # with open('text/historyGPT.txt', mode='r', encoding='gbk') as f:
    #     a = f.read()
    #
    # with open('text/historyGPT.txt', mode='a', encoding='utf-8') as f:
    #     f.write('\U0001f1eb')

