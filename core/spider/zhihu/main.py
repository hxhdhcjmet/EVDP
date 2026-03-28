# 主程序入口
import asyncio
import sys
import traceback
from playwright.async_api import async_playwright
from core.spider.zhihu.zhihu_login import CookieManager
from core.spider.zhihu.zhihu_scraped import ZhihuCrawler
from core.spider.zhihu.zhihu_writer import Writer

async def main():
    print("\n" + "="*40)
    choice = input(" 是否爬取回答正文内容？(y/n): ").strip().lower()
    
    target_url = "https://www.zhihu.com/question/622014984/answer/89542115195"#https://www.zhihu.com/question/622014984/answer/89542115195

    queue = asyncio.Queue()
    writer = Writer("zhihu_scraped_data.jsonl") 

    async with async_playwright() as p:
        login_mgr = CookieManager()
        
        # 1. 验证登录
        browser, context = await login_mgr.check_login_status(p)
        
        if not browser:
            browser, context = await login_mgr.force_login(p)
        
        # 3. 创建页面
        page = await context.new_page()
        # 必须确保在每个新页面都应用伪装
        await login_mgr.apply_stealth_to_page(page)
        
        writer_task = asyncio.create_task(writer.writer(queue))
        crawler = ZhihuCrawler(page, queue, crawl_content=(choice == 'y'))
        
        try:
            await crawler.run(target_url)
        except Exception:
            # 打印详细错误到终端，但不中断 finally 的清理
            traceback.print_exc()
        finally:
            # 结束信号
            await queue.join()
            await queue.put(None)
            await writer_task
            if browser:
                await browser.close()
            print("\n" + "="*40 + "\n[完成] 任务结束。")

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n[用户] 强制停止。")
        sys.exit(0)