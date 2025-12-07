# 保存文件工具
import numpy as np
import pandas as pd
import os
from datetime import datetime
from dataclasses import asdict
from urllib.parse import urlparse
import time
import hashlib


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
    # 如果filename不是文件格式,则创建filename格式的文件夹
    if filename == None:
        # 如果文件名为空，则仅返回文件夹名
        return data_dir
    elif '.' not in filename:
        file = os.path.join(data_dir,filename)
        os.makedirs(file,exist_ok=True)
        return file
    else:
        file_path = os.path.join(data_dir,filename)
        return file_path
    
def default_filename():
    """
    创建默认文件名为当前时间
    """
    current_time = datetime.now()
    time_str = current_time.strftime(r'%Y%m%d%H%M%S')
    return time_str


def save_weatherdatas_as_csv(row_data:dict,filename:str=None):
    """
    将weatherdata保存为csv文件到data文件夹,
    filename:文件名称
    """
    if filename == None:
        # # 获取当前时间
        # current_time = datetime.now()
        # # 装欢为年月日时分秒格式
        # time_str = current_time.strftime(r"%Y%m%d%H%M%S")
        # filename = f'{time_str}.csv'
        default_name = default_filename()
        filename = default_name+'.csv'
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



def save_airQdata_as_csv(row_data,filename:str=None):
    """
    将获得的空气质量数据保存为csv
    """
    if filename == None:
        default_name = default_filename()
        filename = default_name+'.csv'
    else:
        filename = filename+'.csv'

    file_path = get_data_path('data',filename)
    row_data.to_csv(file_path,index=False,encoding='utf-8-sig')
    print(f'{filename}已保存至{file_path}')


def save_movie_info_as_csv(row_data,filename:str = None):
    if filename is None:
        filename = default_filename()
    else:
        filename = filename+'.csv'
    file_path = get_data_path('data',filename)

    try:
        df = pd.DataFrame(row_data)

        fixed_columns = [
            '排名', '标题', "导演&主演&年份&地区&类型", '简介', '评分', '评价人数'
        ]# 固定列

        df = df.reindex(columns = fixed_columns,fill_value = '')
        df.to_csv(file_path,index=False,encoding='utf-8-sig',na_rep='',sep=',',errors='ignore')
        print(f'{filename}已保存至{file_path}')
    except Exception as e:
        print(f'保存失败:{e}')


def get_image_name(url,response):
    ct = response.headers.get('Content-Type', '')
    ext = '.jpg'
    if 'png' in ct:
        ext = '.png'
    elif 'webp' in ct:
        ext = '.webp'
    elif 'jpeg' in ct or 'jpg' in ct:
        ext = '.jpg'
    parsed = urlparse(url)
    base = os.path.basename(parsed.path)
    if base and '.' in base:
        name_part, ext_part = os.path.splitext(base)
        if ext_part:
            ext = ext_part
    digest = hashlib.md5(response.content).hexdigest()[:8]
    ts = default_filename()
    filename = f"{ts}_{digest}{ext}"
    if len(filename) > 100:
        name, ext2 = os.path.splitext(filename)
        filename = f"{name[:80]}_{int(time.time())}{ext2}"
    return filename
    
    
    
if __name__ == '__main__':
    image = get_data_path()
    print(type(image),image)
    
