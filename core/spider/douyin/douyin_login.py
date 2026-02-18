# 基于playwright扫码登陆,保存cookie
# 基于playwright扫码登陆,保存cookie
import json
import io
import os
import time
import qrcode
from playwright.sync_api import sync_playwright
from PIL import Image
from pyzbar.pyzbar import decode


# 路径配置
CURR_FILE = os.path.abspath(__file__)
CURR_FILE_NAME = os.path.dirname(CURR_FILE)
COOKIE_DIR = os.path.join(CURR_FILE_NAME, "cookies")
os.makedirs(COOKIE_DIR, exist_ok=True)
COOKIE_FILE = os.path.join(COOKIE_DIR, "cookie.json")

def login_and_save_cookies():
    with sync_playwright() as p:
        # ================= 第一阶段：无头模式获取二维码 =================
        print("🚀 [阶段一] 正在以无头模式启动，准备提取登录二维码...")
        
        # 启动参数配置
        browser = p.chromium.launch(
            headless=True, 
            args=['--disable-blink-features=AutomationControlled', '--no-sandbox']
        )
        context = browser.new_context(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            viewport={'width': 1280, 'height': 800}
        )
        page = context.new_page()

        try:
            # 1. 访问首页
            page.goto("https://www.douyin.com/", wait_until="domcontentloaded", timeout=40000)
            print("⏳ 等待登录弹窗加载...")
            page.wait_for_timeout(5000) # 等待弹窗动画

            # 2. 提取二维码
            # 注意：坐标裁剪如果出现偏差，可尝试改为 full_page=True 后再用 CV 识别，这里沿用你的坐标
            try:
                screenshot_bytes = page.screenshot(clip={"x": 440, "y": 200, "width": 400, "height": 400})
                image = Image.open(io.BytesIO(screenshot_bytes))
                decoded_objects = decode(image)
            except Exception:
                decoded_objects = []

            # 如果中心区域没切到，尝试全屏截图兜底
            if not decoded_objects:
                print("⚠️ 中心区域解析失败，尝试全屏解析...")
                full_bytes = page.screenshot()
                decoded_objects = decode(Image.open(io.BytesIO(full_bytes)))

            if not decoded_objects:
                print("❌ 未找到二维码，请检查页面加载情况或坐标范围 (debug_view.png)。")
                page.screenshot(path="debug_view.png")
                return

            # 3. 打印二维码
            qr_data = decoded_objects[0].data.decode('utf-8')
            qr = qrcode.QRCode()
            qr.add_data(qr_data)
            qr.make(fit=True)
            print("\n" + "="*45)
            qr.print_ascii(invert=True)
            print("="*45)
            print("\n👉 请使用【抖音 APP】扫码登录")
            print("👉 脚本将监控状态：若直接登录则自动保存；若遇二次验证则唤起浏览器。")

            # 4. 循环监控：区分“登录成功”与“需要验证”
            login_success = False
            needs_manual = False
            
            # 监控 180 秒，给用户足够的时间掏手机
            for i in range(90): 
                # A. 检查 Cookie (成功标志)
                cookies = context.cookies()
                if any(c['name'] == 'sessionid' for c in cookies):
                    print("\n✅ 检测到 sessionid，扫码登录成功！")
                    login_success = True
                    break
                
                # B. 检查是否出现阻断/二次验证 (干预标志)
                # 使用 is_visible() 确保元素是用户可见的，而不是仅仅存在于 HTML 源码中
                # 抖音典型的二次验证标题是 "安全验证" 或者输入框
                is_security_check = False
                
                if page.get_by_text("安全验证").is_visible():
                    print("\n⚠️ 检测到【安全验证】弹窗！")
                    is_security_check = True
                elif page.get_by_placeholder("请输入验证码").is_visible():
                    print("\n⚠️ 检测到【短信验证码】输入框！")
                    is_security_check = True
                elif page.locator("text=为了你的账号安全，请进行短信验证").is_visible():
                    print("\n⚠️ 检测到【账号安全】提示！")
                    is_security_check = True

                if is_security_check:
                    needs_manual = True
                    print("🔄 准备切换到有头模式进行人工处理...")
                    break
                
                # 每 2 秒检查一次
                print(f"\r⏳ 等待扫码结果... ({i*2}s)", end="", flush=True)
                page.wait_for_timeout(2000)

            # ================= 第二阶段：处理结果 =================
            
            # 情况 1: 需要切有头模式 (扫码后出了验证码)
            if needs_manual:
                # 保存当前已经产生的部分 Cookie (比如扫码后的临时 token)
                temp_cookies = context.cookies()
                browser.close() # 关闭无头浏览器

                print("\n\n🚀 [阶段二] 启动可视化浏览器，请手动完成验证...")
                
                # 重新启动有头浏览器
                browser = p.chromium.launch(headless=False, args=['--disable-blink-features=AutomationControlled'])
                context = browser.new_context(
                    user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
                )
                # 继承 Cookie
                context.add_cookies(temp_cookies)
                page = context.new_page()
                page.goto("https://www.douyin.com/")

                print("👉 请在弹出的窗口中手动输入验证码/滑块...")
                
                # 在有头模式下死循环等待，直到成功或超时
                for _ in range(300): # 10 分钟
                    if any(c['name'] == 'sessionid' for c in context.cookies()):
                        login_success = True
                        break
                    page.wait_for_timeout(2000)

            # 保存最终结果
            if login_success:
                final_cookies = context.cookies()
                with open(COOKIE_FILE, "w", encoding="utf-8") as f:
                    json.dump(final_cookies, f, ensure_ascii=False, indent=4)
                print(f"\n🎉 完美登录！Cookies 已保存至: {COOKIE_FILE}")
            else:
                print("\n❌ 登录超时或失败。")

        except Exception as e:
            print(f"\n❌ 发生异常: {e}")
            # 方便调试，报错时截图
            try:
                page.screenshot(path="error_state.png")
            except:
                pass
        finally:
            try:
                browser.close()
            except:
                pass

if __name__ == "__main__":
    login_and_save_cookies()





