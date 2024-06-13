import time
import datetime
import services
import config

from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

from utils.mylog import global_logger, global_logUtil

from FuncPack.checkMCServerFunc import checkMCServer
from FuncPack.getBiliLiveStatusFunc import getLiveStatus


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
        sendmsg = ''
        hour, min, sec = time.strftime('%H %M %S', time.localtime(time.time())).split(' ')
        # print('time:', hour, min, sec, end='\r')
        if self.tick % 360 == 0:
            global_logger.info(f'scheduled time:{hour} {min} {sec} tick:{self.tick} last_tick:{self.last_tick}')

        if self.tick - self.last_tick > 50:
            # 早睡助手
            if hour == '00' and min == '00' and sec == '00':
                global_logger.info('发送早睡提醒')

                # 新一天重置logger，生成新的log文件
                for handler in global_logger.handlers.copy():
                    global_logger.removeHandler(handler)
                global_logUtil.rebuild()

                with open('text/tips.txt', mode='r', encoding='utf-8') as f:
                    sendmsg = f.read()
                self.tick = 0
                self.last_tick = self.tick

            # 开播检测
            if (min == '00' or min == '30') and sec == '30':
                global_logger.info('检测直播状态')
                status = getLiveStatus(arg_roomid=31149017)
                if status == '直播中' and self.last_status != '直播中':
                    sendmsg += '检测到官号开播：\n深圳技术大学Minecraft社直播间\n直播间地址：https://live.bilibili.com/31149017'
                    self.last_status = '直播中'

                if status == '未开播':
                    global_logger.info('未在直播')
                    if self.last_status != '直播中':
                        self.last_status == '未开播'

                self.last_tick = self.tick

            # 服务器轮询
            if min == '10' and sec == '00' and int(hour) % 4 == 0:
                #  if int(hour) % 4 == 0:
                #     with open('text/update.txt', mode='r', encoding='utf-8') as f:
                #         update_context = f.read()
                #     send_mc_group_msg(update_context)
                global_logger.info('轮询服务器状态')
                sendmsg = checkMCServer(logger=global_logger)
                self.last_tick = self.tick

            # 工作日
            if hour == '09' and min == '00' and sec == '00':
                weekday_index = datetime.datetime.now().weekday()
                if weekday_index in [i for i in range(5)]:
                    file_url = f"http://botv3:4994/{weekday_index + 1}.jpg"
                    services.send_mc_group_msg(file_url, data_type='fileUrl')
                    # send_test_msg(file_url, data_type='fileUrl')
                    self.last_tick = self.tick
                    

            # 每日冷知识
            if hour == '15' and min == '50' and sec == '00':

                self.last_tick = self.tick
                global_logger.info('发送冷知识')
                
                def selenium_get():
                    self.count += 1
                    config.browser.get("https://space.bilibili.com/1377901474/dynamic")
                    time.sleep(3)
                    global_logger.info(f'browser.get:{self.count}')
                    try:
                        element = WebDriverWait(config.browser, 10).until(
                            EC.presence_of_element_located((By.XPATH, '//*[@id="page-dynamic"]/div[1]/div/div[1]/div[2]/div/div/div[3]/div/div/div/div/div[1]/div/div/span[2]'))
                        )

                        newMsg = element.text
                        newMsg += '\n--转自东南大学Minecraft社B站动态'
                        newMsg += config.help_msg
                        services.send_mc_group_msg(newMsg)

                        img_element = WebDriverWait(config.browser, 10).until(
                            EC.presence_of_element_located((By.XPATH, '//*[@id="page-dynamic"]/div[1]/div/div[1]/div[2]/div/div/div[3]/div/div/div/div/div[2]/div/div[1]/div/div/picture/img'))
                        )

                        file_url = img_element.get_attribute("src")
                        file_url = file_url[:file_url.rfind('@')]

                        services.send_mc_group_msg(file_url, data_type='fileUrl')
                        
                    except:

                        # 反复重试
                        selenium_get()

                selenium_get()

                return
            
        # 如果有消息，发送消息
        if sendmsg:
            services.send_mc_group_msg(sendmsg)


    def scheduled_loop(self):
        while True:
            self.process_scheduled_msg()

            time.sleep(0.1)
            self.tick += 1
            if self.tick % 360 == 0:
                global_logger.info('scheduled_loop still running')


