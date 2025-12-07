# 获取空气质量，目标网站：https://aqicn.org
import pandas as pd
import requests
import json
from datetime import datetime ,timedelta
try:
    from .utils import save_airQdata_as_csv as save
except ImportError:
    try:
        from core.spider.utils import save_airQdata_as_csv as save
    except ImportError:
        from utils import save_airQdata_as_csv as save


import os
TOKEN = os.getenv('WAQI_TOKEN', 'c427b66ab61b674787e65d025e6cac3e6b3b4183')
HTTPS = f'https://api.waqi.info/feed/here/?token={TOKEN}' 


def data_get(city:str,position:str=None,token=TOKEN):
    if position is not None:
        key = position
    else:
        key = city

    url = f'https://api.waqi.info/feed/{key}/?token={token}'
    response = requests.get(url)
    
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

        today = f'{key}今日空气质量'
        forecast_name = f'{key}空气质量预测'
        save(df_result,today)
        save(df_forecast,forecast_name)
        
    else:
        print(f'网站打开失败,错误状态码{response.status_code}')


def datas_get(citys:list):
    """
    多城市获取,把city列表或position列表作为参数传入
    citys:包含城市名的列表
    """
    for city in citys:
        if  not isinstance(city,str):
            print(f'{city}不符合规范,请输入城市名')
            continue
        data_get(city)
        


if __name__ == '__main__':

    citys = ['qingdao',114514,'beijing','tokyo']
    datas_get(citys)
    

