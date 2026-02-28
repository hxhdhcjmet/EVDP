# 程序主入口
import asyncio
from auth import AuthManager
from scraper import TiebaAsyncScraper

async def main():
    auth = AuthManager()
    if not auth.load_cookie_from_file():
        auth.update_cookie(input("请粘贴Cookie: "))
    
    if not await auth.validate_login():
        print("登录失效"); auth.update_cookie(input("请粘贴新Cookie: "))
        if not await auth.validate_login(): return

    url = input("\n帖子链接: ").strip()
    max_p = input("爬取页数 (直接回车全部): ").strip()
    do_txt = input("是否爬取文字? (y/n, 默认y): ").lower() != 'n'
    do_img = input("是否下载图片? (y/n, 默认y): ").lower() != 'n'
    
    scraper = TiebaAsyncScraper(url, auth.cookie, max_pages=int(max_p) if max_p else 999)
    await scraper.run(fetch_text=do_txt, fetch_img=do_img)
    print("\n任务完成")

if __name__ == "__main__":
    asyncio.run(main())