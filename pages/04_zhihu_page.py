import streamlit as st
import asyncio
import os
import re
import random
from playwright.async_api import async_playwright
from core.spider.zhihu.zhihu_login import CookieManager
from core.spider.zhihu.zhihu_scraped import ZhihuCrawler
from core.spider.zhihu.zhihu_writer import Writer

def extract_id_from_url(url):
    """从知乎链接中提取ID作为文件夹名"""
    # 处理回答链接: https://www.zhihu.com/question/622014984/answer/89542115195
    match = re.search(r'answer/(\d+)', url)
    if match:
        return f"zhihu_answer_{match.group(1)}"
    
    # 处理问题链接: https://www.zhihu.com/question/622014984
    match = re.search(r'question/(\d+)', url)
    if match:
        return f"zhihu_question_{match.group(1)}"
    
    # 兜底：使用时间戳或MD5，这里简单处理
    return f"zhihu_task_{int(random.random() * 10000)}"

async def run_crawler_task(urls, crawl_content, status_placeholder, progress_bar, progress_text):
    login_mgr = CookieManager()
    
    async with async_playwright() as p:
        # 1. 验证登录 (这里再次验证以防万一，但主要依赖 session_state)
        status_placeholder.info("正在初始化爬虫环境...")
        browser, context = await login_mgr.check_login_status(p)
        
        if not browser:
            status_placeholder.error("登录状态已失效，请重新登录。")
            st.session_state.zhihu_login_status = False
            return
        
        # 更新最新用户名
        st.session_state.zhihu_username = login_mgr.username
        
        total_urls = len(urls)
        for idx, url in enumerate(urls):
            folder_name = extract_id_from_url(url)
            status_placeholder.info(f"正在抓取 ({idx+1}/{total_urls}): {url}")
            
            queue = asyncio.Queue()
            writer = Writer(folder_name)
            
            # 创建页面并应用伪装
            page = await context.new_page()
            await login_mgr.apply_stealth_to_page(page)
            
            writer_task = asyncio.create_task(writer.writer(queue))
            
            # 使用闭包捕获 progress_text
            def update_ui(count):
                progress_text.text(f"当前链接已抓取: {count} 条评论")

            crawler = ZhihuCrawler(page, queue, crawl_content=crawl_content, progress_callback=update_ui)
            
            try:
                await crawler.run(url)
            except Exception as e:
                st.error(f"抓取链接 {url} 时出错: {e}")
            finally:
                # 结束信号
                await queue.put(None)
                await writer_task
                await page.close()
                progress_bar.progress((idx + 1) / total_urls)
        
        if browser:
            await browser.close()
        status_placeholder.success("✅ 所有任务已完成！")

def render_zhihu_page():
    st.set_page_config(page_title="知乎评论自动采集", page_icon="💡", layout="wide")
    st.title("💡 知乎回答/问题评论自动采集")

    # ------ 侧边栏：账户配置 ------
    login_mgr = CookieManager()
    
    # 页面进入自动检查登录
    if "zhihu_login_status" not in st.session_state:
        st.session_state.zhihu_login_status = None
        st.session_state.zhihu_username = None
        
        # 自动触发一次验证
        async def auto_verify():
            async with async_playwright() as p:
                b, c = await login_mgr.check_login_status(p)
                if b:
                    st.session_state.zhihu_login_status = True
                    st.session_state.zhihu_username = login_mgr.username
                    await b.close()
                else:
                    st.session_state.zhihu_login_status = False
        
        with st.spinner("正在自动验证登录状态..."):
            asyncio.run(auto_verify())
            st.rerun()

    with st.sidebar:
        st.header("🔑 账户配置")
        
        if st.session_state.zhihu_login_status is True:
            st.success(f"已登录: {st.session_state.zhihu_username or '未知用户'}")
            if st.button("退出登录/重新登录"):
                st.session_state.zhihu_login_status = None
                st.rerun()
        else:
            st.warning("未登录或 Cookie 已失效")
            if st.button("扫码/手动登录"):
                with st.spinner("正在开启登录窗口..."):
                    async def manual_login():
                        async with async_playwright() as p:
                            b, c = await login_mgr.force_login(p)
                            if b:
                                st.session_state.zhihu_login_status = True
                                # 强制登录后再次获取一下用户名
                                b2, c2 = await login_mgr.check_login_status(p)
                                st.session_state.zhihu_username = login_mgr.username
                                await b.close()
                                if b2: await b2.close()
                            else:
                                st.session_state.zhihu_login_status = False
                    
                    asyncio.run(manual_login())
                    st.rerun()

    # ------ 主体界面 ------
    if st.session_state.zhihu_login_status is not True:
        st.info("⚠️ 请先在侧边栏完成登录，否则无法开始爬取。")
        return

    st.markdown("""
    ### 📋 采集任务配置
    输入知乎回答或问题的链接，程序将自动循环采集评论并按 ID 创建文件夹保存。
    """)

    urls_input = st.text_area("请输入知乎链接 (每行一个)", height=150, placeholder="https://www.zhihu.com/question/xxxx\nhttps://www.zhihu.com/question/xxxx/answer/xxxx")
    
    col1, col2 = st.columns(2)
    with col1:
        crawl_content = st.checkbox("是否抓取正文内容", value=True)
    with col2:
        st.caption("注：正文将保存为 article_body 类型在 JSONL 文件中")

    if st.button("🚀 开始采集任务", use_container_width=True):
        if st.session_state.zhihu_login_status is not True:
            st.error("请先完成登录！")
            return
            
        urls = [u.strip() for u in urls_input.split('\n') if u.strip()]
        if not urls:
            st.warning("请输入至少一个有效的知乎链接。")
        else:
            status_p = st.empty()
            prog_bar = st.progress(0)
            prog_text = st.empty()
            
            asyncio.run(run_crawler_task(urls, crawl_content, status_p, prog_bar, prog_text))

if __name__ == "__main__":
    render_zhihu_page()
