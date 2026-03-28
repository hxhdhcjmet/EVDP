# 基础配置
import os

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(BASE_DIR))),"data")
COOKIE_PATH = os.path.join(BASE_DIR, "cookies", "zhihu_cookie.json")

os.makedirs(os.path.dirname(COOKIE_PATH), exist_ok=True)
os.makedirs(DATA_DIR, exist_ok=True)

# 浏览器伪装配置
BROWSER_CONFIG = {
    "user_agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
    "viewport": {"width": 1920, "height": 1080}
}

# 抓取策略控制
HOT_COMMENT_COUNT = 5     # 前几条属于“高赞”
RANDOM_SUB_PROB = 0.3     # 普通评论抓取子评论的概率