# 文章、评论爬取模块
import asyncio
import random
import time
from tqdm import tqdm

class ZhihuCrawler:
    def __init__(self, page, queue, crawl_content=False, progress_callback=None):
        self.page = page
        self.queue = queue
        self.crawl_content = crawl_content
        self.main_comment_count = 0
        self.pbar = None
        self.progress_callback = progress_callback

    async def handle_response(self, response):
            """拦截评论 API 接口数据"""
            # 放宽拦截条件，兼容 api/v4/comments, comment_v5 等不同版本的接口
            #if "api" in response.url and "comment" in response.url:
            if "api/v4/comment_v5" in response.url:
                if response.status == 200:
                    try:
                        data = await response.json()
                        items = data.get("data", [])
                        for item in items:
                            self.main_comment_count += 1
                            if self.pbar:
                                self.pbar.update(1)
                            if self.progress_callback:
                                self.progress_callback(self.main_comment_count)
                            author_info = item.get("author", {})
                            ip_label = item.get("location") or author_info.get("ip_label") or "未知IP"
                            vote = item.get("recation_count") or item.get("vote_count") or 0
                            comment_type = "root_comment" if "child_comments" in item else "child_comment"
                            member_info = author_info.get("member", author_info) 
                            
                            # 安全获取时间
                            created_time = item.get("created_time")
                            time_str = time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(created_time)) if created_time else "未知时间"

                            await self.queue.put({
                                "type": "comment",
                                "author": member_info.get("name", "未知用户"),
                                "ip": ip_label, 
                                "content": item.get("content", ""),
                                "vote": vote,
                                "time": time_str
                            })
                    except Exception as e:
                        # 暴露出错原因，确保鲁棒性的同时方便调试
                        print(f"\n[解析警告] URL: {response.url} | 错误: {e}")

    async def run(self, url):
        # 1. 注册监听
        self.page.on("response", self.handle_response)
        # 修复进度条报错：手动指定 total 为 None 并设置 initial
        self.pbar = tqdm(desc="正在抓取评论", unit="条", total=None, initial=0)

        print(f"[系统] 正在访问: {url}")
        # 增加超时和等待状态
        await self.page.goto(url, wait_until="networkidle", timeout=60000)
        
        # 2. 爬取正文
        if self.crawl_content:
            try:
                await self.page.wait_for_selector(".RichText", timeout=5000)
                content = await self.page.locator(".RichContent-inner").first.inner_text()
                await self.queue.put({"type": "article_body", "content": content, "url": url})
                print("\n[系统] 正文提取成功。")
            except:
                print("\n[系统] 正文提取失败。")

        # 3. 【增强版】开启评论区逻辑
        print("[系统] 正在尝试开启评论区...")
        try:
            # 策略 A: 寻找带有数字的评论按钮 (例如 "1,234 条评论")
            # 使用更通用的正则表达式
            comment_selectors = [
                "button:has-text('条评论')",
                ".ContentItem-actions button:has-text('评论')",
                "button.Button--plain.Button--withIcon.Button--withLabel:has-text('评论')"
            ]
            
            clicked = False
            for selector in comment_selectors:
                btn = self.page.locator(selector).first
                if await btn.is_visible():
                    # 关键：先滚动到按钮位置，防止被顶部导航栏遮挡
                    await btn.scroll_into_view_if_needed()
                    await asyncio.sleep(1)
                    await btn.click()
                    clicked = True
                    print(f"[系统] 已点击评论按钮 ({selector})")
                    break
            
            if not clicked:
                # 策略 B: 如果找不到按钮，尝试按快捷键 'c' (知乎部分页面支持)
                await self.page.keyboard.press("c")
                print("[系统] 尝试通过快捷键展开评论...")

            # 等待评论区渲染，缩短等待时间并增加容错
            # try:
            #     await self.page.wait_for_selector(".Comments-container, .CommentListV2", timeout=5000)
            # except:
            #     print("[提示] 未检测到评论容器，将直接通过滚动尝试触发加载。")
            # 在滚动循环前，确保页面焦点在评论区
            try:
                await self.page.locator(".Comments-container").scroll_into_view_if_needed()
            except:
                pass

        except Exception as e:
            print(f"[警告] 开启评论区异常: {e}")

        # 4. 循环滚动触发 API
        print("[系统] 开始模拟滚动加载评论...")
        last_count = -1
        scroll_idle = 0
        
        for i in range(50):
            scroll_step = random.randint(700, 1000)
            await self.page.mouse.wheel(0, scroll_step)
            
            # 动态等待：分小段检测，一旦发现 main_comment_count 增加就提前中断等待
            wait_time = 0
            while wait_time < 3.0:
                await asyncio.sleep(0.5)
                wait_time += 0.5
                if self.main_comment_count > last_count:
                    break # 数据已到达，直接进入下一次滚动
            
            if self.main_comment_count == last_count:
                scroll_idle += 1
            else:
                scroll_idle = 0 
                last_count = self.main_comment_count
            
            if scroll_idle >= 4 and self.main_comment_count > 0: # 缩短无响应退出阈值
                print(f"\n[系统] 累计抓取 {self.main_comment_count} 条，判定为加载完毕。")
                break
                
        if self.pbar is not None:
            self.pbar.close()