# 缺少数据时的一个简易爬虫，获取所需信息
from bs4 import BeautifulSoup
from parsel import Selector
from typing import List
import requests
import time 
import re
import json
from playwright.sync_api import sync_playwright
from datetime import datetime ,timedelta
try:
    from .utils import save_weatherdatas_as_csv as save
except ImportError:
    try:
        from core.spider.utils import save_weatherdatas_as_csv as save
    except ImportError:
        from utils import save_weatherdatas_as_csv as save


class Weather:
    def __init__(self,city,update_time,temp,wind_position,wind,wet):
        """
        创建天气数据类
        city:城市名
        update_time:更新时间
        temp:温度
        wind_position:温度
        wind:风力
        wet:湿度
        """
        self.city = city
        self.update_time = update_time
        self.temp = temp
        self.wind_position = wind_position
        self.wind = wind
        self.wet = wet
    
    def __str__(self):
        return str({
            "城市":self.city,
            "更新时间":self.update_time,
            "温度":self.temp+"℃",
            "风向":self.wind_position,
            "风力":self.wind,
            "湿度":self.wet
        })

class Weather_7d:
    def __init__(self,city,update_time):
        self.city = city
        self.update_time = update_time
        self.d7_weather = []
        self.d7_temp = dict()
        self.d7_wind_position = []
        self.d7_wind =[]

    def __str__(self):
        return str({
            "城市":self.city,
            "更新时间":self.update_time,
            "天气":self.d7_weather,
            "温度":self.d7_temp,
            "风向":self.d7_wind_position,
            "风力":self.d7_wind
        })
        
    
    def add_temp(self,date:str,lowest:str,highest:str):
        """
        新增某日温度
        date:日期
        lowest:最低温度
        highest:最高温度
        """
        self.d7_temp[date]={'最低温度':lowest,'最高温度':highest+"℃"}

    def add_wind_and_position(self,wind_position,wind:str):
        """
        新增某日风向风力
        wind_position:风向
        wind:风力
        """
        self.d7_wind_position.append(wind_position)
        self.d7_wind.append(wind)
    
    def add_weather(self,weather:str):
        self.d7_weather.append(weather)

class Weather_815d(Weather_7d):
    """
    获取8~15天天气(预报,不一定准,总计8天的) 
    """

# class Weather_40d:
#     """
#     40天天气情况,数据分别为:天气、最高和最低温度、历史均值降水概率
#     """
#     def __init__(self,city,update_time):
#         self.city = city
#         self.update_time = update_time
#         self.d40_weather = []
#         self.d40_temp = dict()
#         self.d40_rainProb = []

#     def __str__(self):
#         return str(
#             {
#                 "城市":self.city,
#                 "更新时间":self.update_time,
#                 "天气":self.d40_weather,
#                 "温度":self.d40_temp,
#                 "历史降水概率":self.d40_rainProb
#             }
#         )

#     def add_temp(self,date:str,lowest:str,highest:str):
#         """
#         添加温度数据
#         date:日期
#         lowest:最低温度
#         highest:最高温度
#         """
#         self.d40_weather[date]={'最低温度':lowest,'最高温度':highest}

#     def add_weather(self,weather:str):
#         """
#         添加天气数据
#         weather:天气
#         """
#         self.d40_weather.append(weather)

#     def add_rainProb(self,rain:str):
#         """
#         添加历史降水概率
#         rain:降水概率
#         """
#         self.add_rainProb(rain)



def draft_time_hm(row_str:str):
    """
    提取00:00(hour,minute)格式的时间
    """
    return re.match(r'^(0?\d|1\d|2[0-3]):[0-5]\d',row_str).group()

def draft_time_ymd(row_str:str):
    return re.match(r'(\d{4}-\d{2}-\d{2})',row_str).group()

def delay_d_day(origin_date:str,d:int)->str:
    """
    计算d天后的时间
    origin_date:原始时间
    d:要延迟的天数
    """
    origin_date = draft_time_ymd(origin_date)
    
    origin_date = datetime.strptime(origin_date,"%Y-%m-%d").date()

    # 计算d天后的时间
    delay_date = origin_date + timedelta(days = d)
    delay_date = delay_date.strftime("%Y-%m-%d")

    return delay_date





# 获取中国天气网数据

def get_1d_weather_data(city_code):
    """
    获取天气数据
    city_code:城市代码
    """

    url = f"https://d1.weather.com.cn/sk_2d/{city_code}.html?_={int(time.time()*1000)}"# 目标网址

    headers = {"Referer":f"https://www.weather.com.cn/weather1d/{city_code}.shtml","User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"}
    # print("开始获取数据...")

    time.sleep(0.5)

    response = requests.get(url,headers=headers)
    response.encoding = "utf-8"

    if response.status_code == 200:
        # 200-OK
        json_data = response.text.replace("var dataSK=","").strip()
        
        data = json.loads(json_data)

        city_weather = Weather(data.get("cityname"),data.get("time"),data.get("temp"),data.get("WD"),data.get("WS"),data.get("SD"))
        return city_weather
       
    else:
        print(f"请求失败,状态码:{response.status_code}")
        return None


