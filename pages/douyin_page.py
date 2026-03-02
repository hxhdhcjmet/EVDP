import streamlit as st
import asyncio
import os
import time
import random
from core.spider.douyin.douyin_comment import CommentFetcher
from core.spider.douyin.douyin_comment_writer import CommentWriter
from core.spider.douyin.douyin_comment_analyser import CommentVisualizer
from core.spider.douyin.douyin_login import login_and_save_cookies
from core.spider.douyin.verify_cookie import verify_cookie
def render_douyin_page():
    st.title("🎵 抖音评论全自动采集与分析")
    st.set_page_config(
        page_title = "抖音评论采集与分析",
        page_icon= "icon/douyin.jpg",
        layout = "wide"     
    )

    # ------ 侧边栏 ------
    # Cookie 管理
    with st.sidebar:
        st.header("🔑 账户配置")
        
        # 检查 Cookie 文件是否存在
        # 假设 cookie 存储在 core/spider/douyin/cookies/cookie.json
        # 使用相对路径查找
        base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        cookie_path = os.path.join(base_dir, "core", "spider", "douyin", "cookies", "cookie.json")
        if os.path.exists(cookie_path):
            # st.caption(f"Cookie路径: {cookie_path}")
            # 优化登录验证 (使用 session_state 避免重复验证)
            if "douyin_login_status" not in st.session_state:
                with st.spinner("正在验证登录状态..."):
                    is_logged, username, path = verify_cookie()
                    st.session_state.douyin_login_status = is_logged
                    st.session_state.douyin_username = username
                    st.session_state.douyin_avatar_path = path
            
            is_logged = st.session_state.douyin_login_status
            username = st.session_state.douyin_username
            avatar_path = st.session_state.douyin_avatar_path

            if is_logged:
                st.success("登陆有效!")
                st.text(f"用户名:{username}")
                st.image(avatar_path, width=150)
            else:
                st.error("登陆失效，请重新登陆!")
                st.image(avatar_path, width=150)
            
            if st.button("重新登陆 (覆盖Cookie)"):
                try:
                    with st.spinner("正在启动浏览器进行扫码登陆..."):
                        login_and_save_cookies()
                    # 清除状态以重新验证
                    if "douyin_login_status" in st.session_state:
                        del st.session_state.douyin_login_status
                    st.success("登陆成功！")
                    st.rerun()
                except Exception as e:
                    st.error(f"登陆失败: {str(e)}")
        else:
            st.warning("未检测到 Cookie，请先登陆")
            if st.button("扫码登陆"):
                try:
                    with st.spinner("正在启动浏览器进行扫码登陆..."):
                        login_and_save_cookies()
                    # 清除状态以重新验证
                    if "douyin_login_status" in st.session_state:
                        del st.session_state.douyin_login_status
                    st.success("登陆成功！")
                    st.rerun()
                except Exception as e:
                    st.error(f"登陆失败: {str(e)}")

    # ------ 主界面 ------ 任务输入
    st.subheader("采集任务")
    url_input = st.text_area("输入视频链接(多个链接请换行)", placeholder="https://www.douyin.com/video/...\nhttps://v.douyin.com/...")

    col1, col2 = st.columns([1, 4])
    with col1:
        # 默认限制
        max_limit = st.number_input("最大爬取数", 10, 100000, 100)
    
    with col2:
        sort_type = st.selectbox("排序方式", [0, 1], format_func=lambda x: "默认排序" if x == 0 else "最新排序")

    if st.button("开始批量执行"):
        urls = [u.strip() for u in url_input.split('\n') if u.strip()]
        if not urls:
            st.error("请输入有效的链接!")
            return

        for idx, url in enumerate(urls):
            time.sleep(random.uniform(1,3))
            st.divider()
            st.markdown(f"#### 正在处理 {idx+1} / {len(urls)} 个视频")
            st.caption(f"URL: {url}")

            # 准备爬取
            try:
                fetcher = CommentFetcher(url, sort_type=sort_type)
                
                # 自定义文件名 (douyin_ + 时间戳 + index)
                # CommentWriter 内部会创建 douyin_timestamp 格式，这里我们传递一个标识
                # 为了避免文件名重复，我们手动生成一个文件名
                import datetime
                timestamp = datetime.datetime.now().strftime(r'%Y%m%d%H%M%S')
                fname = f"douyin_{timestamp}_{idx}"
                
                writer = CommentWriter(fname)
                
                # 创建 UI 进度组件
                p_bar = st.progress(0, text="准备爬取...")
                status_text = st.empty()
                
                # 异步爬取逻辑
                async def run_crawling():
                    await writer.open()
                    count = 0
                    
                    async for comment in fetcher.fetch_generator(max_limit):
                        await writer.write(comment)
                        count += 1
                        progress = min(count / max_limit, 1.0)
                        p_bar.progress(progress, text=f"已抓取 {count} 条评论...")
                    
                    await writer.close()
                    return count

                # 执行爬取
                total_crawled = asyncio.run(run_crawling())
                
                p_bar.progress(1.0, text= f"采集完成！共抓取 {total_crawled} 条。正在启动分析...")
                
                # ------ 链式分析 ------
                st.info("正在生成分析报告...")
                
                # 确保文件存在
                if not os.path.exists(writer.filepath):
                    st.error(f"找不到数据文件: {writer.filepath}")
                    continue
                    
                visualizer = CommentVisualizer(writer.filepath)
                
                # 获取数据文件夹路径，用于保存图片
                data_dir = os.path.dirname(writer.filepath)
                
                # 展示统计结果 (CommentVisualizer 没有 analyze_basic 方法，需要手动计算或从 visualizer.df 获取)
                total_comments = len(visualizer.df)
                avg_digg = visualizer.df['digg_count'].mean() if not visualizer.df.empty else 0
                
                c1, c2 = st.columns(2)
                c1.metric("总评论数", total_comments)
                c2.metric("平均点赞", f"{avg_digg:.1f}")
                
                # 展示图表并保存
                t1, t2, t3, t4 = st.tabs(["词云图", "评论时间密度", "用户分布", "情感分析"])
                
                with t1:
                    fig_wc = visualizer.plot_wordcloud()
                    st.pyplot(fig_wc)
                    # 保存图片
                    wc_path = os.path.join(data_dir, "wordcloud.png")
                    fig_wc.savefig(wc_path)
                    st.caption(f"图片已保存至: {wc_path}")

                with t2:
                    fig_time = visualizer.plot_time_density()
                    st.pyplot(fig_time)
                    time_path = os.path.join(data_dir, "time_density.png")
                    fig_time.savefig(time_path)
                    st.caption(f"图片已保存至: {time_path}")
                
                with t3:
                    fig_ip = visualizer.plot_ip_distribution()
                    st.pyplot(fig_ip)
                    ip_path = os.path.join(data_dir, "ip_distribution.png")
                    fig_ip.savefig(ip_path)
                    st.caption(f"图片已保存至: {ip_path}")
                
                with t4:
                    fig_sent = visualizer.plot_sentiment_analysis()
                    st.pyplot(fig_sent)
                    sent_path = os.path.join(data_dir, "sentiment_analysis.png")
                    fig_sent.savefig(sent_path)
                    st.caption(f"图片已保存至: {sent_path}")

            except Exception as e:
                st.error(f"处理视频 {url} 时发生错误: {str(e)}")
                import traceback
                st.code(traceback.format_exc())

if __name__ == "__main__":
    render_douyin_page()
