# 工具类函数

import time
import os



class Garbage:
    # 垃圾类，用于保存、清除日志截图信息
    def __init__(self,base_dir:str):
        self.garbage_path = os.path.join(base_dir,"garbage")
        os.makedirs(self.garbage_path,exist_ok=True) # 创建文件夹
        print(f"垃圾文件夹创建成功:{self.garbage_path}")


    def save_screenshot(self,page,name):
        """
        保存页面截图至garbage文件夹
        """
        filename = f"{name}_{int(time.time())}.png"
        path = os.path.join(self.garbage_path,filename)

        page.screenshot(path = path)

        print(f"截图已保存至:{path}")
        return path

    def clear_garbage(self,t:int = 1):
        """
        清空垃圾文件夹中文件
        t:保存的时间,满足时间自动清空
        """
        if not os.path.exists(self.garbage_path):
            return 
        now = time.time()

        for file in os.listdir(self.garbage_path):
            path = os.path.join(self.garbage_path,file)

            if os.path.isfile(path):
                file_time = os.path.getmtime(path)
                if now - file_time > t * 86400:
                    os.remove(path)
                    print(f"已清理文件:{file}")
    

    def clear_now(self):
        """
        立即清除garbage所有文件
        """
        self.clear_garbage(0)
     

