# 登陆、cookie管理

import json
import os
import asyncio
import re
from playwright_stealth import Stealth
from core.spider.zhihu.config import COOKIE_PATH, BROWSER_CONFIG

class CookieManager:
    def __init__(self):
        self.cookie_path = COOKIE_PATH
        self.username = None

    def load_cookies(self):
        """加载 Cookie,确保返回的是 List"""
        if os.path.exists(self.cookie_path):
            try:
                with open(self.cookie_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    # 自动处理字典或列表格式
                    if isinstance(data, list):
                        return data
                    if isinstance(data, dict):
                        return data.get("cookies", [])
            except Exception as e:
                print(f"读取 Cookie 文件异常: {e}")
        return None

    async def apply_stealth_to_page(self, page):
        """
        正确实例化并应用 Stealth
        """
        # 实例化时不传 page，调用方法时传 page
        stealth_config = Stealth() 
        # 异步环境使用 apply_stealth_async
        await stealth_config.apply_stealth_async(page)

    async def check_login_status(self, playwright):
        """
        第一阶段：静默验证。
        如果 Cookie 有效，直接返回环境。
        """
        cookies = self.load_cookies()
        if not cookies:
            return None, None

        print("正在尝试静默登录验证...")
        browser = await playwright.chromium.launch(headless=True)
        context = await browser.new_context(**BROWSER_CONFIG)
        
        try:
            await context.add_cookies(cookies)
            page = await context.new_page()
            await self.apply_stealth_to_page(page)
            
            # 尝试访问个人首页，这里比通知页更稳定
            await page.goto("https://www.zhihu.com/", wait_until="networkidle", timeout=15000)
            
            # 检查是否存在头像或“发想法”等登录后特有元素
            # 增加了多个选择器兼容，防止知乎改版
            is_login = await page.evaluate('''() => {
                return !!(document.querySelector('.AppHeader-profile') || 
                         document.querySelector('.DraftEditor-root') ||
                         document.querySelector('.AppHeader-user'));
            }''')

            if is_login:
                try:
                    # 尝试通过页面 DOM 提取右上角头像包含的用户名信息
                    username_raw = await page.evaluate('''() => {
                        let avatar = document.querySelector(".AppHeader-profileAvatar");
                        return avatar ? avatar.alt : null;
                    }''')
                    
                    if username_raw:
                        # 清洗用户名: "【点击进入xxx主页】" -> "xxx" 或 "点击进入 xxx 的主页" -> "xxx"
                        # 尝试多种匹配模式
                        match = re.search(r'点击打开\s*(.*?)\s*(?:的主页|主页)', username_raw)
                        if match:
                            self.username = match.group(1).strip(" 【】")
                        else:
                            # 兜底：直接去掉固定前缀后缀
                            self.username = username_raw.replace("点击打开", "").replace("的主页", "").replace("主页", "").strip(" 【】")
                    
                    if self.username:
                        print(f"[系统] 静默验证成功：登录状态有效。欢迎回来，当前账号: 【{self.username}】")
                    else:
                        print("[系统] 静默验证成功：登录状态有效。(未能提取到用户名)")
                except Exception as e:
                    print(f"无法获取用户名:{e}")
                    print("[系统] 静默验证成功：登录状态有效。")
                return browser, context
            else:
                await page.close()
                await browser.close()
                return None, None
        except Exception as e:
            print(f"静默验证过程出错: {e}")
            await browser.close()
            return None, None

    async def force_login(self, playwright):
        """
        交互登录。
        """
        print("准备开启有头模式，请进行扫码或账号登录...")
        browser = await playwright.chromium.launch(headless=False)
        context = await browser.new_context(**BROWSER_CONFIG)
        page = await context.new_page()
        await self.apply_stealth_to_page(page)
        
        await page.goto("https://www.zhihu.com/signin")
        
        # 循环检测登录状态
        max_wait = 120  # 最大等待120秒
        wait_time = 0
        while wait_time < max_wait:
            await asyncio.sleep(2)
            wait_time += 2
            
            # 检测是否跳转离开登录页且出现了用户信息
            current_url = page.url
            if "signin" not in current_url:
                # 再次检测关键元素
                is_login = await page.evaluate('''() => {
                    return !!(document.querySelector('.AppHeader-profile') || 
                             document.querySelector('.AppHeader-user'));
                }''')
                
                if is_login:
                    print("登录成功！正在抓取最新凭证...")
                    await asyncio.sleep(3)  # 给浏览器一点时间刷入所有 Session Cookie
                    
                    new_cookies = await context.cookies()
                    # 保存为标准 JSON 格式
                    with open(self.cookie_path, 'w', encoding='utf-8') as f:
                        json.dump(new_cookies, f, indent=4, ensure_ascii=False)
                    
                    print(f"Cookie 已更新至: {self.cookie_path}")
                    await page.close()
                    return browser, context
            
            if "unhuman" in current_url:
                print("检测到安全验证（验证码），请在浏览器中手动完成。")

        print("登录超时，请重新运行。")
        await browser.close()
        return None, None