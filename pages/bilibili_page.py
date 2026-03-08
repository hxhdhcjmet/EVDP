import streamlit as st
import asyncio
import os
import traceback
from core.spider.bilibili.bilibili_comment import Video_Comment_Extractor
from core.spider.bilibili.CommentWriter import CommentWriter
from core.spider.bilibili.CommentAnalyser import CommentAnalyser


def render_bilibili_page():
    st.title("📺 Bilibili 评论全自动采集与分析")
    st.set_page_config(
        page_title = "Bilibili 评论采集与分析",
        page_icon="icon/bilibili.webp",
        layout = "wide"    
    )

    #------ 侧边栏 ------
    # Cookie 管理
    with st.sidebar:
        st.header("🔑 账户配置")

        # 实例化临时Extractor 用来检查Cookie
        # 传入TEST_LINK仅为初始化,不代表最终爬取目标
        temp_extractor = Video_Comment_Extractor("https://www.bilibili.com/video/BV1qt411j7fV")
        temp_extractor.get_cookies()

        # 优化登录状态验证 (使用 session_state 避免重复请求)
        if "bilibili_login_status" not in st.session_state:
            with st.spinner("正在验证登录状态..."):
                st.session_state.bilibili_login_status = temp_extractor.check_login_status()
                st.session_state.bilibili_uname = temp_extractor.uname

        if st.session_state.bilibili_login_status:
            st.success(f"已登陆:{st.session_state.bilibili_uname}")
            if st.button("更新Cookie"):
                st.session_state.show_cookie_input = True
            
        else:
            st.warning("当前为匿名模式(无法抓取IP属地)")
            st.session_state.show_cookie_input = True

        if st.session_state.get('show_cookie_input'):
            new_cookie = st.text_area("粘贴新的 Cookie 字符串:", help="从浏览器控制台获取的 raw string")
            if st.button("保存并验证"):
                if new_cookie:
                    temp_extractor.save_cookie_to_file(new_cookie)
                    # 清除状态以重新验证
                    if "bilibili_login_status" in st.session_state:
                        del st.session_state.bilibili_login_status
                    st.session_state.show_cookie_input = False
                    st.rerun() # 重新加载页面以触发 get_cookies
                else:
                    st.error("请输入内容")

        # ------主界面------任务输入
    st.subheader("采集任务")
    url_input = st.text_area("输入视频链接(多个链接请换行)",placeholder="https://www.bilibili.com/video/BV1xxxx\nhttps://www.bilibili.com/video/BV2xxxx")

    col1,col2,col3 = st.columns([1,2,3])
    with col1:
        max_concurrency = st.number_input("并发数",1,10,5)

    with col2:
        crawl_limit_option = st.selectbox("主评阈值", ["max", "200", "500", "自定义"])

    with col3:
        order_type = st.selectbox("排序方式",["time","hot"],help = "建议选择 time 爬取更安全")

    custom_limit = None
    if crawl_limit_option == "自定义":
        custom_limit = st.number_input("自定义主评阈值", min_value=1, value=200, step=1)

    if crawl_limit_option == "max":
        max_main_comments = None
    elif crawl_limit_option == "200":
        max_main_comments = 200
    elif crawl_limit_option == "500":
        max_main_comments = 500
    else:
        max_main_comments = int(custom_limit) if custom_limit else 200

    if st.button("开始批量执行"):
        urls = [u.strip() for u in url_input.split('\n') if u.strip()]
        if not urls:
            st.error("请输入有效的链接!")
            return 
                
        for idx,url in enumerate(urls):
            st.divider()
            st.markdown(f"#### 正在处理 {idx+1} / {len(urls)} 个视频")
            st.caption(f"URL: {url}")


                    # 准备爬取
            writer = None
            try:
                extractor = Video_Comment_Extractor(url)

                from core.spider.utils import default_filename
                        # 自定义文件名(BV号+时间戳)
                fname  = f"bili_{extractor.extract_bv_id() or 'video'}_{idx}"
                writer = CommentWriter(fname)

                        # 创建UI进度组件
                p_bar = st.progress(0,text = "准备爬取...")
                status_text = st.empty()

                        # 定义进度回调函数
                def update_ui(ratio,msg):
                    p_bar.progress(min(ratio,1.0),text = msg)



                        # 异步爬取
                asyncio.run(extractor.crawl_all_comments_async(
                                writer = writer,
                                order = order_type,
                                callback=update_ui,
                                max_concurrency=max_concurrency,
                                max_main_comments=max_main_comments
                        ))
                            
                p_bar.progress(1.0,text = "✅ 采集完成！正在启动分析...")
                writer.close()


                        # 链式分析
                st.info("📊 正在生成分析报告...")
                analyzer = CommentAnalyser(writer.filepath)
                analyzer.load()
                analyzer.preprocess()
                analyzer.load_stopwords()
                data_dir = os.path.dirname(writer.filepath)


                        # 展示统计结果
                stats = analyzer.analyze_basic()
                c1,c2,c3 = st.columns(3)
                c1.metric("主评论总数", stats['total_comments'])
                c2.metric("平均点赞", f"{stats['avg_like']:.1f}")
                c3.metric("平均回复", f"{stats['avg_reply']:.1f}")


                        # 展示图表
                t1,t2,t3 = st.tabs(["词云图","评论时间密度","用户分布"])
                with t1:
                    fig_wc = analyzer.plot_wordcloud(return_fig = True)
                    if fig_wc is not None:
                        st.pyplot(fig_wc)
                        wc_path = os.path.join(data_dir, "wordcloud.png")
                        fig_wc.savefig(wc_path)
                        st.caption(f"图片已保存至: {wc_path}")
                    else:
                        st.warning("词云图生成失败")

                with t2:
                    fig_time = analyzer.plot_time_density(return_fig = True)
                    if fig_time is not None:
                        st.pyplot(fig_time)
                        time_path = os.path.join(data_dir, "time_density.png")
                        fig_time.savefig(time_path)
                        st.caption(f"图片已保存至: {time_path}")
                    else:
                        st.warning("评论时间密度图生成失败")

                            # 展示部分关键词
                    st.write("Top 关键词:",analyzer.get_keywords(5))
                with t3:
                    fig_ip = analyzer.plot_ip_distribution(deduplicate = True,return_fig = True)
                    if fig_ip is not None:
                        st.pyplot(fig_ip)
                        ip_path = os.path.join(data_dir, "ip_distribution.png")
                        fig_ip.savefig(ip_path)
                        st.caption(f"图片已保存至: {ip_path}")
                    else:
                        st.warning("IP分布图生成失败")

                    fig_lv = analyzer.plot_user_level(return_fig = True)
                    if fig_lv is not None:
                        st.pyplot(fig_lv)
                        lv_path = os.path.join(data_dir, "user_level.png")
                        fig_lv.savefig(lv_path)
                        st.caption(f"图片已保存至: {lv_path}")
                    else:
                        st.warning("用户等级图生成失败")

            except Exception as e:
                st.error(f"处理视频{url}时发生错误: {str(e)}")
                st.code(traceback.format_exc())
            finally:
                if writer:
                    writer.close()


if __name__ == "__main__":
    # 调用渲染
    render_bilibili_page()
