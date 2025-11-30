# 获取社交媒体帖子内容信息
# 百度贴吧
# 知乎


import requests
import re
import json
import time
import os
import random
from pathlib import Path
from playwright.sync_api import sync_playwright
from bs4 import BeautifulSoup
from concurrent.futures import ThreadPoolExecutor,as_completed
from tqdm import tqdm
from urllib.parse import urlparse
from utils import get_image_name,get_data_path

BASE_DIR = Path(__file__).resolve().parent # 脚本所在文件夹
COOKIE_DIR = BASE_DIR / "cookies"
PROFILE_DIR = BASE_DIR / "profile"# persistent profile存放目录
COOKIE_DIR.mkdir(exist_ok = True)
PROFILE_DIR.mkdir(exist_ok = True)




# 随机user_agent列表,防止被封
USER_AGENTS = [
    # Chrome on Windows 10
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/109.0.0.0 Safari/537.36",
    # Chrome on macOS
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/109.0.0.0 Safari/537.36",
    # Firefox on Windows 10
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:108.0) Gecko/20100101 Firefox/108.0",
    # Firefox on macOS
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10.15; rv:108.0) Gecko/20100101 Firefox/108.0",
    # Safari on macOS
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/16.1 Safari/605.1.15",
    # Edge on Windows 10
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/108.0.0.0 Safari/537.36 Edg/108.0.1462.42",
]


