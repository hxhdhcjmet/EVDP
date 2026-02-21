# 验证保存的抖音cookie是否有效

import json
import os
from playwright.sync_api import sync_playwright
from utils import Garbage

# 保存cookie的路径
CURR_FILE = os.path.abspath(__file__)
CURR_FILE_NAME = os.path.dirname(CURR_FILE)
COOKIE_FILE = os.path.join(CURR_FILE_NAME, "cookies", "cookie.json")




def verify_cookie()->bool:
    """
    验证抖音cookie是否有效
    """
    if not os.path.exists(COOKIE_FILE):
        print(f"找不到cookie文件:{COOKIE_FILE}!")
        return False
    
    print(f"正在加载Cookie : {COOKIE_FILE}...")
    with open(COOKIE_FILE,"r",encoding = 'utf-8') as f:
        cookies = json.load(f)
    is_logged_in_statically = any(c['name'] == 'sessionid_ss' for c in cookies)
    if not is_logged_in_statically:
        print("警告!未找到'sessionid_ss'字段")
    
    print("浏览器实测...")
    with sync_playwright() as p:
        browser = p.chromium.launch(headless = True)
        context = browser.new_context(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        )

        # 注入cookie
        context.add_cookies(cookies)
        page = context.new_page()

        # 创建garbage类
        garbage = Garbage(CURR_FILE_NAME)
        garbage.clear_now()

        try:
            print("正在访问个人中心...")
            page.goto("https://www.douyin.com/user/self",timeout=15000)
            page.wait_for_timeout(3000)
            # 等待用户名元素加载
            username_locator = page.locator('#user_detail_element > div > div.a3i9GVfe.nZryJ1oM._6lTeZcQP.y5Tqsaqg > div.IGPVd8vQ > div.HjcJQS1Z > h1 > span > span > span > span > span > span')
            username_locator.wait_for(timeout=10000)
            username = username_locator.inner_text()



            print("="*45)
            print("Cookie有效")
            print(f"用户名:{username}")
            print(f"当前URL:{page.url}")
            print("="*45)

            garbage.save_screenshot(page,"login_succes")
            browser.close()
            garbage.clear_garbage(1)
            
            return True
        
        except TimeoutError:
            print("Cookie无效")
            print(f"当前URL:{page.url}")
            
            garbage.save_screenshot(page,"login_fail")
            browser.close()

            return False
        
        except Exception as e:
            print(f"发生错误:{e}")
            garbage.save_screenshot(page,"unknow_fail")
            browser.close()

            return False
        



if __name__ == "__main__":
    verify_cookie()