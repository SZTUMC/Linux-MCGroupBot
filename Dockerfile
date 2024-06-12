FROM python:3.11.9

WORKDIR /usr/src/myapp/Linux-MCGroupBot
COPY requirements.txt ./

RUN pip install --no-cache-dir -r requirements.txt  -i https://pypi.tuna.tsinghua.edu.cn/simple
RUN mkdir logs

COPY . .

# 设置默认环境变量值
ENV OPENAI_API_KEY="" \
    OPENAI_API_BASE="" \
    TOKEN=""

# 在启动容器时要求设置环境变量，如果未设置则容器启动失败
CMD ["bash", "-c", "\
if [ -z \"$OPENAI_API_KEY\" ]; then\
    echo \"Error: OPENAI_API_KEY not set\";\
    exit -1;\
fi;\
if [ -z \"$OPENAI_API_BASE\" ]; then\
    echo \"Error: OPENAI_API_BASE not set\";\
    exit -1;\
fi;\
if [ -z \"$TOKEN\" ]; then\
    echo \"Error: TOKEN not set\";\
    exit -1;\
fi;\
    echo \"Starting application with \
    OPENAI_API_KEY=$OPENAI_API_KEY, OPENAI_API_BASE=$OPENAI_API_BASE, TOKEN=$TOKEN\"; \
    python main.py; \
"]

