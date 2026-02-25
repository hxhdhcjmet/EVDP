# 工具类函数

import time
import os
import datetime
import json



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




class CookieManager:
    def __init__(self,row_cookie:str,save_path:str):
        self.row_cookie = row_cookie
        self.save_path = save_path

    def _parse_expires_from_cookie_value_(self,key,value):
        """
        从Cookie值中解析expires时间戳,不同Cookie有不同的解析规则
        Args:
            key: Cookie名称
            value: Cookie值
        Returns:
            int/float: 解析后的时间戳，-1表示永不过期
        """
        # 1. sid_guard格式：xxx|1771400415|5184000|Sun, 19-Apr-2026 07:40:15 GMT
        if key == "sid_guard":
            try:
                parts = value.split('|')
                if len(parts) >= 4:
                    # 解析GMT时间字符串为时间戳
                    gmt_time_str = parts[3].replace('+0000', '').strip()
                    # 处理不同的时间格式
                    try:
                        # 格式1: Sun, 19-Apr-2026 07:40:15 GMT
                        dt = datetime.strptime(gmt_time_str, '%a, %d-%b-%Y %H:%M:%S %Z')
                    except:
                        try:
                            # 格式2: Sun, 19 Apr 2026 07:40:15 GMT
                            dt = datetime.strptime(gmt_time_str, '%a, %d %b %Y %H:%M:%S %Z')
                        except:
                            # 用时间戳字段
                            return int(parts[1]) + int(parts[2])
                    return dt.timestamp()
            except:
                return -1
        
        # 2. 登录时间相关Cookie，过期时间设为1年
        elif key in ["login_time", "uid_tt", "sessionid", "sessionid_ss", "sid_tt"]:
            try:
                login_ts = int(value) / 1000 if len(value) > 10 else int(value)
                return login_ts + 365 * 24 * 3600  # 登录后1年过期
            except:
                return -1
        
        # 3. 默认：-1表示永不过期
        return -1


    def cookie_str_to_full_cookie_list(self,default_domain=".douyin.com", default_path="/", 
                                        default_httpOnly=False, default_secure=False, 
                                        default_sameSite="Lax"):
        """
        将字符串格式的cookie转换为包含完整字段的列表字典格式（expires从原始Cookie提取）
        
        Args:
            cookie_str: 原始cookie字符串
            default_domain: 默认domain
            default_path: 默认path
            default_httpOnly: 默认httpOnly属性
            default_secure: 默认secure属性
            default_sameSite: 默认sameSite属性
            
        Returns:
            list: 包含完整cookie字段的列表
        """
        cookie_list = []
        cookie_str = self.row_cookie
        
        if not cookie_str or cookie_str.strip() == "":
            return cookie_list
        
        # 按分号分割cookie键值对
        cookie_pairs = cookie_str.split(';')
        
        for pair in cookie_pairs:
            # 去除首尾空格
            pair = pair.strip()
            # 跳过空的键值对
            if not pair:
                continue
            
            # 按第一个等号分割（避免value中包含等号的情况）
            if '=' in pair:
                key, value = pair.split('=', 1)
                # 清理键名和值的空格
                key = key.strip()
                value = value.strip()
                # 跳过无意义的空键/空值
                if key and value:
                    # 解析expires时间戳（从原始Cookie提取）
                    expires = self._parse_expires_from_cookie_value_(key, value)
                    
                    # 构建完整的cookie字典
                    cookie_dict = {
                        "name": key,
                        "value": value,
                        "domain": default_domain,
                        "path": default_path,
                        "expires": expires,
                        "httpOnly": default_httpOnly,
                        "secure": default_secure,
                        "sameSite": default_sameSite
                    }
                    cookie_list.append(cookie_dict)
        cookie_json = json.dumps(cookie_list,indent=4, ensure_ascii=False)
        with open(self.save_path,'w',encoding = "utf-8") as f:
            f.write(cookie_json)

        
        