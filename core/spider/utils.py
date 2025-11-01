# 保存文件工具
import numpy as np
import pandas as pd
import os
from datetime import datetime


def get_data_path(dir_name:str='data',filename:str=None):
    """
    找到保存文件夹路径、文件夹名和文件名
    """
    #保存到与app.py同级的data文件夹内
    curr_file_path = os.path.abspath(__file__)
    curr_dir = os.path.dirname(curr_file_path)

    parent1 = os.path.dirname(curr_dir)
    parent2 = os.path.dirname(parent1)

    data_dir = os.path.join(parent2,dir_name) #创建data文件夹

    # 创建data文件夹（不存在时）
    os.makedirs(data_dir,exist_ok=True)
    # 获取最终文件路径
    file_path = os.path.join(data_dir,filename)
    return file_path




def save_weatherdatas_as_csv(row_data:dict,filename:str=None):
    """
    将weatherdata保存为csv文件到data文件夹,
    filename:文件名称
    """
    if filename == None:
        # 获取当前时间
        current_time = datetime.now()
        # 装欢为年月日时分秒格式
        time_str = current_time.strftime(r"%Y%m%d%H%M%S")
        filename = f'{time_str}.csv'
    else:
        filename = filename+'.csv'
    file_path = get_data_path('data',filename)
 
    # 获取日期列表:
    dates = list(row_data.d7_temp.keys())
    # 扁平化数据，为每一天创建记录
    flattened = []
    for i,date in enumerate(dates):
        temp_info = row_data.d7_temp[date]
        daily={
            '日期':date,
            '城市':row_data.city,
            '更新时间':row_data.update_time,
            '天气':row_data.d7_weather[i],
            '最低温度':temp_info['最低温度'],
            '最高温度':temp_info['最高温度'],
            '风向':row_data.d7_wind_position[i],
            '风力':row_data.d7_wind[i]
        }
        flattened.append(daily)# 收集每一天
    
    df = pd.DataFrame(flattened)
    df.to_csv(file_path,index=False,encoding='utf-8-sig')
    print(f'{filename}已保存至{file_path}')