# 访问ua
TIEBA_HEADERS={
    # 核心标识（贴吧校验必含）
    "Host": "tieba.baidu.com",  # 固定贴吧域名，不可修改
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/139.0.0.0 Safari/537.36",  # 最新Chrome标识，模拟真实用户
    "Connection": "keep-alive",
    
    # 内容协商（匹配贴吧返回格式）
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7",
    "Accept-Encoding": "gzip, deflate, br, zstd",  # 贴吧支持的压缩格式
    "Accept-Language": "zh-CN,zh;q=0.9,en;q=0.8",  # 优先中文，符合贴吧场景
    
    # 缓存控制（避免旧内容，贴吧动态内容多）
    "Cache-Control": "no-cache",
    "Pragma": "no-cache",
    
    # 防盗链与跨域（贴吧重点校验字段）
    "Referer": "https://tieba.baidu.com/",  # 来源必须是贴吧自身，避免防盗链拦截
    "Origin": "https://tieba.baidu.com",  # 跨域请求时匹配，非跨域也保留（增强真实性）
    
    # 浏览器特征（模拟Chrome最新版，避开特征检测）
    "Sec-CH-UA": '"Chromium";v="139", "Not=A?Brand";v="8", "Google Chrome";v="139"',
    "Sec-CH-UA-Mobile": "?0",  # 桌面端（移动端可改为 ?1，配合对应User-Agent）
    "Sec-CH-UA-Platform": '"Windows"',  # 操作系统（macOS/Linux可替换为对应值）
    "Sec-Fetch-Dest": "document",  # 访问贴吧页面用 document；调用接口用 empty
    "Sec-Fetch-Mode": "navigate",  # 页面跳转用 navigate；接口请求用 cors
    "Sec-Fetch-Site": "same-origin",  # 同域名请求，固定 same-origin
    "Sec-Fetch-User": "?1",  # 用户主动触发，模拟点击访问
    "Upgrade-Insecure-Requests": "1",  # 强制HTTPS，贴吧已全站HTTPS
    
    # 登录态相关（需登录后操作时添加，替换为自己的Cookie）
    "Cookie": "BAIDUID=D3616ACDBB7A6A3911B6CED3B9EE7CAD:FG=1; BAIDUID_BFESS=D3616ACDBB7A6A3911B6CED3B9EE7CAD:FG=1; BIDUPSID=D3616ACDBB7A6A3911B6CED3B9EE7CAD; PSTM=1760858689; BAIDU_WISE_UID=wapp_1763474395463_868; H_PS_PSSID=60274_65800_65361_65989_66057_66108_65866_66142_66224_66199_66162_66303_66356_66321_66340_66381_66254_66273_66393_66435_66395_66477_66519_66529; wise_device=0; USER_JUMP=-1; Hm_lvt_292b2e1608b0823c1cb6beef7243ef34=1763624338,1763827918,1764047036,1764495968; HMACCOUNT=FE5C9BB5F54528E0; video_bubble0=1; arialoadData=false; st_key_id=17; ppfuid=FOCoIC3q5fKa8fgJnwzbE67EJ49BGJeplOzf+4l4EOvDuu2RXBRv6R3A1AZMa49I27C0gDDLrJyxcIIeAeEhD8JYsoLTpBiaCXhLqvzbzmvy3SeAW17tKgNq/Xx+RgOdb8TWCFe62MVrDTY6lMf2GrfqL8c87KLF2qFER3obJGnsqkZri/4OJbm7r4CyJIowGEimjy3MrXEpSuItnI4KD4fjIlZ2ecytbQIdvNGR1YpJoInxmnRdG3FZ6g498cYlDRs5uwxNLoGCsDA4eWixpRJsVwXkGdF24AsEQ3K5XBbh9EHAWDOg2T1ejpq0s2eFy9ar/j566XqWDobGoNNfmfpaEhZpob9le2b5QIEdiQdtJfhN1eLb/i/C9hcVPjDWFCMUN0p4SXVVUMsKNJv2T6OLplwoChxYN5dlTZk+bcHasmgOrJ40n63OsKSOpoSLs44C79cnwEM1bKFV00Jh1g8FgmBulEX1NIsJI/2qJK/Q+//wdrn6SUz7a0vEMm7QqGqBJJILGchC/ZM0axiniVRKx4R3cqVpTVNqTP1tWGnGGu/AVLS3NcPF3XemJkZyi6L0BPA661JDj0lmZIgcCHm0lGODoYWzuL7ZDizBm0d8BJIJUS1lUOPNebjg5OCjwkSq16g64gugrO/OhN+XjRMTNne43cKuMDmex1CEngB2QvyTjxXMcJvDDEe3McIycHFbZmbEY9LT3RuWsSjij5HIeKAxeCJRzKQmiJrt2NfmujPmSvwwcsjL97Gs89pRU3eykTJn4tcTUXl65JM0UyyMcJOPP8jPyaezwVp7oiJ/q1uQn9VsBjBmLNQsYnwiX1i39zQE19TGybrzqrM1pDNXcybRETVwM6jql+eIXlewf4jZIONqitUD98U0FeHk4vnOZOyajeVuJqw/hTdAQtApplNnCjhwNPVCEwOM+fgoewyfnTeyYbFNvWZZSblAHHxUnYx9OEBH0ljzkFSY+Oo6VuGtuVcWQFAbufgkqJnJqWT1fbYVd7Yyx2Kk4cXFJQdKps+jY88nMSivXabqVOFHtiCaV8u3uSe0kPld4zsYRDDc4ujl2xJR5AN3q8OeRvvb9Mxhxs9bjxa5KdKAwMvzbQbq/mwgjd9siXUizBEYRDDc4ujl2xJR5AN3q8Oe1WWULX5oIJzwrbxFaliZTRLbhH0MNlXHePf60sunDcFG4X+UjvIZDl0Se0IQy2dV3g0r2enUpE2z8YgtK7508RTllnZC81hhWPgxy+x2ZmXayxvT1iTUpRrGE132K7Dr; XFI=d87ecae0-cddd-11f0-8136-7dd85bf0943e; XFCS=859697508E4191B2EA955B3DC0EC598080548998283D31BD26451D5B08C37E63; XFT=V498h0ZZjo8u0fj47EVDJlio4hypc2tw9Xp+fD5vG1c=; ZFY=O6UCK4xbPtdtCLURpnMdoMBKuVMdMSxvjblECUyJonM:C; BA_HECTOR=ak21aha4a0850h210k2gah0h042g221kio9qe24; Hm_lpvt_292b2e1608b0823c1cb6beef7243ef34=1764501329; ariaappid=c890648bf4dd00d05eb9751dd0548c30; ariauseGraymode=false; ab_sr=1.0.1_MjdiZmRmMGViOTRkN2NjN2Y5ZTdiY2I3MzYzYjFlMmIwN2I4NGE4N2E3ZWNkMjliNjg3MDVkOWM4NDljYzk1M2E3MTEzYzcyYWE3ZWU2OGFhZGYyZjY3ODM3MTk1NzRmZDgyOGI1YWM3ZmYwNDFiMmI0MDFhMDg0MzRhYWJmZDQ3M2FlNTFiZmE3YTU3ZTgzMTUyMjg0MGU5MWI5ZjJkYg==; st_data=2406f74341f8d8709d6456fd3a6e23b93093a7a7607926cd16fb30995b5833338167b57e51640807cc362be1d293dc6669a2fa05d5b16d66ce0f264d51d07b0d3cead91b57ae18e41fc2a610c401a56975e769c67fddf5911fe0c45fbf7b25c137325b42a796e60f62c4fe94843c601aba732f2f52967d655466611c6ee66576c271558a3281fed90396edd007ef4622; st_sign=4833cb98",  # 从浏览器F12复制真实Cookie
    # 接口请求额外字段（异步加载内容时添加）
    # "X-Requested-With": "XMLHttpRequest"  # 异步接口（如加载更多、签到）必加
}


