# 缺少数据时的一个简易爬虫，获取所需信息
from bs4 import BeautifulSoup
from parsel import Selector
from typing import List
import requests
import time 
import re
import json
from playwright.sync_api import sync_playwright

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
        self.upgrade_Time = upgrade_Time
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
        
        data = json.loads(json_data)

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

        tomorrow_t = soup.select(r"#\37 d > ul > li:nth-child(2) > p.tem > span")
        if tomorrow_t is not None:
            print(tomorrow_t[0].text)
        else:
            print("空")
        
        browser.close()


        



beijing = 101010100
qingdao = 101120201
get_7dweather_data(qingdao)
