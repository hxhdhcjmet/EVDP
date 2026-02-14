# 针对bilibili评论爬取的工具类
from datetime import datetime
import os


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