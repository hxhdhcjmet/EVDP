import asyncio
import json
import os
import re
import random
from typing import AsyncGenerator
from playwright.async_api import async_playwright
from tqdm.asyncio import tqdm
import time

# 从外部导入写类 (确保 douyin_comment_writer.py 与此文件在同级目录或 Python 路径中)
from douyin_comment_writer import CommentWriter

# 随机UA
USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/109.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/109.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:108.0) Gecko/20100101 Firefox/108.0",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/108.0.0.0 Safari/537.36 Edg/108.0.1462.42",
]

class CommentFetcher:
    def __init__(self, video_url: str, sort_type: int = 0):
        self.video_url = self._clean_url(video_url)
        self.sort_type = sort_type 
        self.queue = asyncio.Queue()
        self.total_on_page = 0

    def _clean_url(self, url: str) -> str:
        """处理不同类型的链接，确保提取出核心 ID 并生成干净的 URL"""
        # 兼容匹配 /video/123456 或 ?modal_id=123456
        match = re.search(r'(?:video/|modal_id=)(\d+)', url)
        if match:
            video_id = match.group(1)
            # 统一转为标准 video 格式，方便后续安全拼接 ?sort_type=
            return f"https://www.douyin.com/video/{video_id}"
        return url

    def _load_cookie(self):
        curr_folder = os.path.dirname(os.path.abspath(__file__))
        cookie_path = os.path.join(curr_folder, 'cookies', 'cookie.json')
        if not os.path.exists(cookie_path):
            return []
        with open(cookie_path, "r", encoding="utf-8") as f:
            return json.load(f)

    async def _get_total_count(self, page) -> int:
        locator_strategies = [
            'span:has-text("评论") >> xpath=following-sibling::*[1]',
            '[class*="comment"][class*="count"]',
            'div[data-e2e="comment-list"] h2 span'
        ]
        text = ""
        for idx, locator_str in enumerate(locator_strategies):
            try:
                locator = page.locator(locator_str).first
                await locator.wait_for(state="attached", timeout=3000)
                text = await locator.inner_text()
                if text.strip(): 
                    break
            except: 
                continue

        if not text: return 0
        numbers = re.findall(r'\d+\.?\d*[wm]?', text.lower())
        if not numbers: return 0
        
        raw_num = numbers[0]
        if 'w' in raw_num: return int(float(raw_num.replace('w', '')) * 10000)
        if 'm' in raw_num: return int(float(raw_num.replace('m', '')) * 1000000)
        return int(float(raw_num))

    async def handle_response(self, response):
        """同时捕获主评论和子评论包"""
        url = response.url
        if "aweme/v1/web/comment/list/" in url:
            try:
                data = await response.json()
                comments = data.get("comments") or []
                for c in comments:
                    await self.queue.put({
                        "cid": c.get("cid"),
                        "text": c.get("text"),
                        "nickname": c.get("user", {}).get("nickname"),
                        "digg_count": c.get("digg_count"),
                        "create_time": c.get("create_time"),
                        "ip_label": c.get("ip_label"),
                        "reply_total": c.get("reply_comment_total", 0),
                        "is_reply": "reply" in url,
                        "reply_id": c.get("reply_id")
                    })
            except: 
                pass

    async def fetch_generator(self, user_limit: int) -> AsyncGenerator[dict, None]:
        async with async_playwright() as pw:
            browser = await pw.chromium.launch(headless=True, args=["--no-sandbox"])
            context = await browser.new_context(
                user_agent=random.choice(USER_AGENTS),
                viewport={'width': 1280, 'height': 800}
            )
            cookies = self._load_cookie()
            if cookies: 
                await context.add_cookies(cookies)
            
            page = await context.new_page()
            page.on("response", self.handle_response)
            
            final_url = f"{self.video_url}?sort_type={self.sort_type}"
            # 必须使用 domcontentloaded，避免因后台持续发包导致 30s 超时
            await page.goto(final_url, wait_until="domcontentloaded")
            
            # 等待评论区初始加载
            await asyncio.sleep(2)
            
            self.total_on_page = await self._get_total_count(page)
            real_limit = min(self.total_on_page, user_limit) if self.total_on_page > 0 else user_limit
            
            count = 0
            consecutive_empty = 0
            
            while count < real_limit:
                # 模拟滚动触发
                await page.mouse.wheel(0, random.randint(1500, 2500))
                await asyncio.sleep(random.uniform(1.0, 2.0))
                
                # 处理回复评论：寻找“展开X条回复”或“展开”并随机点击
                try:
                    expand_btns = await page.get_by_text(re.compile(r"展开.*回复|展开更多")).all()
                    for btn in expand_btns[:3]: 
                        if random.random() > 0.4:
                            await btn.click(timeout=1000)
                            await asyncio.sleep(0.5)
                except: 
                    pass

                found_in_round = 0
                while not self.queue.empty():
                    item = await self.queue.get()
                    yield item
                    count += 1
                    found_in_round += 1
                    if count >= real_limit: 
                        break
                
                # 防止死循环
                if found_in_round == 0:
                    consecutive_empty += 1
                    if consecutive_empty > 20: 
                        break
                else:
                    consecutive_empty = 0

            await browser.close()

async def run_task(url: str, limit: int, folder_name: str, sort_type: int = 0):
    fetcher = CommentFetcher(url, sort_type=sort_type)
    writer = CommentWriter(folder_name)
    await writer.open()
    
    # 初始不设定 total，避免出现 0/0 的进度条
    pbar = tqdm(desc="采集进度", unit="条")
    
    first_data = True
    try:
        async for comment in fetcher.fetch_generator(limit):
            this_start  = time.time()
            if first_data:
                # 在获取到第一条数据时，我们已经知道了页面上的大概总数，此时再设定进度条上限
                actual_goal = min(fetcher.total_on_page, limit) if fetcher.total_on_page > 0 else limit
                pbar.total = actual_goal
                pbar.refresh()
                first_data = False
            
            this_dur = time.time() - this_start
            if this_dur > 60:
                print("用时超时，退出！")
                raise TimeoutError
            await writer.write(comment)
            pbar.update(1)
    except Exception as e:
        print(f"\n[异常中断] {e}")
    finally:
        await writer.close()
        pbar.close()
        print(f"\n[完成] 成功抓取: {pbar.n} 条")

if __name__ == "__main__":
    TARGET_URL = "https://www.douyin.com/video/7584329244173077806" 
    USER_LIMIT = 500
    SORT_BY = 0 
    SAVE_FOLDER = "test" 

    asyncio.run(run_task(TARGET_URL, USER_LIMIT, SAVE_FOLDER, sort_type=SORT_BY))