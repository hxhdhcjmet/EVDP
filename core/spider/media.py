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
from concurrent.futures import ThreadPoolExecutor,as_compled
from tqdm import tqdm

BASE_DIR = Path(__file__).resolve().parent # 脚本所在文件夹
COOKIE_DIR = BASE_DIR / "cookies"
PROFILE_DIR = BASE_DIR / "profile"# persistent profile存放目录
COOKIE_DIR.mkdir(exist_ok = True)
PROFILE_DIR.mkdir(exist_ok = True)

# user-agent头
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
    "Cookie": "BIDUPSID=DBE6076EC2C0EC31FBE72F9485E0358A;PSTM=1755176313; MCITY=-%3A; H_WISE_SIDS_BFESS=62327_63143_63327_63948_64005_64048_64090_64174_64247_64246_64258_64261_64272_64318_64366_64362_64363_64416_64425_64437_64450_64459_64479_64485_64501_64514_64448_64087_64556; BAIDUID=F3DA61729F2FF55197A6EB9E8181AF57:FG=1; H_PS_PSSID=62325_63141_63325_63948_64174_64247_64314_64358_64366_64361_64364_64395_64439_64443_64450_64462_64471_64483_64502_64512_64087_64562_64568_64574_64591_64597_64596_64602; H_WISE_SIDS=62325_63141_63325_63948_64174_64247_64314_64358_64366_64361_64364_64395_64439_64443_64450_64462_64471_64483_64502_64512_64087_64562_64568_64574_64591_64597_64596_64602; BAIDUID_BFESS=F3DA61729F2FF55197A6EB9E8181AF57:FG=1; __bid_n=197120f0bd2550424f2fed; scholar_new_version=1; Hm_lvt_292b2e1608b0823c1cb6beef7243ef34=1763473405; HMACCOUNT=CFFD7F63486FDC44; BAIDU_WISE_UID=wapp_1763473402325_86; USER_JUMP=-1; BAIDU_SSP_lcr=https://cn.bing.com/; st_key_id=17; arialoadData=false; ppfuid=FOCoIC3q5fKa8fgJnwzbE67EJ49BGJeplOzf+4l4EOvDuu2RXBRv6R3A1AZMa49I27C0gDDLrJyxcIIeAeEhD8JYsoLTpBiaCXhLqvzbzmvy3SeAW17tKgNq/Xx+RgOdb8TWCFe62MVrDTY6lMf2GrfqL8c87KLF2qFER3obJGnsqkZri/4OJbm7r4CyJIowGEimjy3MrXEpSuItnI4KD7cPaJi+EtbDcJgnQk/tNlLZmOvCi7lsE0/UM0w4HSMVKV6TtZPdnfPwavqz1YlANFCkfVyqzHN/SxYAXZ6d2tzGgLbz7OSojK1zRbqBESR5Pdk2R9IA3lxxOVzA+Iw1TWLSgWjlFVG9Xmh1+20oPSbrzvDjYtVPmZ+9/6evcXmhcO1Y58MgLozKnaQIaLfWRHYJbniad6MOTaDR3XV1dTIPexGF1prpvWLuC+Z/MajfC+8txIZSGBmWKsHQdG2iG3eTNkbS2el0J2+pbyoXJb0q7mN8ihyjCuxjpwkmHnWMqfhwWryYacZfOfIdenDLSkJsc4rBzsbBPyjKAzWGBO7nCxNtgYtDo26K+8ukl31Y+/geIrmTvn+xVA1gAbbf1lkKhylX1zGsOVlJip30kecMEGvjdNWpsel/qfsfe5JBpqDTksMVoBr7nszRboiUHbedcq1mi/UXvX2b3lxbCLv4Mxoy+dFS3Fr9jSAmssiPARPZutqXQT8krr+KVakPUpdbkwv/8CHDu0C/Z5vtDeiYLQpEgFjmQoey69Fz+kM7Y5cg925MGCeBU4jWp2g2g/26eTIZ94Kn7DT9ssnkkiBXYHkU/8mt94O5z1Xj3TEHmu6E7ZsaVQWbJ05JHlQRNUhpOuhw8bYyjFOBzzWtHbYbSa9AM5B1U28ZEDPBEvSMRPgS91Uw7CJQXNUDxDR+gXJQoG0sQhLOfQ+H6CPhLu1e5pW3qVm6jGndb2e9A44FBq40twT0SdgxNxGH6dx/+2zinVPKXI+oymb7UrF2I+ZEd6VO50CmaP+JD/V8nCK/kazYq146hp/2XIWCky++QvQau87dgPQPBPOdZfELQaEBSLlhBmNwzEBsxOHy7QZw9iAQNcYCK2xfeYf2imATVV3bwYaC8F4XJ12oqlxKXLxUJaJyL/ORX2lW3xKCro0F9iAQNcYCK2xfeYf2imATVYemNDYxCmdd8ZXU4Cg4htkEQSRUz7L4kkhL4CxkTt2IBjr/vyN58BqfauYSxfP9O4KEVJ4njsvVmNwgrtRSkK0qC//MHvADyaJlnxIzTi4GWx4UhpRCqPktHIslB6EWFA==; video_bubble0=1; XFI=adc4fa20-c484-11f0-a299-0574945d15ad; ZFY=vy6DGRGwGEzeaaQUM3tj:BxgE65vtkUKjS72xeBMLSoY:C; XFCS=EB5157D46EF82AB38C61F9FE2EB33DAB526F18C97303503CAD3CB7B2A3BC6DB3; XFT=35U8C85lw3MOlkyV5rAQ2jMNsXdO8qFbrrZlkV5bFaI=; wise_device=0; TIEBAUID=cb23caae14130a0d384a57f1; Hm_lvt_049d6c0ca81a94ed2a9b8ae61b3553a5=1763474060; Hm_lpvt_049d6c0ca81a94ed2a9b8ae61b3553a5=1763474060; TIEBA_SID=H4sIAAAAAAAAA9MFAPiz3ZcBAAAA; Hm_lpvt_292b2e1608b0823c1cb6beef7243ef34=1763474555; BA_HECTOR=a10180aka08h04ak0ka404alag80am1khov3r25; ariaappid=c890648bf4dd00d05eb9751dd0548c30; ariauseGraymode=false; ab_sr=1.0.1_YWVhMTcwYzNmZjFjNzg2ZjMzYmEzODc1NTNhMjRhNmE0OWUwMzEwOTJjNjFlYWVmNDM2MDc4M2RkNWFkM2JiNzRkYWQwOGVhNmFiZGVmZGZhZDI0MmUyNjQzZTYxM2RkMTkwYjg5MGFiYThmN2Q4OTAzMTE3ZGViZGU4YWFlMTc2OThlMmUwYjAzY2EyOWJiYTNkZjc4MjcwYTI3ZWIyMThmMjViZWU3NDUxZTI4ZDUyNTg4MmNmNTZlYzc3M2Nm; st_data=9a7aa8718c2a6fcccbfef9c7fd9018868c9ceb2eb8c03767255884ba6143e0401f778533dd2567fc485e0ec55832514517e52f2b05543e209ad2c9d23ef23007edba3acac4fc3ebef235d3d519a3f7fd4ba8eeb8c84b43909d8351fef2f8cba6987afa4525c075624b32128fe90f1ad4a954a678c1948d83fa1d13f1a45382c3814b6c7fa11c3453a5a1d584b9fccf6b; st_sign=62536e1a",  # 从浏览器F12复制真实Cookie
    # 接口请求额外字段（异步加载内容时添加）
    # "X-Requested-With": "XMLHttpRequest"  # 异步接口（如加载更多、签到）必加
}