def get_7d_weather_data(city_code):
    """
    获取7日天气
    city_code:城市代码
    """
    # 获取7日找api接口失败，跳转商业合作界面，遂用playwright
    with sync_playwright() as p:
        # 使用playwright框架
        # 配置浏览器
        browser = p.chromium.launch(headless = True)
        page = browser.new_page()

        target_url = f"https://www.weather.com.cn/weather/{city_code}.shtml"
        page.goto(target_url)

        page.wait_for_timeout(1000) # 等待1s确保所有元素加载完成

        page_html = page.content() # 获取渲染后的完整html

        soup = BeautifulSoup(page_html,"html.parser")

        # 提取时间(xx:xx格式str类型)
        update_time = soup.select_one(".ctop .time")
        if update_time is not None:
            update_time = draft_time_hm(update_time.text.strip())

        # 提取str类型城市名  
        city = soup.select_one(".ctop .crumbs a:last-of-type")
        if city is not None:
            city = str(city.text.strip())
        
        if update_time and city is not None:
            weather_7d = Weather_7d(city,update_time)
            curr_date = soup.select_one(r"h1.view i").text.strip()
            date = []
            for i in range(7):
               date.append(delay_d_day(curr_date,i))
                # 创建容器，开始提取最高、最低温度，风向和风力
                # 今天的天气信息CSS格式与后面预期几天的不同，分开处理
                # 风向在客户端显示为图标，文字信息在title中
            for li,j in zip(soup.select(r"#\37 d ul li"),date):
                weather = li.select_one('p.wea').text.strip()
                lowest_temp = li.select_one("p.tem i").text.strip()
                highest_temp = li.select_one("p.tem span").text.strip()
                wind = li.select_one('p.win i').text.strip()
                wind_position = [s.get('title') for s in li.select('p.win em span')]

                weather_7d.add_temp(j,lowest_temp,highest_temp)
                weather_7d.add_weather(weather)
                weather_7d.add_wind_and_position(wind_position,wind)
            browser.close()

            return weather_7d

        else:
            print("城市名或更新时间提取失败")
            browser.close()
            return None

        




def get_815d_weather_data(city_code:str):
    """
    获取未来8~15日的天气预测数据(预测，所以可能不准)
    city_code:城市代码
    """
    with sync_playwright() as p:
        # 使用playwright框架
        # 配置浏览器
        browser = p.chromium.launch(headless = True)
        page = browser.new_page()

        target_url = f"https://www.weather.com.cn/weather15d/{city_code}.shtml"
        page.goto(target_url)

        page.wait_for_timeout(1000) # 等待1s确保所有元素加载完成

        page_html = page.content() # 获取渲染后的完整html

        soup = BeautifulSoup(page_html,"html.parser")

        # 以下获取时间、城市名方法相同
        # 提取时间(xx:xx格式str类型)
        update_time = soup.select_one(".ctop .time")
        if update_time is not None:
            update_time = draft_time_hm(update_time.text.strip())

        # 提取str类型城市名  
        city = soup.select_one(".ctop .crumbs a:last-of-type")
        if city is not None:
            city = str(city.text.strip())

        if city and update_time is not None:
            weather_815d = Weather_815d(city,update_time)
            curr_date = curr_date = soup.select_one(r"h1.view i").text.strip()
            date = []
            for i in range(8):
                date.append(delay_d_day(curr_date,i+7))# 从今天先加7天，在这之后递增便是8~15天
            
            # 获取8~15日的未来天气数据
            for day,j in zip(soup.select(r'ul.t.clearfix li'),date):
                weather = day.select_one('span.wea').text.strip()
                tem = day.select_one('span.tem')
                # 这里获取最高温度会得到单位，与函数添加出有重叠，因此获取时去掉单位
                highest_temp = tem.text.strip().split('/')[0].strip('℃')
                lowest_temp = tem.text.strip().split('/')[-1]
                wind_position = day.select_one('span.wind').text.strip()
                wind = day.select_one('span.wind1').text.strip()

                # 添加到类中
                weather_815d.add_temp(j,lowest_temp,highest_temp)
                weather_815d.add_weather(weather)
                weather_815d.add_wind_and_position(wind_position,wind)

        browser.close()
        return weather_815d


# def get_40d_weather_data(city_code:str):
#     """
#     获取40天的天气情况
#     city_code:城市代码
#     """
#     with sync_playwright() as p:
#         browser = p.chromium.launch(headless = True)
#         page = browser.new_page()
#         target_url = f"https://www.weather.com.cn/weather40d/{city_code}.shtml"
#         page.goto(target_url)
#         page.wait_for_timeout(1000)
#         page_content =page.content()

#         soup = BeautifulSoup(page_content,'html.parser')

#         # 获取更新时间
#         update_time = soup.select_one('.ctop .time')
#         if update_time is not None:
#             update_time = draft_time_hm(update_time.text.strip())
           
#         # 获取城市名称
#         city = soup.select_one(".ctop .crumbs a:last-of-type")
#         if city is not None:
#             city = str(city.text.strip())
        

#         data = soup.select_one("#table >tbody")
#         weather_40d = Weather_40d(city,update_time)
#         detail_data = data.select("tr")
#         detail_data = detail_data[1:]# 第一个是周一~周日列表，去除

#         for eveday in detail_data:
#             highest = eveday.select_one(".w_xian").select_one('.max')
#             lowest = eveday.select_one(".w_xian").select_one('.min')
#             if highest and lowest is not None :
#                 highest = highest.text.strip()
#                 lowest = lowest.text.strip('/')# /10℃形式，把/去掉

if __name__ == "__mian__":
    beijing = 101010100
    qingdao = 101120201
    shanghai = 101020100

    d7_wea = get_7d_weather_data(shanghai)
    save(d7_wea,'上海8-15日天气')
