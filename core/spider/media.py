import os
import time
import random
import re
import json
import hashlib
import requests
import pandas as pd
import sqlite3
from dataclasses import dataclass
from typing import List, Optional, Dict, Any
from urllib.parse import urlparse, quote, parse_qs
from bs4 import BeautifulSoup

try:
    from .utils import get_image_name, get_data_path
except ImportError:
    try:
        from core.spider.utils import get_image_name, get_data_path
    except ImportError:
        from utils import get_image_name, get_data_path

# 访问ua
TIEBA_HEADERS={
    "Host": "tieba.baidu.com",  
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/139.0.0.0 Safari/537.36",  
    "Connection": "keep-alive",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7",
    "Accept-Encoding": "gzip, deflate, br, zstd",  
    "Accept-Language": "zh-CN,zh;q=0.9,en;q=0.8",  
    "Cache-Control": "no-cache",
    "Pragma": "no-cache",
    "Referer": "https://tieba.baidu.com/",  
    "Origin": "https://tieba.baidu.com",  
    "Sec-CH-UA": '"Chromium";v="139", "Not=A?Brand";v="8", "Google Chrome";v="139"',
    "Sec-CH-UA-Mobile": "?0",  
    "Sec-CH-UA-Platform": '"Windows"',  
    "Sec-Fetch-Dest": "document",  
    "Sec-Fetch-Mode": "navigate",  
    "Sec-Fetch-Site": "same-origin",  
    "Sec-Fetch-User": "?1",  
    "Upgrade-Insecure-Requests": "1",  
}

# 下载ua
DOWN_HEADERS = { 
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/128.0.0.0 Safari/537.36',
    'Host': 'tiebapic.baidu.com',  
    'Referer': 'https://tieba.baidu.com/',  
    'Accept': 'image/webp,image/apng,image/svg+xml,image/*,*/*;q=0.8',
    'Accept-Encoding': 'gzip, deflate, br',
    'Accept-Language': 'zh-CN,zh;q=0.9,en;q=0.8',
    'Connection': 'keep-alive',  
    'Cache-Control': 'no-cache'
}

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

def random_sleep(a=0.5, b=1.5):
    """随机延迟，模拟人类操作"""
    time.sleep(random.uniform(a, b))


def generate_random_user_agent():
    """生成随机uer_agent头"""
    DOWN_HEADERS['User-Agent'] = random.choice(USER_AGENTS)
    TIEBA_HEADERS['User-Agent'] = random.choice(USER_AGENTS)


def get_cookie():
    """从文件获取cookie"""
    try:
        # 使用绝对路径
        cookie_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'cookies', 'tieba_cookie.json')
        with open(cookie_path, 'r') as f:
            cookie = json.load(f)
            TIEBA_HEADERS['Cookie'] = cookie['cookie']
            DOWN_HEADERS['Cookie'] = cookie['cookie']
        print(f"成功加载Cookie: {cookie['cookie'][:10]}...")
    except Exception as e:
        print(f"获取cookie失败: {e}")
        # 如果没有Cookie，使用简单的请求头
        TIEBA_HEADERS['Cookie'] = ''
        DOWN_HEADERS['Cookie'] = ''