# 下载ua
DOWN_HEADERS = { 
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/128.0.0.0 Safari/537.36',
                'Host': 'tiebapic.baidu.com',  # 明确指定Host
                'Referer': 'https://tieba.baidu.com/',  # 必须是贴吧域名
                'Accept': 'image/webp,image/apng,image/svg+xml,image/*,*/*;q=0.8',
                'Accept-Encoding': 'gzip, deflate, br',
                'Accept-Language': 'zh-CN,zh;q=0.9,en;q=0.8',
                'Cookie': 'BAIDUID=D3616ACDBB7A6A3911B6CED3B9EE7CAD:FG=1; BAIDUID_BFESS=D3616ACDBB7A6A3911B6CED3B9EE7CAD:FG=1; BIDUPSID=D3616ACDBB7A6A3911B6CED3B9EE7CAD; PSTM=1760858689; BAIDU_WISE_UID=wapp_1763474395463_868; RT="z=1&dm=baidu.com&si=842187d5-e610-4ca2-983c-902ec7924c08&ss=mi5bvhmh&sl=0&tt=0&bcn=https%3A%2F%2Ffclog.baidu.com%2Flog%2Fweirwood%3Ftype%3Dperf&ul=1v9b&hd=1v9u"; H_PS_PSSID=60274_65800_65361_65989_66057_66108_65866_66142_66224_66199_66162_66303_66356_66321_66340_66381_66254_66273_66393_66435_66395_66477_66519_66529; ZFY=y6E8rVI1:BgXbttQ3r1FD9:Am:ANDlb5JEA4oyVJPa:BhGE:C; BA_HECTOR=80a48l0ka12g24250h84802la08gal1kiae5s25; ariaappid=c890648bf4dd00d05eb9751dd0548c30; ariauseGraymode=false; ab_sr=1.0.1_NDgxZDBiYjIwNTk4MTlmYWZhODlhOTFlZDcyN2M5ZjBjMWM5MzAxZTBhYzQzOGY5YzlkNTg4NDIxOTE4YzMzNmI1NDY3NTMwYzI5MmViNDI2ZmM0MzVhMDk2OWI0MjZmMGNmYjJhYTFkMzk1MDJjNWJiYWQ3M2YxYTg5MjdkZmUxZDJiZGQwYjQ4ZmVlZDhjNzNmOWZlNTYwMzJiMjk0Ng==; arialoadData=false; ppfuid=FOCoIC3q5fKa8fgJnwzbE67EJ49BGJeplOzf+4l4EOvDuu2RXBRv6R3A1AZMa49I27C0gDDLrJyxcIIeAeEhD8JYsoLTpBiaCXhLqvzbzmvy3SeAW17tKgNq/Xx+RgOdb8TWCFe62MVrDTY6lMf2GrfqL8c87KLF2qFER3obJGnsqkZri/4OJbm7r4CyJIowGEimjy3MrXEpSuItnI4KD4fjIlZ2ecytbQIdvNGR1YpJoInxmnRdG3FZ6g498cYlDRs5uwxNLoGCsDA4eWixpRJsVwXkGdF24AsEQ3K5XBbh9EHAWDOg2T1ejpq0s2eFy9ar/j566XqWDobGoNNfmfpaEhZpob9le2b5QIEdiQdtJfhN1eLb/i/C9hcVPjDWFCMUN0p4SXVVUMsKNJv2T6OLplwoChxYN5dlTZk+bcHasmgOrJ40n63OsKSOpoSLs44C79cnwEM1bKFV00Jh1g8FgmBulEX1NIsJI/2qJK/Q+//wdrn6SUz7a0vEMm7QqGqBJJILGchC/ZM0axiniVRKx4R3cqVpTVNqTP1tWGnGGu/AVLS3NcPF3XemJkZyi6L0BPA661JDj0lmZIgcCHm0lGODoYWzuL7ZDizBm0d8BJIJUS1lUOPNebjg5OCjwkSq16g64gugrO/OhN+XjRMTNne43cKuMDmex1CEngB2QvyTjxXMcJvDDEe3McIycHFbZmbEY9LT3RuWsSjij5HIeKAxeCJRzKQmiJrt2NfmujPmSvwwcsjL97Gs89pRU3eykTJn4tcTUXl65JM0UyyMcJOPP8jPyaezwVp7oiJ/q1uQn9VsBjBmLNQsYnwiX1i39zQE19TGybrzqrM1pDNXcybRETVwM6jql+eIXlewf4jZIONqitUD98U0FeHk4vnOZOyajeVuJqw/hTdAQtApplNnCjhwNPVCEwOM+fgoewyfnTeyYbFNvWZZSblAHHxUnYx9OEBH0ljzkFSY+Oo6VuGtuVcWQFAbufgkqJnJqWT1fbYVd7Yyx2Kk4cXFJQdKps+jY88nMSivXabqVOFHtiCaV8u3uSe0kPld4zsYRDDc4ujl2xJR5AN3q8OeRvvb9Mxhxs9bjxa5KdKAwMvzbQbq/mwgjd9siXUizBEYRDDc4ujl2xJR5AN3q8Oe1WWULX5oIJzwrbxFaliZTRLbhH0MNlXHePf60sunDcFG4X+UjvIZDl0Se0IQy2dV3g0r2enUpE2z8YgtK7508RTllnZC81hhWPgxy+x2ZmXayxvT1iTUpRrGE132K7Dr',  # 关键！添加真实Cookie
                'Connection': 'keep-alive',  # 保持连接
                'Cache-Control': 'no-cache'

}




