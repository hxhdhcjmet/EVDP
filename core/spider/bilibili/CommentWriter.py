# 将爬取到的评论写入文件

import threading
import os
import json
from core.spider.bilibili.utils import default_filename,get_data_path
class CommentWriter:
    def __init__(self,filename = default_filename()):
        # timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M")
        file_path = get_data_path(filename = filename) # 这里创建的是文件夹,需要进一步创建一个同名文件
        save_file_name = filename+'.jsonl'
        full_file_path = os.path.join(file_path,save_file_name)
        self.filepath = full_file_path
        self.fp = None
        self.lock = threading.Lock()

    def open_for_write(self):
        """
        仅在需要写入时调用
        """
        if not self.fp:
            # 使用a模式
            self.fp = open(self.filepath,'a',encoding = 'utf-8')


        # try:
        #     with open(full_file_path,'x',encoding = 'utf-8') as f:
        #         pass
        #     print(f'初始化成功,保存文件路径:{full_file_path},数据文件与文件夹同名,为:{save_file_name}')
        # except FileExistsError:
        #     print('保存文件已存在,将不重复创建!')
        # except Exception as e:
        #     print(f'初始化评论爬取类,创建文件时发生错误:{e}')
        # finally:
        #     self.filepath = full_file_path
        #     self.fp = open(self.filepath,'w',encoding = 'utf-8')

    def write(self,data):
        if not self.fp:
            self.open_for_write()
        with self.lock:
            self.fp.write(json.dumps(data,ensure_ascii=False)+'\n')

    def close(self):
        if self.fp:
            self.fp.close()
        