# ---------------------工具类函数，模仿真人行为-----------------
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




# =======================================




class CookieManager:
    """
    登陆保存cookie类
    """
    def __init__(self,platform,login_url,success_cookie,cookie_dir = "cookies"):
        self.platform = platform
        self.login_url = login_url
        self.success_cookie = success_cookie
        self.cookie_dir = cookie_dir

        if not os.path.exists(cookie_dir):
            os.makedirs(cookie_dir)

        self.cookie_path = os.path.join(cookie_dir,f'{platform}.json')

    def login_and_save_cookies(self):
        with sync_playwright() as p:
            browser = p.chromium.launch(headless = False)# 打开网页版，能扫码登陆
            context = browser.new_context()
            page = context.new_page()

            print(f'进入{self.platform}登陆页面，请扫码或手动登陆...')
            page.goto(self.login_url,wait_until = 'networkidle')

            # 等待登录成功(通过检测cookie)
            while True:
                cookies = context.cookies()
                if self.success_cookie in [c["name"] for c in cookies]:
                    print(f'{self.platform}登陆成功!')
                    break
                time.sleep(1)

            # 把cookie保存
            with open(self.cookie_path,"w",encoding = 'utf-8') as f:
                json.dump(cookies,f,ensure_ascii = False,indent = 2)
            
            print(f"已保存至{self.platform}cookies->{self.cookie_path}")
            browser.close()

    def load_cookies(self):
        if not os.path.exists(self.cookie_path):
            raise FileNotFoundError(f"{self.cookie_path}不存在,请先登陆。")
        with open(self.cookie_path,"r",encoding = 'utf-8') as f:
            return json.load(f)

