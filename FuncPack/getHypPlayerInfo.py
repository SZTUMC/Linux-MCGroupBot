import cloudscraper
import pytz
from bs4 import BeautifulSoup
from datetime import datetime

def get_hyp_player_info(name:str, mode="Overall")->tuple[tuple, tuple] | str:
    """
    功能: 获取当前玩家在hypixel服务器的个人信息，当前包含大厅数据和起床战争数据
    参数: 
        1.name: 玩家的正版id
        2.mode: 选择查询的模式, 具体看"玩家数据可选项.txt"文本文件

    返回值：
        (大厅数据)+(起床数据)

    异常情况：
        网络请求错误
    """

    url = 'https://plancke.io/hypixel/player/stats/{}#BedWars'.format(name)


    # 伪装一下
    scraper = cloudscraper.create_scraper(browser={
        'browser': 'firefox',
        'platform': 'windows',
        'mobile': False
    })
    res = scraper.get(url)
    response = res.text
    soup = BeautifulSoup(response, "html.parser")


    # 大厅信息数据
    def lobby_info():
        info = soup.findAll("div", {"class": "card-box m-b-10"})
        info_str = ""
        for i in info:
            info_str += i.get_text("<br>")
        info_list = info_str.split("<br>")
        info_list = [x for x in info_list if x != "\n" and x != " "]
        # 大厅等级和状态(可增添、修改，详情看 info_list)
        for i in range(len(info_list)):
            if info_list[i] == "Level:":
                lobby_level = info_list[i + 1]
            if info_list[i] == "Status":
                if info_list[i + 1] != "Offline":
                    status = info_list[i + 2]
                else:
                    status = info_list[i + 1]
            if info_list[i] == "Last login: ":
                query_date_str = info_list[i + 1]
                query_date_str = query_date_str[:query_date_str.rfind(' ')]
                naive_dt = datetime.strptime(query_date_str, '%Y-%m-%d %H:%M')
                edt = pytz.timezone('US/Eastern')
                local_dt = edt.localize(naive_dt)
                cst = pytz.timezone('Asia/Shanghai')
                Last_login = datetime.strftime(local_dt.astimezone(cst), '%Y-%m-%d %H:%M')

        return lobby_level, status, Last_login


    # 起床战争数据
    def bedwars_info():
        """
        起床战争数据
        """
        text = soup.findAll({"div"}, {"id": "stat_panel_BedWars"})
        bedwar_list_str = ""
        for d in text:
            bedwar_list_str += d.get_text("<b>")
        bedwar_list = bedwar_list_str.split("<b>")
        bedwar_list = [x for x in bedwar_list if x != "\n" and x != " "]
        # 起床等级(可增添、修改，详情看 bedwar_list)
        for i in range(len(bedwar_list)):
            if bedwar_list[i] == "Level:":
                bedwar_level = bedwar_list[i + 1]

        # 各模式具体数据(可增添、修改，详情看 bedwar_list)
        # K  D  K/D(Normal) 	K  D  K/D(Final) 	 W  L  W/L    Beds Broken
        # 1  2   3              4  5   6             7  8   9         10
        for i in range(len(bedwar_list)):
            if bedwar_list[i] == mode:
                KD = bedwar_list[i + 3]
                WL = bedwar_list[i + 9]
                beds_broken = bedwar_list[i + 10]

        return bedwar_level, KD, WL, beds_broken


    # 判断是否请求成功
    if res.ok:
        return lobby_info(), bedwars_info()
    else:
        return None


if __name__ == "__main__":
    # query_list = ["genekneetieMay", "Mick4994", "WGtian", "kingen_325", "noobsheep0v0", "Isbells"]
    query_list = ["WGtian", "Mick4994"]
    for player_name in query_list:
        print(player_name + ":")
        print(get_hyp_player_info(name=player_name))
        print()