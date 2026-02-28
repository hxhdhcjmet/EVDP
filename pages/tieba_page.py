import streamlit as st
import asyncio
import os
import re
from core.spider.tieba.auth import AuthManager
from core.spider.tieba.scraper import TiebaAsyncScraper

def render_tieba_page():
    st.title("📌 百度贴吧帖子全自动采集")

    # ------ 侧边栏：账户配置 ------
    auth = AuthManager()
    has_cookie = auth.load_cookie_from_file()

    with st.sidebar:
        st.header("🔑 账户配置")
        
        # 验证登录状态
        if has_cookie:
            with st.spinner("正在验证登录状态..."):
                is_logged_in = asyncio.run(auth.validate_login())
            
            if is_logged_in:
                st.success(f"已登录: {auth.user_info.get('nickname', '未知用户')}")
                if auth.user_info.get('phone'):
                    st.caption(f"手机号: {auth.user_info['phone']}")
                if st.button("更新 Cookie"):
                    st.session_state.show_tieba_cookie_input = True
            else:
                st.warning("Cookie 已失效或未登录")
                st.session_state.show_tieba_cookie_input = True
        else:
            st.info("未检测到 Cookie 配置")
            st.session_state.show_tieba_cookie_input = True

        if st.session_state.get('show_tieba_cookie_input'):
            new_cookie = st.text_area("粘贴百度贴吧 Cookie:", help="从浏览器控制台获取的 raw Cookie 字符串")
            if st.button("保存并验证"):
                if new_cookie:
                    auth.update_cookie(new_cookie)
                    st.session_state.show_tieba_cookie_input = False
                    st.rerun()
                else:
                    st.error("请输入 Cookie")

    # ------ 主界面：任务输入 ------
    st.subheader("🚀 采集任务")
    url_input = st.text_input("输入帖子链接", placeholder="https://tieba.baidu.com/p/8419121896")

    col1, col2 = st.columns(2)
    with col1:
        max_pages = st.number_input("最大爬取页数", min_value=1, max_value=9999, value=10)
    with col2:
        st.write("") # 占位
        st.write("") # 占位
        fetch_img = st.checkbox("下载图片", value=True)
        fetch_text = st.checkbox("保存帖子回复", value=True)

    if st.button("开始采集"):
        if not url_input:
            st.error("请输入有效的帖子链接！")
            return
        
        # 提取 post_id 验证链接
        match = re.search(r'/p/(\d+)', url_input)
        if not match:
            st.error("链接格式不正确，请确保包含 /p/数字")
            return
        
        post_id = match.group(1)
        
        # 准备爬取
        try:
            scraper = TiebaAsyncScraper(url_input, auth.cookie, max_pages=max_pages)
            
            # 创建 UI 进度组件
            p_bar = st.progress(0, text="准备开始...")
            
            # 定义进度回调函数
            def update_ui(ratio, msg):
                p_bar.progress(min(ratio, 1.0), text=msg)

            # 执行异步爬取
            with st.spinner("正在爬取中..."):
                asyncio.run(scraper.run(
                    fetch_text=fetch_text,
                    fetch_img=fetch_img,
                    callback=update_ui
                ))
            
            st.success(f"✅ 采集完成！数据已保存至: /home/EVDP/data/tid_{post_id}")
            st.balloons()
            
        except Exception as e:
            st.error(f"采集过程中发生错误: {str(e)}")

if __name__ == "__main__":
    render_tieba_page()
