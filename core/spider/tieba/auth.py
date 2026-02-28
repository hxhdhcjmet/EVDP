# 权限与用户信息
import json, os, aiohttp, random
try:
    from config import COOKIE_PATH, COMMON_HEADERS, USER_AGENTS
except ImportError:
    from core.spider.tieba.config import COOKIE_PATH, COMMON_HEADERS, USER_AGENTS

class AuthManager:
    def __init__(self):
        self.cookie = ""
        self.user_info = {}

    def load_cookie_from_file(self):
        if os.path.exists(COOKIE_PATH):
            try:
                with open(COOKIE_PATH, 'r', encoding='utf-8') as f:
                    self.cookie = json.load(f).get("cookie", "").strip()
                    return True
            except: pass
        return False

    def update_cookie(self, new_cookie: str):
        self.cookie = new_cookie.strip()
        os.makedirs(os.path.dirname(COOKIE_PATH), exist_ok=True)
        with open(COOKIE_PATH, 'w', encoding='utf-8') as f:
            json.dump({"cookie": self.cookie}, f, ensure_ascii=False, indent=4)

    async def validate_login(self) -> bool:
        if not self.cookie: return False
        headers = {"User-Agent": USER_AGENTS[0], "Cookie": self.cookie}
        async with aiohttp.ClientSession(headers=headers) as session:
            try:
                async with session.get("https://tieba.baidu.com/dc/common/tbs", timeout=10) as resp:
                    if (await resp.json(content_type=None)).get("is_login") == 1:
                        async with session.get("https://tieba.baidu.com/f/user/json_userinfo") as r:
                            d = (await r.json(content_type=None)).get("data", {})
                            self.user_info = {"nickname": d.get("user_name_url"), "phone": d.get("mobilephone")}
                            print(f"登录成功: {self.user_info['nickname']}\n(phone:{self.user_info['phone']})")
                            return True
            except: pass
        return False