# ---------------------工具类函数-----------------
def random_sleep(a = 0.5,b = 1.5):
    time.sleep(random.uniform(a,b))

def human_scroll(page,scroll_times = 3):
    """
    模拟滚动页面行为
    """
    for _ in range(scroll_times):
        # 随机往下滚动一段距离
        page.mouse.wheel(0,random.randint(200,800))
        random_sleep(0.3,1.2)

def human_move_mouse(page,steps = 10):
    """
    模拟鼠标移动到随机位置
    """
    viewport = page.viewport_size or {"width":1200,"height":800}
    w,h = viewport["width"],viewport["height"]
    start_x = random.randint(int(w*0.2),int(w*0.8))
    start_y = random.randint(int(h*0.2),int(h*0.8))
    page.mouse.move(start_x,start_y)
    for _ in range(steps):
        nx = start_x+random.randint(-100,100)
        ny = start_y+random.randint(-100,100)
        page.mouse.move(max(0,mx),max(0,ny))
        random_sleep(0.01,0.1)



def generate_random_user_agent():
    """
    生成随机uer_agent头
    """
    DOWN_HEADERS['User-Agent'] = random.choice(USER_AGENTS)
    TIEBA_HEADERS['User-AGENT'] = random.choice(USER_AGENTS)



# =======================================