# 初始化知乎爬虫
# def get_zhihu_content_by_keyword(keyword:str):
#     # 初始化知乎
#     zhihu = CookieManager(platform = "zhihu",login_url = "https://www.zhihu.com",success_cookie = "z_c0")
#     # 只做一次登陆，即如果没有cookie才登陆
#     if not os.path.exists(zhihu.cookie_path):
#         zhihu.login_and_save_cookies()
#     # 获取cookies
#     cookies = zhihu.load_cookies()

#     with sync_playwright() as p:
#         browser = p.chromium.launch(headless = True)
#         context = browser.new_context()
#         print(page_html[:10000])
#         else:
#             print("空")dd_cookies(cookies)

#         page = context.new_page()
#         target_url  = f"https://www.zhihu.com/search?q={keyword}"
#         page.goto(target_url,wait_until = "networkidle")

#         # 等待异步渲染完成
#         page.wait_for_load_state("networkidle")
#         time.sleep(2)

#         page_html = page.content()

#         if(page_html)


class TiebaImageDownloader:
    """
    贴吧图片下载器
    """
    def __init__(self,image_urls,save_dir = 'tieba_images',max_workers = 10,timeout = 15):
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

        # 统计信息
        self.success_count = 0
        self.fail_count = 0
        self.fail_urls = []


    def deduplicate_urls(self,image_urls:list)->list:
        """
        对图片链接去重
        """
        return list(set(image_urls))



def tieba_crawl_all(url):
    """
    根据链接下载百度贴吧帖子下面的回复信息
    """
    https_head = 'https://tieba.baidu.com' # 所有链接拼接完整

    response = requests.get(url = url,headers = TIEBA_HEADERS)
    if response.status_code == 200:
        soup = BeautifulSoup(response.text,'html.parser')

        # 获取"只看楼主"页面
        lzonly = url+'?see_lz=1'

        # 获取下一页控制信息
        next_page = soup.find('li',class_ = 'l_pager pager_theme_4 pb_list_pager')
        next_page_urls = [url]

        if next_page:
            next_page_url = [npu.get('href') for npu in next_page.find_all('a')][:-2] # 去掉最后两个为 "下一页"、"尾页"
            nextNum = len(next_page_url)
            for i in range(nextNum):
                next_page_urls.append(url+f'?pn={i+2}')
        else:
            print('获取页面列表失败')
        
        names = [] # 昵称
        user_ids = [] # 用户id
        personal_links = [] # 个人主页链接
        comments = [] # 回复帖子信息
        images = [] # 获取图片链接，可用于保存图片
        page = 1

        for link in next_page_urls:
            print(f'总共{len(next_page_urls)}页帖子')
            try:
                print(f'正在获取第{page}页信息...')
                each_page_do(link,names,user_ids,personal_links,comments,images,https_head)
                print(f'第{page}页信息获取成功!')
            except Exception as e:
                print(f'第{page}页帖子信息获取异常:{e}')
            
            page+=1
            time.sleep(1)
        
        print(names,user_ids,personal_links,comments,images)

        
        
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
    url = r'https://tieba.baidu.com/p/10234572512'
    tieba_crawl_all(url)
    



