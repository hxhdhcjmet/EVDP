import streamlit as st
import asyncio
import os
import re
from core.spider.tieba.auth import AuthManager
from core.spider.tieba.scraper import TiebaAsyncScraper

def render_tieba_page():
    st.title("📌 百度贴吧帖子自动采集")
    st.set_page_config(
        page_title = "百度贴吧帖子采集",
        page_icon = "icon/tieba.webp",
        layout = "wide"
    )

    # ------ 侧边栏：账户配置 ------
    auth = AuthManager()
    has_cookie = auth.load_cookie_from_file()

    with st.sidebar:
        st.header("🔑 账户配置")
        
        # 验证登录状态 (使用 session_state 优化，避免重复验证)
        if has_cookie:
            if "tieba_login_status" not in st.session_state:
                with st.spinner("正在验证登录状态..."):
                    st.session_state.tieba_login_status = asyncio.run(auth.validate_login())
                    st.session_state.tieba_user_info = auth.user_info
            
            is_logged_in = st.session_state.tieba_login_status
            user_info = st.session_state.tieba_user_info

            if is_logged_in:
                st.success(f"已登录: {user_info.get('nickname', '未知用户')}")
                if user_info.get('phone'):
                    st.caption(f"手机号: {user_info['phone']}")
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
                    # 清除缓存的状态以重新验证
                    if "tieba_login_status" in st.session_state:
                        del st.session_state.tieba_login_status
                    st.session_state.show_tieba_cookie_input = False
                    st.rerun()
                else:
                    st.error("请输入 Cookie")

    # ------ 主界面：任务输入 ------
    st.subheader("采集任务")
    url_input = st.text_area("输入帖子链接 (每行一个)", placeholder="https://tieba.baidu.com/p/xxx", height=100)

    col1, col2 = st.columns(2)
    with col1:
        max_pages_option = st.selectbox("最大爬取页数", options=[1, 5, 10, 20, 50, 100, "Max (全部)"], index=2)
        if max_pages_option == "Max (全部)":
            max_pages = 999999 # 代表全部
        else:
            max_pages = max_pages_option
    with col2:
        st.write("") # 占位
        st.write("") # 占位
        fetch_img = st.checkbox("下载图片", value=True)
        fetch_text = st.checkbox("保存帖子回复", value=True)

    if st.button("开始采集"):
        urls = [u.strip() for u in url_input.split('\n') if u.strip()]
        if not urls:
            st.error("请输入有效的帖子链接！")
            return
        
        for idx, url in enumerate(urls):
            st.divider()
            st.markdown(f"#### 正在处理 {idx+1} / {len(urls)}: {url}")
            
            # 提取 post_id 验证链接
            match = re.search(r'/p/(\d+)', url)
            if not match:
                st.error(f"链接格式不正确: {url}")
                continue
            
            post_id = match.group(1)
            
            # 准备爬取
            try:
                # 增加链接间的随机延迟 (风控)
                if idx > 0:
                    wait_time = random.uniform(2, 5)
                    st.caption(f"等待 {wait_time:.1f} 秒以符合风控策略...")
                    import time
                    time.sleep(wait_time)

                scraper = TiebaAsyncScraper(url, auth.cookie, max_pages=max_pages)
                
                # 创建 UI 进度组件
                p_bar = st.progress(0, text="准备开始...")
                
                # 定义进度回调函数
                def update_ui(ratio, msg):
                    p_bar.progress(min(ratio, 1.0), text=msg)

                # 执行异步爬取
                with st.spinner(f"正在爬取 {url} ..."):
                    asyncio.run(scraper.run(
                        fetch_text=fetch_text,
                        fetch_img=fetch_img,
                        callback=update_ui
                    ))
                
                st.success(f"✅ 采集完成！数据已保存至: /home/EVDP/data/tid_{post_id}")
                
            except Exception as e:
                st.error(f"采集过程中发生错误 ({url}): {str(e)}")
        

if __name__ == "__main__":
    render_tieba_page()
