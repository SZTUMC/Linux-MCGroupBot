import logging
import time
import traceback
from io import StringIO

class LogUtil:
    
    def __init__(self, path, log_level = logging.DEBUG) -> None: 
        self._init_logger(path, log_level)
        self.last_traceback_msg = ''


    def _init_logger(self, path, log_level):
        self.logger = logging.getLogger()
        self.logger.setLevel(logging.INFO)  # Log等级总开关
        rq = time.strftime('%Y-%m-%d %H-%M', time.localtime(time.time()))
        log_path = path
        log_name = log_path + rq + '.log'
        logfile = log_name
        fh = logging.FileHandler(logfile, mode='w', encoding='utf-8')
        ch = logging.StreamHandler()
        fh.setLevel(log_level)  # 输出到文件的log等级的开关
        ch.setLevel(logging.DEBUG)  # 输出到控制台的log等级的开关
        formatter = logging.Formatter("%(asctime)s - %(filename)s [%(threadName)s] - %(levelname)s: %(message)s")
        fh.setFormatter(formatter)
        ch.setFormatter(formatter)
        self.logger.addHandler(ch)
        self.logger.addHandler(fh)


    def rebuild(self):
        self._init_logger()


    def getLogger(self):
        return self.logger


    def record_start_info(self, args: dict) -> None:
        str_info = 'Start Args:\n'
        for key, value in args.items():
            for _ in range(7):
                str_info += "\t" 
            str_info += f"[{key}: {str(value)}]" + "\n"
        str_info = str_info[:-1]
        self.logger.info(str_info)


    def logger_wrapper(self, func):
        def wrapper(*args, **kwargs):
            try:
                self.logger.info(f'{func.__name__} running... args: {args}, kwargs: {kwargs}')
                return func(*args, **kwargs)
            except Exception as e:
                f = StringIO()
                traceback.print_exc(file=f)
                traceback_msg = f.getvalue()
                if self.last_traceback_msg != traceback_msg:
                    self.logger.error(traceback_msg)
                self.last_traceback_msg = traceback_msg
                self.logger.error(f'{func.__name__} failed: {e}\n detail traceback_msg:\n{traceback_msg}')
            
        return wrapper

# workspace: /usr/src/myapp/Linux-MCGroupBot/
global_logUtil = LogUtil(path='logs/')
global_logger = global_logUtil.getLogger()


