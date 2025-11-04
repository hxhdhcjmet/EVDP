# 获取空气质量，目标网站：https://aqicn.org
import pandas as pd
from bs4 import BeautifulSoup
from parsel import Selector
from typing import List
import requests
import time 
import re
import json
from playwright.sync_api import sync_playwright
from datetime import datetime ,timedelta
from utils import save_airQdata_as_csv as save


TOKEN = 'c427b66ab61b674787e65d025e6cac3e6b3b4183' # 输入获取到的token，可前往https://aqicn.org/data-platform/token/ 处申请
HTTPS = f'https://api.waqi.info/feed/here/?token={TOKEN}' 


def data_get(city:str,position:str=None,token=TOKEN):
    if position is not None:
        key = position
    else:
        key = city

    url = f'https://api.waqi.info/feed/{key}/?token={token}'
    response = requests.get(HTTPS)
    
    if response.status_code == 200:
        row_data = response.json()

        city_data = row_data['data']
        iaqi = city_data['iaqi']
        city = city_data['city']['name']
        update_time = city_data['time']['s']
        # 存放实时数据
        result = {
        'city':city,
        'city_pos':city_data['city']['geo'], 
        'time':update_time,
        'dominant':city_data['dominentpol'],# 主要污染物
        }
        for k,v in iaqi.items():
            result[k] = v.get('v')
        # 预测数据
        forecast = []
        for pollutant,daily_list in city_data['forecast']['daily'].items():
            for d in daily_list:
                forecast.append({
                'city':city,
                'pollutant':pollutant,
                'date':d.get('day'),
                'avg':d.get('avg'),
                'max':d.get('max'),
                'min':d.get('min')
                }
                )
        df_result = pd.DataFrame([result])
        df_forecast = pd.DataFrame(forecast)
        save(df_result,'北京今日天气状况')
        save(df_forecast,'北京天气状况预测')
        
    else:
        print(f'网站打开失败,错误状态码{response.status_code}')



if __name__ == '__main__':
    data_get('beijing')


