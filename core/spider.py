# 缺少数据时的一个简易爬虫，获取所需信息
from bs4 import BeautifulSoup
from parsel import Selector
from typing import List
import requests
import time 
import re
import json

url_weather = r"https://d1.weather.com.cn/sk_2d/101010100.html?_=1761118015460"




class Weather:
    def __init__(self,city,upgrade_Time,temp,wind_position,wind,wet):
        """
        创建天气数据类
        city:城市名
        upgrade_Time:更新时间
        temp:温度
        wind_position:温度
        wind:风力
        wet:湿度
        """
        self.city = city
        self.upgrade_Time = upgradeTime
        self.temp = temp
        self.wind_position = wind_position
        self.wind = wind
        self.wet = wet
    
    def __str__(self):
        return str({
            "城市":self.city,
            "更新时间":self.upgrade_Time,
            "温度":self.temp+"℃",
            "风向":self.wind_position,
            "风力":self.wind,
            "湿度":self.wet
        })


# 获取中国天气网数据

def get_1dweather_data(city_code):
    """
    获取天气数据
    city_code:城市代码
    """

    url = f"https://d1.weather.com.cn/sk_2d/{city_code}.html?_={int(time.time()*1000)}"# 目标网址

    headers = {"Referer":f"https://www.weather.com.cn/weather1d/{city_code}.shtml","User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"}
    print("开始获取数据...")

    time.sleep(0.5)

    response = requests.get(url,headers=headers)
    response.encoding = "utf-8"

    if response.status_code == 200:
        # 200-OK
        json_data = response.text.replace("var dataSK=","").strip()
        print(type(json_data))
        data = json.loads(json_data)
        print(type(data))
        city_weather = Weather(data.get("cityname"),data.get("time"),data.get("temp"),data.get("WD"),data.get("WS"),data.get("SD"))
        return city_weather
       
    else:
        print(f"请求失败,状态码:{response.status_code}")
        return None


def get_7dweather_data(city_code):
    """
    获取7日天气
    city_code:城市代码
    """

    url = f"https://d1.weather.com.cn/weather/7d/{city_code}.html?_={int(time.time()*1000)}"
    headers = {
    "Referer": f"https://www.weather.com.cn/weather/{city_code}.shtml",
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                  "AppleWebKit/537.36 (KHTML, like Gecko) "
                  "Chrome/129.0.0.0 Safari/537.36",
    "Accept": "*/*",
    "Accept-Language": "zh-CN,zh;q=0.9",
    "Connection": "keep-alive",
    "Host": "d1.weather.com.cn",
    "X-Requested-With": "XMLHttpRequest",
    "Accept-Encoding": "gzip, deflate, br"
}
    print("开始获取数据...")
    time.sleep(1)
    response = requests.get(url,headers=headers,allow_redirects = False)
    response.encoding = "utf-8"
    
    
    if True:
        #200-OK
        print(response.status_code)
        print(response.url)
        print("Location:",response.headers.get("Location"))
        print(response.text[:300])
    else:
        print(f"请求失败,状态码:{response.status_code}")



beijing = 101010100
get_7dweather_data(beijing)
