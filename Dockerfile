FROM python:3.12

WORKDIR /usr/src/myapp/Linux-MCGroupBot
COPY requirements.txt ./

RUN pip install --no-cache-dir -r requirements.txt  -i https://pypi.tuna.tsinghua.edu.cn/simple
RUN mkdir logs

COPY . .

CMD [ "python mcs.py" ]
