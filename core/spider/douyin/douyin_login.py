# 基于playwright扫码登陆,保存cookie
# 基于playwright扫码登陆,保存cookie
import json
import io
import os
import qrcode
from playwright.sync_api import sync_playwright
from PIL import Image
from pyzbar.pyzbar import decode
from .utils import Garbage,CookieManager


# 路径配置
CURR_FILE = os.path.abspath(__file__)
CURR_FILE_NAME = os.path.dirname(CURR_FILE)
COOKIE_DIR = os.path.join(CURR_FILE_NAME, "cookies")
os.makedirs(COOKIE_DIR, exist_ok=True)
COOKIE_FILE = os.path.join(COOKIE_DIR, "cookie.json")
TEST_FOR_PASTED = os.path.join(COOKIE_DIR,"test_cookie.json")

def login_and_save_cookies():
    with sync_playwright() as p:
        # ================= 第一阶段：无头模式获取二维码 =================
        print("正在启动，准备提取登录二维码...")
        
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
        garbage = Garbage(CURR_FILE_NAME)
        garbage.clear_now()# 清理上一轮的截图信息

        try:
            # 1. 访问首页
            page.goto("https://www.douyin.com/", wait_until="domcontentloaded", timeout=40000)
            print("等待登录弹窗加载...")
            page.wait_for_timeout(6000) # 等待弹窗动画

            # 2. 提取二维码
            # 注意：坐标裁剪如果出现偏差，可尝试改为 full_page=True 后再用 CV 识别
            try:
                screenshot_bytes = page.screenshot(clip={"x": 440, "y": 200, "width": 400, "height": 400})
                image = Image.open(io.BytesIO(screenshot_bytes))
                decoded_objects = decode(image)
            except Exception:
                decoded_objects = []

            # 如果中心区域没切到，尝试全屏截图兜底
            if not decoded_objects:
                print("中心区域解析失败，尝试全屏解析...")
                full_bytes = page.screenshot()
                decoded_objects = decode(Image.open(io.BytesIO(full_bytes)))

            if not decoded_objects:
                print("未找到二维码，请检查页面加载情况或坐标范围 (debug_view.png)。")
                garbage.save_screenshot(page,"debug_view")
                return

            # 3. 打印二维码
            qr_data = decoded_objects[0].data.decode('utf-8')
            qr = qrcode.QRCode()
            qr.add_data(qr_data)
            qr.make(fit=True)
            print("\n" + "="*45)
            qr.print_ascii(invert=True)
            print("="*45)
            print("\n请使用【抖音 APP】扫码登录")
            print("脚本将监控状态：若直接登录则自动保存；若遇二次验证则唤起浏览器。")

            # 4. 循环监控：区分“登录成功”与“需要验证”
            login_success = False
            needs_manual = False
            
            # 监控 180 秒，给足够的时间掏手机
            for i in range(90): 
                # A. 检查 Cookie (成功标志)
                cookies = context.cookies()
                if any(c['name'] == 'sessionid' for c in cookies):
                    print("\n检测到 sessionid，扫码登录成功！")
                    login_success = True
                    break
                
                # B. 检查是否出现阻断/二次验证 (干预标志)
                # 使用 is_visible() 确保元素是用户可见的，而不是仅仅存在于 HTML 源码中
                # 抖音典型的二次验证标题是 "安全验证" 或者输入框
                is_security_check = False
                
                if page.get_by_text("安全验证").is_visible():
                    print("\n检测到【安全验证】弹窗！")
                    is_security_check = True
                elif page.get_by_placeholder("请输入验证码").is_visible():
                    print("\n检测到【短信验证码】输入框！")
                    is_security_check = True
                elif page.locator("text=为了你的账号安全，请进行短信验证").is_visible():
                    print("\n检测到【账号安全】提示！")
                    is_security_check = True

                if is_security_check:
                    needs_manual = True
                    print("切换到有头模式进行人工处理...")
                    break
                
                # 每 2 秒检查一次
                print(f"\r等待扫码结果... ({i*2}s)", end="", flush=True)
                page.wait_for_timeout(2000)

            # ================= 第二阶段：处理结果 =================
            
            # 情况 1: 需要切有头模式 (扫码后出了验证码)
            if needs_manual:
                # 保存当前已经产生的部分 Cookie (比如扫码后的临时 token)
                temp_cookies = context.cookies()
                browser.close() # 关闭无头浏览器

                print("\n\n启动可视化浏览器，请手动完成验证...")
                
                # 重新启动有头浏览器
                browser = p.chromium.launch(headless=False, args=['--disable-blink-features=AutomationControlled'])
                context = browser.new_context(
                    user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
                )
                # 继承 Cookie
                context.add_cookies(temp_cookies)
                page = context.new_page()
                page.goto("https://www.douyin.com/")

                print("请在弹出的窗口中手动输入验证码/滑块...")
                
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
                print(f"\n完美登录！Cookies 已保存至: {COOKIE_FILE}")
            else:
                print("\n登录超时或失败。")

        except Exception as e:
            print(f"\n发生异常: {e}")
            # 方便调试，报错时截图
            try:
                garbage.save_screenshot(page,"error_state")
            except:
                pass
        finally:
            try:
                browser.close()
            except:
                pass
            
