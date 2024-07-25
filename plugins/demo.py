import time
from plugins import AbstractPlugin


class HelloPlugin(AbstractPlugin):
    """
    示例插件
    """
    def __init__(self, author, name):
        pass

    def onLoad(self):
        pass

    def run(self):
        print('hello are running')

    def command_run(self, command: str, args: str) -> str:
        return 'hello! run command application'

    def scheduled_run(self, now_time: time.struct_time) -> str:
        return 'hello! run scheduled application'

    def onCommand(self, command, args) -> bool:
        if command == 'hello':
            return True

        return False

    def onScheduled(self, now_time) -> bool:
        # 当每天8点整时运行
        if now_time.tm_hour == 8 and now_time.tm_min == 0 and now_time.tm_sec == 0:
            return True

        return False