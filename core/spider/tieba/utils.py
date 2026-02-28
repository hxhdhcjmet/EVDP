# 贴吧工具类

import time
import os
import datetime
import hashlib
from urllib.parse import urlparse

def default_filename():
    """
    创建默认文件名为当前时间
    """
    current_time = datetime.now()
    time_str = current_time.strftime(r'%Y%m%d%H%M%S')
    return time_str


def get_data_path(dir_name:str='data',filename:str=None):
    """
    找到保存文件夹路径、文件夹名和文件名
    """
    #保存到与app.py同级的data文件夹内
    curr_file_path = os.path.abspath(__file__)
    curr_dir = os.path.dirname(curr_file_path)

    parent1 = os.path.dirname(curr_dir)
    parent2 = os.path.dirname(parent1)
    parent3 = os.path.dirname(parent2)

    data_dir = os.path.join(parent3,dir_name) #创建data文件夹

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