def pasted_cookie_to_file(row_cookie:str):
    """
    粘贴cookie保存为登陆用cookie
    """
    cookie_manager = CookieManager(row_cookie,TEST_FOR_PASTED)
    cookie_manager.cookie_str_to_full_cookie_list()


if __name__ == "__main__":
    pasted_cookie_to_file("""enter_pc_once=1; UIFID_TEMP=29a1f63ec682dc0a0df227dd163e2b46e3a6390e403335fa4c2c6d1dc0ec5ffa72ed26c9b98bff493e3d28704aca88161d4a0bc5f0fd51a97aa09027b42dded9c9ce4edc5ee01c90efa0906b888b9dcc0d3e993c94a9a6decb7e172bcd51f57a; SEARCH_RESULT_LIST_TYPE=%22single%22; hevc_supported=true; SEARCH_UN_LOGIN_PV_CURR_DAY=%7B%22date%22%3A1769429419599%2C%22count%22%3A1%7D; fpk1=U2FsdGVkX19MEs6hYIiMIIhD1kVnVlep/FN5yHVHVXlWeNsJoRsI3QMu8lZkgmq8oTofztlBqfrFpv4pJrRORw==; fpk2=940676c3a8a8572fffba9e3881d0fb19; passport_csrf_token=a92d60cebb825b6f3669d055a3751dc6; passport_csrf_token_default=a92d60cebb825b6f3669d055a3751dc6; s_v_web_id=verify_mkv4lj2h_CTm4HDOs_3CPs_4lhp_9eik_iY3EoO3LYwmd; bd_ticket_guard_client_web_domain=2; UIFID=4015c499a3bc1f891e3545aff6854b8d6b607a7d41f92affc21a7a75b0f3b1a1932d7c90647e23ead2e0e95db19cb1f71cbb3bfd7c85a1602941df506915c2f261ed3e84a44708f1088b34204fb1a8d324513f986b5954e6c18e1a91b45a5287a9f99f97b28604efa0e8c7a88f6392fa5904629cb827fef9892c8d0ebada2093d9d77860d3b703c52ee20a648f2c5fcbca601d8ea419919c843e9620a95205aa; passport_mfa_token=CjXWFT22rkwB%2F%2B7T9bw2hwYU4ZXEiufn5HR8uyTEK89MbZ0gN7hOWRh9zCD1UHACYjsCbXWjpxpKCjwAAAAAAAAAAAAAUBIywGFfr3EBc%2BDicIJSsGUxPTTmx8jE1Vk2XRvjcz6V8h3F21VSct7BnhNxJErAeyUQpsyJDhj2sdFsIAIiAQPrni%2FF; d_ticket=2b4ef55c12ceee1f391a53af8ba8351262e05; is_dash_user=1; my_rd=2; download_guide=%223%2F20260218%2F1%22; passport_assist_user=Cj1wsNEZGODcyeAqDfZtSxt9qj7hz20YWn8iiAitrx8KOhWOkbimH7BJs9IdnJfiwqZ3p8ZaEi0I4-coI2auGkoKPAAAAAAAAAAAAABQFjsvrOI-qQGzwdW9Uii_uykgZBO7oXxTqFapyHygLFu_3G1XCoW_xg8CUKIfo8VRYRC4-IkOGImv1lQgASIBA6YunLA%3D; n_mh=aF0tKUWUyAcHJlDDx97fS0ZhnnMfusA3XPbgj9kIlNU; sid_guard=d0e99a463cf279a5b883ac3336b65362%7C1771400415%7C5184000%7CSun%2C+19-Apr-2026+07%3A40%3A15+GMT; uid_tt=2153e9b1f3c9e2b6ae10bbec14340bf7; uid_tt_ss=2153e9b1f3c9e2b6ae10bbec14340bf7; sid_tt=d0e99a463cf279a5b883ac3336b65362; sessionid=d0e99a463cf279a5b883ac3336b65362; sessionid_ss=d0e99a463cf279a5b883ac3336b65362; session_tlb_tag=sttt%7C11%7C0OmaRjzyeaW4g6wzNrZTYv_________hUGFknmWVHAT6b7Vgb2rRoiTp92AXeEUgCBOsxYAvt58%3D; is_staff_user=false; sid_ucp_v1=1.0.0-KDFhOThhNTI3MjI1OGE5NjA2MDFjYzdkMGVlYjUwM2E3MzkzMDIyZTUKHwjvlM-E-gIQ39nVzAYY7zEgDDDXkpHaBTgHQPQHSAQaAmxmIiBkMGU5OWE0NjNjZjI3OWE1Yjg4M2FjMzMzNmI2NTM2Mg; ssid_ucp_v1=1.0.0-KDFhOThhNTI3MjI1OGE5NjA2MDFjYzdkMGVlYjUwM2E3MzkzMDIyZTUKHwjvlM-E-gIQ39nVzAYY7zEgDDDXkpHaBTgHQPQHSAQaAmxmIiBkMGU5OWE0NjNjZjI3OWE1Yjg4M2FjMzMzNmI2NTM2Mg; _bd_ticket_crypt_cookie=2f6c348237eb3fe935f743992af20160; __security_mc_1_s_sdk_sign_data_key_web_protect=401b50b8-4a82-ad70; __security_mc_1_s_sdk_cert_key=93f1b991-4904-b735; __security_mc_1_s_sdk_crypt_sdk=b5207565-4006-b634; __security_server_data_status=1; login_time=1771400415871; publish_badge_show_info=%220%2C0%2C0%2C1771400416316%22; DiscoverFeedExposedAd=%7B%7D; SelfTabRedDotControl=%5B%5D; FRIEND_NUMBER_RED_POINT_INFO=%22MS4wLjABAAAA3yMyyc87_AUkDdt1P2XVgZDApycwjhxEKD3qVboShSI%2F1771516800000%2F1771509322604%2F0%2F0%22; PhoneResumeUidCacheV1=%7B%22101478287983%22%3A%7B%22time%22%3A1771663220606%2C%22noClick%22%3A1%7D%7D; __druidClientInfo=JTdCJTIyY2xpZW50V2lkdGglMjIlM0ExMzY4JTJDJTIyY2xpZW50SGVpZ2h0JTIyJTNBNzcyJTJDJTIyd2lkdGglMjIlM0ExMzY4JTJDJTIyaGVpZ2h0JTIyJTNBNzcyJTJDJTIyZGV2aWNlUGl4ZWxSYXRpbyUyMiUzQTEuMjUlMkMlMjJ1c2VyQWdlbnQlMjIlM0ElMjJNb3ppbGxhJTJGNS4wJTIwKFdpbmRvd3MlMjBOVCUyMDEwLjAlM0IlMjBXaW42NCUzQiUyMHg2NCklMjBBcHBsZVdlYktpdCUyRjUzNy4zNiUyMChLSFRNTCUyQyUyMGxpa2UlMjBHZWNrbyklMjBDaHJvbWUlMkYxNDUuMC4wLjAlMjBTYWZhcmklMkY1MzcuMzYlMjBFZGclMkYxNDUuMC4wLjAlMjIlN0Q=; JXEntranceNegative=1; stream_player_status_params=%22%7B%5C%22is_auto_play%5C%22%3A0%2C%5C%22is_full_screen%5C%22%3A0%2C%5C%22is_full_webscreen%5C%22%3A0%2C%5C%22is_mute%5C%22%3A1%2C%5C%22is_speed%5C%22%3A1%2C%5C%22is_visible%5C%22%3A0%7D%22; volume_info=%7B%22isUserMute%22%3Afalse%2C%22isMute%22%3Atrue%2C%22volume%22%3A0.5%7D; __ac_signature=_02B4Z6wo00f01vm3uFwAAIDBdB8B14uxF4r5l7zAANgB36; FOLLOW_LIVE_POINT_INFO=%22MS4wLjABAAAA3yMyyc87_AUkDdt1P2XVgZDApycwjhxEKD3qVboShSI%2F1771776000000%2F0%2F1771745130106%2F0%22; douyin.com; device_web_cpu_core=12; device_web_memory_size=8; architecture=amd64; strategyABtestKey=%221771853252.509%22; ttwid=1%7Cd2LYDIhqOn_RIA0EBwuX2XnuSqTQOC6yeLgssmfUIvg%7C1771853251%7C2b920d8b28e3646457ec39271a70468aeb59b414bcd31faa5159a77ec8981907; sdk_source_info=7e276470716a68645a606960273f276364697660272927676c715a6d6069756077273f276364697660272927666d776a68605a607d71606b766c6a6b5a7666776c7571273f275e58272927666a6b766a69605a696c6061273f27636469766027292762696a6764695a7364776c6467696076273f275e582729277672715a646971273f2763646976602729277f6b5a666475273f2763646976602729276d6a6e5a6b6a716c273f2763646976602729276c6b6f5a7f6367273f27636469766027292771273f273130323d303736303d34323234272927676c715a75776a716a666a69273f2763646976602778; bit_env=eYrBBzzDtFujgebMIfCvJPYIsTYJ84ynxwQXK-zZp-di1GLwzx7v6lGHOwyRW6vUJRF-yWH7Q0uoJNDh8oCCw_FOqojcrhrZTgbemTNJaWZtmKqRcTGmFM8s1TKRH25YljUDQ-F5e15C2RQ7B0qdMt6IorwhbwKBlHconiRKkRe25YxtRl_mxdQqX3Z3gHckzDXE7NhgNmTneox_Cza8ASO9YHGoIOugqxyYuRtHFUumYos93A_O--nr9cdS-drTndIjH2aH1B2R31Kp2IdtoVNwfxSWS4iVljmrE-bO5WaouC2iGSqbf_8maEDwdvaoZZ7e-5naPjBcEhDHout3hy5kGIHiWre9LKHYsDHa4Rj18e1DArZtQRXzEDJIYX8J4sQyJRSpOEGsMZ7w5JDD_j_v8ZPK5Q7EmzPl9PeJT4wn2VWeCQ45CMebN_mHGLm4YBIYSf3cE2h5Le6iyHzSkpKyeY2o3hhcwoE5dgvuWlrLXkp_doEXcr1M_N6thXmnRlqqc1XBlTD6YGeFKHCHhElNwpMK53-QOzvw_3c67_HH_K7b13HT0Jzd8JcHcVM2; gulu_source_res=eyJwX2luIjoiYmJiYzc3OGQ2NWQyOGFlMzU1ODNmNDVlM2YzMDEwNjVjYTcwNTY2NjUwOGMzYWY2MzBjNmFlYTY4YTJkYTAxYiJ9; passport_auth_mix_state=tkucqpi8imhcdazhc2f6l0ayu8obfhls; IsDouyinActive=true; dy_swidth=674; dy_sheight=698; stream_recommend_feed_params=%22%7B%5C%22cookie_enabled%5C%22%3Atrue%2C%5C%22screen_width%5C%22%3A674%2C%5C%22screen_height%5C%22%3A698%2C%5C%22browser_online%5C%22%3Atrue%2C%5C%22cpu_core_num%5C%22%3A12%2C%5C%22device_memory%5C%22%3A8%2C%5C%22downlink%5C%22%3A9.7%2C%5C%22effective_type%5C%22%3A%5C%224g%5C%22%2C%5C%22round_trip_time%5C%22%3A0%7D%22; FOLLOW_NUMBER_YELLOW_POINT_INFO=%22MS4wLjABAAAA3yMyyc87_AUkDdt1P2XVgZDApycwjhxEKD3qVboShSI%2F1771862400000%2F0%2F1771853291351%2F0%22; bd_ticket_guard_client_data=eyJiZC10aWNrZXQtZ3VhcmQtdmVyc2lvbiI6MiwiYmQtdGlja2V0LWd1YXJkLWl0ZXJhdGlvbi12ZXJzaW9uIjoxLCJiZC10aWNrZXQtZ3VhcmQtcmVlLXB1YmxpYy1rZXkiOiJCUG8zaWdjN2Y4SjZrdGQreXJEL0gySDRERWNnOUJZR01VV0RZd2haQld1QWp4L2lGa2FZR05jWFYwdlhvQjRwN2FEa3d6VG8yMEtjWk5yMytIWStDbk09IiwiYmQtdGlja2V0LWd1YXJkLXdlYi12ZXJzaW9uIjoyfQ%3D%3D; bd_ticket_guard_client_data_v2=eyJyZWVfcHVibGljX2tleSI6IkJQbzNpZ2M3ZjhKNmt0ZCt5ckQvSDJINERFY2c5QllHTVVXRFl3aFpCV3VBangvaUZrYVlHTmNYVjB2WG9CNHA3YURrd3pUbzIwS2NaTnIzK0hZK0NuTT0iLCJ0c19zaWduIjoidHMuMi42ZTg0NjBiOWE4NzJmMWQ4NTFmZWE1M2NjZDcxMWIwZWFkODMwNDk5Zjk2YmRmODkxNTJhZTQwYTVmMWQyNjI4YzRmYmU4N2QyMzE5Y2YwNTMxODYyNGNlZGExNDkxMWNhNDA2ZGVkYmViZWRkYjJlMzBmY2U4ZDRmYTAyNTc1ZCIsInJlcV9jb250ZW50Ijoic2VjX3RzIiwicmVxX3NpZ24iOiJPbWVHV1JoQ2VYaWliNm5LY1ZLSWJPWHBEdjA0NHhYVGVnaDZSSWZ3bnlzPSIsInNlY190cyI6IiM0bzRZTUV6ZHB3OWU1dGVOTzAxOEFHdHdyYmY0amhZMU9WanBrbElhaGo5NEV1NUw0Z3NubE5meUN6cy8ifQ%3D%3D; home_can_add_dy_2_desktop=%221%22; odin_tt=49149f139efbdfbd5c7eb37c456bc1ff2e1f07509ce9fadc4ed60cf9b80d215e0b33324dd83fa433a0ae9107fd1baad8789c520d70827957d2c13398af32ccc6; biz_trace_id=6fce5dbc""")
    # login_and_save_cookies()



