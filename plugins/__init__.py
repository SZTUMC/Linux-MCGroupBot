import os
import pkgutil
import time
from abc import ABC, abstractmethod


class AbstractPlugin(ABC):
    @abstractmethod
    def __init__(self, author, name):
        pass

    def onLoad(self):
        pass

    def onUnload(self):
        pass

    def quick_answer(self, context) -> str:
        return ''

    def command_run(self, command: str, args: str) -> str:
        pass

    def scheduled_run(self, now_time: time.struct_time) -> str:
        pass

    @abstractmethod
    def run(self) -> None:
        """
        无论何种情况每个机器人刻都执行的函数，运行在子进程，可用于插件的值后台计算更新，请注意最好在一刻内完成
        :return:
        """
        pass

    @abstractmethod
    def onCommand(self, command: str, args: str) -> bool:
        """
        命令回调触发器，给定命令
        :param command: 命令字符串
        :param args: 参数字符串
        :return: 是否触发
        """
        return False

    @abstractmethod
    def onScheduled(self, now_time: time.struct_time) -> bool:
        """
        时间回调触发器，给定指定格式的时间，返回True则触发事件，反之不触发
        Eg:
        :param now_time: 现在的时间
        :return: 是否触发
        """
        return False
