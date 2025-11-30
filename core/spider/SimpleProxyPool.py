import random
import requests
import threading
import asyncio
import aiohttp
import time
from bs4 import BeautifulSoup
from concurrent.futures import ThreadPoolExecutor,as_completed

MAX_PAGES = 2 # 最大抓取页数

BASE_URl = "https://www.89ip.cn/index_{page}.html"


# 你原来的类结构保持不变
class SimpleProxyPool:
    def __init__(self):
        self.proxy_list = []
        self.lock = threading.Lock()
        self.refresh_frequency = 300

        # 新的代理源（不会 521）
        self.sources = [
            "https://www.89ip.cn/index_1.html",
            "https://www.89ip.cn/index_2.html",
            "http://proxylist.fatezero.org/proxy.list",
            "https://raw.githubusercontent.com/TheSpeedX/PROXY-List/master/http.txt"
        ]
    def get_from_github(self):
        """
        从github获取代理列表
        """
        response = requests.get(self.sources[3])
        if response.status_code == 200:
            proxies = response.text.splitlines()[:100]
            with self.lock:
                self.proxy_list.extend(proxies)
            self.proxy_list = list(set(self.proxy_list)) # 去重
            print(f'从githubuser处获得代理:{len(self.proxy_list)}条')


    # ----------------------------------------------------------------------
    # 抓取代理：保持你的函数名、功能，但换成稳定数据源
    # ----------------------------------------------------------------------
    def _get_free_proxies(self):
        proxies = []

        headers = {
            "User-Agent": "Mozilla/5.0"
        }
        for page in range(1,MAX_PAGES+1):
            print(f'正在获取第{page}页代理...')
            url = f"https://www.89ip.cn/index_{page}.html"
            try:
                response = requests.get(url,headers = headers,timeout = 10)
                if response.status_code == 200:
                    soup = BeautifulSoup(response.text,'html.parser')
                    table = soup.find_all('table',class_ = 'layui-table')[0]
                    rows = table.find_all('tr')[1:]   # 跳过表头
                    for row in rows:
                        content = row.find_all('td')
                        ip = content[0].text.strip()
                        port = content[1].text.strip()
                        self.proxy_list.append(fr'http://{ip}:{port}')
                    self.proxy_list = list(set(self.proxy_list)) # 去重
                    
                else:
                    print(f'访问失败,状态码{response.status_code}')
            except Exception as e:
                print(f'发生错误:{e}')

    def verify_proxy(self,proxy):
        """
        验证代理有效性
        """
        proxies = {
            'http':proxy,
            'https':proxy
        }
        test_url = 'http://www.baidu.com'
        try:
            response = requests.get(test_url,proxies = proxies,timeout = 5,allow_redirects=False)
            if  200<= response.status_code  <= 307:
                return True
            else:
                print(f'无效原因:{response.status_code}')
                return False
        except Exception as e:
            print('错误原因',e)
            return False
    
    def verify(self):
        """
        多线程验证代理有效性
        """
        print('开始验证代理有效性...')
        start = time.time()
        valid_proxies = []
        with ThreadPoolExecutor(max_workers = 20) as executor:
            futures = {executor.submit(self.verify_proxy,proxy):proxy for proxy in self.proxy_list}
            for future in as_completed(futures):
                proxy = futures[future]
                try:
                    if future.result():
                        valid_proxies.append(proxy)
                    else:
                        print('无效代理')
                except Exception as e:
                    print('验证时发生错误:',e)
        with self.lock:
            self.proxy_list = valid_proxies
        print(f'验证完成,有效代理:{len(self.proxy_list)},耗时:{time.time()-start:.2f}秒')
    
    def get_random_proxy(self):
        """
        返回随机代理
        """
        return random.choice(self.proxy_list if self.proxy_list else None)  



if __name__ == '__main__':
    proxypool = SimpleProxyPool()
    proxypool.get_from_github()
    proxypool._get_free_proxies()
    proxypool.verify()

    
    