class TiebaImageDownloader:
    """
    贴吧图片下载器
    """
    def __init__(self,image_urls,save_dir = 'tieba_images',max_workers = 5,timeout = 15,delay = 0.8):
        """
        初始化下载器类
        image_urls:图片链接列表
        save_dir:保存目录
        max_workers:线程池最大线程数
        time_out:请求超时时间
        """
        self.image_urls = image_urls
        self.save_dir = save_dir
        self.max_workers = max_workers
        self.timeout = timeout
        self.delay = delay # 加点延迟

        # 统计信息
        self.success_count = 0
        self.fail_count = 0
        self.fail_urls = []


    def deduplicate_urls(self,image_urls:list)->list:
        """
        对图片链接去重
        """
        return list(set(image_urls))
    

    def download_single_image(self,url):
        """
        下载单张图片
        """
        time.sleep(random.uniform(0.1,self.delay)) # 随机延迟
        try:
            generate_random_user_agent() # 每次下载前生成随机ua
            response = requests.get(url,headers = DOWN_HEADERS,timeout = self.timeout,stream = True)
            response.raise_for_status() # 抛出http错误
            # 创建文件夹
            dirpath = get_data_path('data',self.save_dir)


            # 获取文件名
            filename = get_image_name(url,response) 
            save_path = os.path.join(dirpath,filename) # 创建下载图片文件夹

            # 避免覆盖已有文件
            if os.path.exists(save_path):
                name,ext = os.path.splitext(filename)
                save_path = os.path.join(self.save_dir, f"{name}_{int(time.time())}{ext}")

                # 下载并保存
            with open(save_path,'wb') as f:
                for chunk in response.iter_content(chunk_size = 1024*1024):
                    if chunk:
                        f.write(chunk)
            print(f'图片{filename}下载完成!')
            return (True,url,save_path)

        except requests.exceptions.RequestException as e:
            error_msg = f"网络问题:{str(e)}"
            return False,url,error_msg
        except Exception as e:
            error_msg = f"未知问题:{str(e)}"
            return False,url,error_msg


            
    def download_all_images(self):
        """
        批量下载
        """
        print(f'\n开始下载图片,共{len(self.image_urls)}张')
        start_time = time.time()

        # 线程池下载
        with ThreadPoolExecutor(max_workers = self.max_workers) as executor:
            futures = []
            for url in self.image_urls:
                futures.append(executor.submit(self.download_single_image,url))
                time.sleep(random.uniform(0.1,self.delay)) # 控制提交任务间隔,防止过快
                for future in as_completed(futures):
                    success,url,result = future.result()
                    if success:
                        self.success_count += 1
                    else:
                        self.fail_count+=1
                        self.fail_urls.append((url,result))
 
        # 循环下载，不通过线程池
        # for url in self.image_urls:
        #     success,url,result = self.download_single_image(url)
        #     if success:
        #         self.success_count += 1
        #     else:
        #         self.fail_count+=1
        #         self.fail_urls.append((url,result))


       

        # 输出统计信息
        end_time = time.time()
        total_time = end_time -start_time
        print("\n"+"="*50)
        print(f'下载完成!总用时:{total_time:.2f}秒')
        print(f'总图片数:{len(self.image_urls)}张')
        print(f'成功下载:{self.success_count}张')
        print(f'下载失败:{self.fail_count}张')
        print('='*50)

        if self.fail_urls:
            print(f'\n下载失败链接{len(self.fail_urls)}个:')
            for url,reason in self.fail_urls:
                print(f'{url}:下载失败原因:{reason}')