@dataclass
class TiebaImageDownloader:
    url: str  # 帖子URL
    max_pages: int = 5  # 最大爬取页数
    download_delay: int = 1000  # 下载延迟(毫秒)
    thread_count: int = 5  # 线程数
    max_retries: int = 3  # 最大重试次数

    def __post_init__(self):
        # 为每个链接创建单独的文件夹
        parsed_url = urlparse(self.url)
        path_parts = parsed_url.path.strip('/').split('/')
        # 使用帖子ID或路径作为文件夹名
        folder_name = path_parts[-1] if path_parts else f"tieba_{int(time.time())}"
        self.download_dir = get_data_path('data', folder_name)
        os.makedirs(self.download_dir, exist_ok=True)

        # 创建图片子文件夹
        self.images_dir = os.path.join(self.download_dir, "images")
        os.makedirs(self.images_dir, exist_ok=True)

        # 记录已下载的图片MD5，避免重复下载
        self.downloaded_images = set()
        # 存储所有爬取的数据
        self.crawl_data = []

        # 初始化cookie
        get_cookie()

    def get_page_content(self, page_num: int) -> Optional[str]:
        """使用requests获取页面内容"""
        try:
            # 构建分页URL
            parsed_url = urlparse(self.url)
            query_params = parse_qs(parsed_url.query)
            query_params["pn"] = [str(page_num)]
            query_string = "&" + "&".join([f"{k}={v[0]}" for k, v in query_params.items()])
            page_url = f"{parsed_url.scheme}://{parsed_url.netloc}{parsed_url.path}?{query_string[1:]}"

            # 生成随机user-agent
            generate_random_user_agent()
            
            # 请求页面
            response = requests.get(page_url, headers=TIEBA_HEADERS, timeout=10)
            response.encoding = 'utf-8'
            print(f"请求URL: {page_url}")
            print(f"响应状态码: {response.status_code}")
            page_content = response.text
            if response.status_code == 200:
                print(f"页面内容长度: {len(page_content)} 字符")
                # 检测是否为404页面
                if 'page404' in page_content or 'TB404' in page_content:
                    print(f"页面 {page_num} 是404错误页面，跳过")
                    return None
                # 保存第一页内容到文件查看
                if page_num == 1:
                    with open('page_content.html', 'w', encoding='utf-8') as f:
                        f.write(page_content)
                    print("页面内容已保存到page_content.html")
            return page_content
        except Exception as e:
            print(f"获取第{page_num}页内容失败: {e}")
            return None

    def extract_post_data(self, html_content: str) -> List[Dict[str, Any]]:
        """从页面内容提取帖子数据"""
        try:
            posts_data = []
            soup = BeautifulSoup(html_content, 'html.parser')
            
            # 更新选择器以匹配当前页面结构
            posts = soup.find_all(class_="l_post l_post_bright j_l_post clearfix")
            
            print(f"找到 {len(posts)} 个帖子元素")
            
            for post in posts:
                try:
                    # 提取帖子数据
                    post_data = post.get("data-field")
                    if not post_data:
                        continue
                    
                    try:
                        post_data = json.loads(post_data)
                    except json.JSONDecodeError as e:
                        print(f"JSON解析失败: {e}")
                        continue
                    
                    # 提取用户信息
                    author_info = post_data.get("author", {})
                    user_id = author_info.get("user_id", "")
                    user_name = author_info.get("user_name", "") or author_info.get("user_nickname", "")
                    portrait = author_info.get("portrait", "")
                    
                    # 获取用户URL
                    user_url = post.find('a', class_='p_author_name j_user_card')
                    user_url = user_url.get('href', '') if user_url else ""
                    if user_url and not user_url.startswith('http'):
                        user_url = f"https://tieba.baidu.com{user_url}"
                    
                    # 提取内容信息
                    content_info = post_data.get("content", {})
                    post_id = content_info.get("post_id", "")
                    thread_id = content_info.get("thread_id", "")
                    post_content = content_info.get("content", "")
                    comment_num = content_info.get("comment_num", 0)
                    
                    # 提取时间信息
                    post_time = post.find(class_="p_postTime")
                    if not post_time:
                        post_time = post.find("span", class_="tail-info")
                    time_text = post_time.text.strip() if post_time else ""
                    
                    # 提取楼层信息
                    floor_info = post.find(class_="tail-info")
                    floor_info = floor_info.text.strip() if floor_info else ""
                    
                    # 提取图片URL
                    images = []
                    content_soup = BeautifulSoup(post_content, 'html.parser')
                    img_elements = content_soup.find_all(class_="BDE_Image")
                    for img_element in img_elements:
                        img_url = img_element.get("src")
                        if img_url:
                            images.append(img_url)
                            print(f"找到图片: {img_url}")
                    
                    # 构建帖子信息，保持与原结构兼容
                    post_data = {
                        "username": user_name,
                        "user_url": user_url,
                        "content": post_content,
                        "time": time_text,
                        "images": images,
                        # 新增字段
                        "user_id": user_id,
                        "portrait": portrait,
                        "post_id": post_id,
                        "thread_id": thread_id,
                        "comment_num": comment_num,
                        "floor_info": floor_info
                    }
                    posts_data.append(post_data)
                except Exception as e:
                    print(f"提取单个帖子数据失败: {e}")
                    continue
            
            print(f"提取到 {len(posts_data)} 条帖子信息")
            return posts_data
        except Exception as e:
            print(f"提取帖子数据失败: {e}")
            return []

    def download_image(self, url: str):
        """下载单张图片"""
        for retry in range(self.max_retries):
            try:
                # 生成随机user-agent
                generate_random_user_agent()
                
                # 下载图片
                response = requests.get(url, headers=DOWN_HEADERS, timeout=10)
                response.raise_for_status()
                
                # 计算图片MD5，避免重复下载
                image_content = response.content
                md5_hash = hashlib.md5(image_content).hexdigest()
                
                if md5_hash in self.downloaded_images:
                    print(f"图片已存在，跳过: {url}")
                    return
                
                # 获取图片名称
                image_name = get_image_name(url, response)
                image_path = os.path.join(self.images_dir, image_name)
                
                # 保存图片
                with open(image_path, 'wb') as f:
                    f.write(image_content)
                
                # 记录已下载图片
                self.downloaded_images.add(md5_hash)
                print(f"图片下载成功: {image_name}")
                
                return
            except Exception as e:
                print(f"下载图片失败({retry + 1}/{self.max_retries}): {url}, 错误: {e}")
                # 重试前延迟
                time.sleep(random.uniform(1.0, 3.0))
        
        print(f"图片下载失败，已达最大重试次数: {url}")

    def download_images(self):
        """下载所有图片和帖子信息"""
        print(f"开始爬取帖子: {self.url}")
        
        page_num = 1
        all_images = []
        
        while page_num <= self.max_pages:
            print(f"正在爬取第{page_num}页...")
            
            # 生成随机user-agent
            generate_random_user_agent()
            
            # 获取页面内容
            content = self.get_page_content(page_num)
            if not content:
                page_num += 1
                random_sleep()
                continue
            
            # 提取帖子数据
            post_data = self.extract_post_data(content)
            self.crawl_data.extend(post_data)
            
            # 收集所有图片URL
            for post in post_data:
                all_images.extend(post['images'])
            
            page_num += 1
            # 随机延迟
            random_sleep()
        
        print(f"共找到 {len(all_images)} 张图片")
        
        # 下载图片
        if all_images:
            for url in all_images:
                self.download_image(url)
                # 随机延迟
                time.sleep(random.uniform(0.1, 0.5))
        
        print("图片下载完成")
        
        # 保存数据
        self.save_data()

    def save_data(self):
        """保存爬取的数据为json、csv和sqlite数据库"""
        if not self.crawl_data:
            print("没有爬取到数据，无法保存")
            return
        
        # 保存为json格式
        json_file = os.path.join(self.download_dir, "data.json")
        with open(json_file, "w", encoding="utf-8") as f:
            json.dump(self.crawl_data, f, ensure_ascii=False, indent=2)
        print(f"数据已保存为json文件: {json_file}")
        
        # 保存为csv格式
        # 先将嵌套的images字段转换为字符串
        csv_data = []
        for item in self.crawl_data:
            csv_item = item.copy()
            csv_item["images"] = ",".join(csv_item["images"])
            csv_data.append(csv_item)
        
        df = pd.DataFrame(csv_data)
        csv_file = os.path.join(self.download_dir, "data.csv")
        df.to_csv(csv_file, index=False, encoding="utf-8-sig")
        print(f"数据已保存为csv文件: {csv_file}")
        
        # 保存到sqlite数据库
        db_file = os.path.join(self.download_dir, "data.db")
        conn = sqlite3.connect(db_file)
        cursor = conn.cursor()
        
        # 创建表
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS tieba_posts (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT,
                user_url TEXT,
                content TEXT,
                time TEXT,
                images TEXT
            )
        ''')
        
        # 插入数据
        for item in csv_data:
            cursor.execute('''
                INSERT INTO tieba_posts (username, user_url, content, time, images)
                VALUES (?, ?, ?, ?, ?)
            ''', (item["username"], item["user_url"], item["content"], item["time"], item["images"]))
        
        conn.commit()
        conn.close()
        print(f"数据已保存到sqlite数据库: {db_file}")


def tieba_crawl_all(url: str, max_pages: int = 20):
    """
    获取帖子中的所有回复、图片等信息
    url:帖子链接
    max_pages:最大爬取页数
    """
    # 初始化下载器
    downloader = TiebaImageDownloader(url, max_pages=max_pages)
    
    # 爬取图片和帖子信息
    downloader.download_images()
    
    print(f"共获取到 {len(downloader.crawl_data)} 条帖子信息")
    
    return downloader.crawl_data


if __name__ == '__main__':
    # 测试
    url = "https://tieba.baidu.com/p/10266068882"
    tieba_crawl_all(url, max_pages=10)
