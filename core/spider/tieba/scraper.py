# 爬虫爬取
import asyncio
import aiohttp
import random
import re
import json
from bs4 import BeautifulSoup
from tqdm.asyncio import tqdm
try:
    from config import COMMON_HEADERS, USER_AGENTS
    from data_manager import DataManager
except ImportError:
    from core.spider.tieba.config import COMMON_HEADERS, USER_AGENTS
    from core.spider.tieba.data_manager import DataManager

class TiebaAsyncScraper:
    def __init__(self, url: str, cookie: str, max_pages: int = 999):
        match = re.search(r'/p/(\d+)', url)
        self.post_id = match.group(1) if match else None
        self.cookie = cookie
        self.max_pages = max_pages
        self.dm = DataManager(f"tid_{self.post_id}")
        self.semaphore = asyncio.Semaphore(3) # 控制并发风控

    async def fetch_page(self, session: aiohttp.ClientSession, page_num: int):
        url = f"https://tieba.baidu.com/p/{self.post_id}"
        params = {"pn": str(page_num), "ajax": "1"}
        headers = {**COMMON_HEADERS, "User-Agent": USER_AGENTS[0], "Cookie": self.cookie}
        async with self.semaphore:
            try:
                # 随机停顿风控
                await asyncio.sleep(random.uniform(0.6, 1.2))
                async with session.get(url, params=params, headers=headers, timeout=15) as resp:
                    return await resp.text() if resp.status == 200 else None
            except: return None

    async def fetch_sub_comments(self, session: aiohttp.ClientSession, pid: str, page_num: int = 1):
        """异步获取该楼层的所有子回复"""
        url = "https://tieba.baidu.com/p/comment"
        params = {
            "tid": self.post_id,
            "pid": pid,
            "pn": str(page_num),
        }
        headers = {**COMMON_HEADERS, "User-Agent": USER_AGENTS[0], "Cookie": self.cookie}
        async with self.semaphore:
            try:
                async with session.get(url, params=params, headers=headers, timeout=10) as resp:
                    html = await resp.text()
                    soup = BeautifulSoup(html, 'html.parser')
                    sub_replies = []
                    
                    for c in soup.find_all('li', class_='lzl_single_post'):
                        c_body = c.find('span', class_='lzl_content_main')
                        if c_body:
                            sub_replies.append({
                                "user": c.find('a', class_='j_user_card').get_text(strip=True) if c.find('a', class_='j_user_card') else "匿名",
                                "text": c_body.get_text(strip=True),
                                "ip_location": self._extract_ip(c) # 子回复也有 IP 属地
                            })
                    return sub_replies
            except: return []

    def _extract_ip(self, element):
        """从元素中提取 IP 属地"""
        tails = element.find_all('span', class_='post-tail-wrap')
        for t in tails:
            txt = t.get_text(strip=True)
            if "IP属地" in txt:
                return txt.replace("IP属地:", "").strip()
        
        # 有些情况下 IP 属地在 lzl_content_reply 的文本里
        lzl_tails = element.find_all('span', class_='lzl_time')
        for t in lzl_tails:
            parent = t.parent
            if parent and "IP属地" in parent.get_text():
                match = re.search(r'IP属地:(\w+)', parent.get_text())
                if match: return match.group(1)
        return "未知"

    def parse_floor_generator(self, html: str, fetch_img: bool):
        """使用生成器逐条解析，提高内存效率"""
        soup = BeautifulSoup(html, 'html.parser')
        post_list = soup.find_all('div', class_=re.compile(r'l_post'))
        
        for post in post_list:
            try:
                d_field = json.loads(post.get('data-field', '{}'))
                pid = d_field.get('content', {}).get('post_id') or post.get('data-pid')
                content_div = post.find('div', class_='d_post_content')
                if not content_div: continue

                # --- 提取 IP 属地 ---
                ip_location = self._extract_ip(post)

                # 提取子回复 (抓取该楼层的所有子回复)
                sub_replies = []
                # 1. 先抓当前页已有的
                for c in post.find_all('li', class_='lzl_single_post'):
                    c_body = c.find('span', class_='lzl_content_main')
                    if c_body:
                        sub_replies.append({
                            "user": c.find('a', class_='j_user_card').get_text(strip=True) if c.find('a', class_='j_user_card') else "匿名",
                            "text": c_body.get_text(strip=True),
                            "ip_location": self._extract_ip(c)
                        })
                
                img_urls = [img['src'] for img in content_div.find_all('img', class_='BDE_Image')] if fetch_img else []

                # 2. 检查是否有更多子回复
                total_lzl = d_field.get('content', {}).get('comment_num', 0)
                item_to_yield = {
                    "pid": pid,
                    "floor": d_field.get('content', {}).get('post_no'),
                    "author": d_field.get('author', {}).get('user_name'),
                    "ip_location": ip_location,
                    "content": content_div.get_text(strip=True),
                    "sub_replies": sub_replies,
                    "has_more_lzl": total_lzl > len(sub_replies),
                    "total_lzl": total_lzl,
                    "images": img_urls,
                    "time": next((t.get_text(strip=True) for t in post.find_all('span', class_='post-tail-wrap') if re.search(r'\d{4}-\d{2}', t.get_text())), "未知")
                }
                yield item_to_yield
            except: continue

    async def run(self, fetch_text: bool, fetch_img: bool, callback=None):
        async with aiohttp.ClientSession() as session:
            first_html = await self.fetch_page(session, 1)
            if not first_html: 
                if callback: callback(0, "无法访问帖子")
                return print("无法访问")
            
            soup = BeautifulSoup(first_html, 'html.parser')
            spans = soup.select('li.l_reply_num span.red')
            total_pages = int(spans[1].get_text()) if len(spans) >= 2 else 1
            
            real_max = min(total_pages, self.max_pages)
            pbar = tqdm(total=real_max, desc="异步爬取中")
            
            for p in range(1, real_max + 1):
                msg = f"正在爬取第 {p}/{real_max} 页..."
                if callback: callback(p / real_max, msg)
                
                p_html = await self.fetch_page(session, p)
                if p_html:
                    # 迭代生成器，解析一条写一条
                    for item in self.parse_floor_generator(p_html, fetch_img):
                        # 如果该楼层有更多子回复，这里异步补齐
                        if item.get("has_more_lzl") and item.get("pid"):
                            # 简单起见，这里只抓取第1页之后的子回复，如果有很多页，可以循环抓取
                            # 为防止请求过多，这里默认只抓取前几页子回复
                            for sub_p in range(1, (item["total_lzl"] // 10) + 2):
                                if sub_p == 1: continue # 第一页已经有一部分在 item["sub_replies"] 了
                                more_lzl = await self.fetch_sub_comments(session, item["pid"], sub_p)
                                if not more_lzl: break
                                # 合并并去重
                                existing_texts = {r["text"] for r in item["sub_replies"]}
                                for r in more_lzl:
                                    if r["text"] not in existing_texts:
                                        item["sub_replies"].append(r)
                                        existing_texts.add(r["text"])
                                if len(item["sub_replies"]) >= item["total_lzl"]: break
                        
                        if fetch_text: 
                            # 异步写入数据
                            await self.dm.save_post_jsonl(item)
                        
                        if fetch_img and item["images"]:
                            # 异步下载图片
                            await asyncio.gather(*(self.dm.download_image(session, u) for u in item["images"]))
                pbar.update(1)
            pbar.close()
            if callback: callback(1.0, "爬取完成")