def tieba_crawl_all(url):
    """
    根据链接下载百度贴吧帖子下面的回复信息
    """
    https_head = 'https://tieba.baidu.com' # 所有链接拼接完整

    generate_random_user_agent() # 生成随机ua
    response = requests.get(url = url,headers = TIEBA_HEADERS)
    if response.status_code == 200:
        soup = BeautifulSoup(response.text,'html.parser')

        # 获取"只看楼主"页面
        lzonly = url+'?see_lz=1'

        # 获取下一页控制信息
        # next_page = soup.find('li',class_ = 'l_pager pager_theme_4 pb_list_pager')
        # next_page_urls = [url]

        # if next_page:
        #     next_page_url = [npu.get('href') for npu in next_page.find_all('a')][:-2] # 去掉最后两个为 "下一页"、"尾页"
        #     nextNum = len(next_page_url)
        #     for i in range(nextNum):
        #         next_page_urls.append(url+f'?pn={i+2}')
        # else:
        #     print('获取页面列表失败')

        # 获取所有分页链接
        total_page_size = soup.select('#thread_theme_5 > div.l_thread_info > ul > li:nth-child(2) > span:nth-child(2)')
        if total_page_size:
            total_page_size = int(total_page_size[0].text.strip())
            next_page_urls = [url+f'?pn={i+1}' for i in range(total_page_size)]

        

        
        print(f'总共{len(next_page_urls)}页帖子')
        extract_num = 20 # 提取前20页信息做测试
        next_page_urls = next_page_urls[:extract_num]
        print(f'实际提取{len(next_page_urls)}页帖子信息')


        names = [] # 昵称
        user_ids = [] # 用户id
        personal_links = [] # 个人主页链接
        comments = [] # 回复帖子信息
        images = [] # 获取图片链接，可用于保存图片
        page = 1

        for link in next_page_urls:
            try:
                print(f'正在获取第{page}页信息...')
                each_page_do(link,names,user_ids,personal_links,comments,images,https_head)
                print(f'第{page}页信息获取成功!')
            except Exception as e:
                print(f'第{page}页帖子信息获取异常:{e}')
    
            page+=1
            time.sleep(random.uniform(1.0,2.5)) # 随机延迟

         # 对获取的链接信息去重
        personal_links = list(set(personal_links))
        images = list(set(images))
        

        print('\n'+'='*50)
        print('所有页面信息获取完毕!')
        
        # 获取统计信息
        names_len = len(names)
        user_ids_len = len(user_ids)
        personal_links_len = len(personal_links)
        comments_len = len(comments)
        images_len = len(images)
        print(f'共获取昵称:{names_len}个')
        print(f'共获取用户id:{user_ids_len}个')
        print(f'共获取去重后个人主页链接:{personal_links_len}个')
        print(f'共获取回复帖子信息:{comments_len}条')
        print(f'共获取去重后图片链接:{images_len}个')


        print('='*50+'\n')
        return names,user_ids,personal_links,comments,images

        
        
    else:
        print(f'请求错误,状态码:{response.status_code}')

def each_page_do(url:str,names:list,user_ids:list,personal_links:list,comments:list,images:list,https_head:str):
    """
    在每个页面下作信息提取的函数
    """
    response = requests.get(url = url ,headers = TIEBA_HEADERS)
    if response.status_code == 200:
        soup = BeautifulSoup(response.text,'html.parser')
        # 先定位到帖子部分
        postlist = soup.find('div',class_ = 'p_postlist')
        if postlist:
            author = postlist.find_all('ul',class_ = 'p_author') # 昵称
            user_id = postlist.find_all('li',class_ = 'd_name') # id
            personal_link = postlist.find_all('a',class_ = 'p_author_name j_user_card')# 主页链接
            comment = postlist.find_all('div',class_ = 'd_post_content j_d_post_content') # 获取回复
            image = postlist.find_all('img',class_ = 'BDE_Image') # 获取图片内容

            if author:
                for name in author:
                    names.append(name.text.strip().replace('\n',''))

            else:
                print('获取个人信息失败')

            if user_id:
                for userid in user_id:
                    # 获取的id是 '{"user_id":xxxxx}'格式的字符串,先去'"user_id":',再去掉左右大括号
                    userid = userid.get('data-field').replace('"user_id":','').strip('{}')
                    user_ids.append(userid)

            else:
                print('获取id失败')
            
            # 获取个人主页网址
            if personal_link:
                for plink in personal_link:
                    plink = https_head+plink.get('href')
                    personal_links.append(plink)

            else:
                print('获取主页链接失败')

            # 获取回复信息
            if comment:
                for comm in comment:
                    comments.append(comm.text.strip() if len(comm.text.strip())!=0 else '图片等非文字回复内容')

            else:
                print('获取每人发帖信息失败')

            if image:
                for img in image:
                    images.append(img.get('src'))
            else:
                print('获取图片链接失败')

        else:
            print(f'帖子回复信息获取失败')
    else:
        print(f'{url}访问失败,状态码:{response.status_code}')







if __name__ == '__main__':
    url = r'https://tieba.baidu.com/p/7892470381'
    names,user_ids,personal_links,comments,images =  tieba_crawl_all(url)
    down = TiebaImageDownloader(images[:50]) # 初始化下载类
    down.download_all_images()
    



