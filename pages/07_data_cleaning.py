"""
数据清洗页面
提供可视化的数据清洗和标准化功能
"""

import streamlit as st
import pandas as pd
from pathlib import Path
import sys
import os
from datetime import datetime

# 添加项目路径
sys.path.insert(0, '/home/EVDP')

from core.analysis import DataCleaner, clean_file

# 页面配置
st.set_page_config(
    page_title="数据清洗与标准化",
    layout="wide",
    page_icon="🧹"
)

# 自定义样式
st.markdown("""
<style>
    .step-header {
        font-size: 1.2em;
        font-weight: bold;
        margin-top: 1em;
        margin-bottom: 0.5em;
        color: #1f77b4;
    }
    .metric-card {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        padding: 15px;
        border-radius: 8px;
        color: white;
        margin: 5px 0;
    }
    .success-box {
        background-color: #d4edda;
        border: 1px solid #c3e6cb;
        border-radius: 5px;
        padding: 10px;
        margin: 10px 0;
    }
</style>
""", unsafe_allow_html=True)


def safe_to_dict(comment):
    """安全转换评论为字典"""
    try:
        data = {
            'comment_id': comment.comment_id,
            'platform': comment.platform,
            'content': comment.content,
            'user_name': comment.user_name,
            'user_id': comment.user_id,
            'user_level': comment.user_level,
            'like_count': comment.like_count,
            'reply_count': comment.reply_count,
            'publish_time': comment.publish_time.isoformat() if comment.publish_time else None,
            'ip_location': comment.ip_location,
            'is_reply': comment.is_reply,
            'parent_id': comment.parent_id,
            'content_metadata': comment.content_metadata,
        }
        return data
    except Exception as e:
        st.error(f"转换错误: {e}")
        return None


def render_data_cleaning_page():
    """渲染数据清洗页面"""
    
    st.title("🧹 数据清洗与标准化")
    st.markdown("将不同平台的评论数据标准化为统一格式，便于后续分析")
    
    # 初始化 session state
    if 'cleaner' not in st.session_state:
        st.session_state.cleaner = DataCleaner()
    if 'cleaned_comments' not in st.session_state:
        st.session_state.cleaned_comments = None
    if 'cleaning_report' not in st.session_state:
        st.session_state.cleaning_report = None
    
    # ========== 步骤 1: 选择数据源 ==========
    st.markdown('<p class="step-header">📍 步骤 1: 选择数据源</p>', unsafe_allow_html=True)
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("**方式 1: 从已有数据选择**")
        
        # 扫描 data 目录
        data_dir = Path('/home/EVDP/data')
        if data_dir.exists():
            jsonl_files = list(data_dir.rglob('*.jsonl'))
            
            if jsonl_files:
                file_options = [str(f) for f in jsonl_files]
                selected_file = st.selectbox(
                    "选择数据文件",
                    file_options,
                    format_func=lambda x: x.split('/data/')[-1] if '/data/' in x else x
                )
                
                # 显示文件信息
                if selected_file:
                    with open(selected_file, 'r', encoding='utf-8') as f:
                        line_count = sum(1 for _ in f)
                    st.info(f"📄 文件包含 {line_count} 行数据")
            else:
                st.warning("未找到数据文件")
                selected_file = None
        else:
            st.warning("data 目录不存在")
            selected_file = None
    
    with col2:
        st.markdown("**方式 2: 上传新文件**")
        uploaded_file = st.file_uploader(
            "选择 JSONL 文件",
            type=['jsonl', 'json'],
            help="支持 B站/贴吧/知乎/抖音格式"
        )
        
        if uploaded_file:
            st.success(f"✓ 已上传: {uploaded_file.name}")
    
    # ========== 步骤 2: 清洗配置 ==========
    st.markdown('<p class="step-header">⚙️ 步骤 2: 清洗配置</p>', unsafe_allow_html=True)
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        remove_html = st.checkbox("去除HTML标签", value=True)
        mark_url = st.checkbox("标记URL链接", value=True)
    
    with col2:
        mark_mention = st.checkbox("标记@提及", value=True)
        normalize_emoji = st.checkbox("标准化表情", value=True)
    
    with col3:
        flatten_replies = st.checkbox("扁平化回复", value=True, help="将嵌套回复展开为独立评论")
        show_raw_data = st.checkbox("保留原始数据", value=True, help="用于调试和溯源")
    
    # ========== 执行清洗 ==========
    st.markdown('<p class="step-header">🚀 执行清洗</p>', unsafe_allow_html=True)
    
    col1, col2, col3 = st.columns([2, 1, 1])
    
    with col1:
        if st.button("🧹 开始清洗", type="primary", use_container_width=True):
            # 确定数据源
            data_source = None
            if uploaded_file:
                # 保存上传的文件
                temp_path = f"/tmp/{uploaded_file.name}"
                with open(temp_path, 'wb') as f:
                    f.write(uploaded_file.getbuffer())
                data_source = temp_path
            elif selected_file:
                data_source = selected_file
            
            if not data_source:
                st.error("请先选择数据源！")
            else:
                # 执行清洗
                with st.spinner("正在清洗数据..."):
                    try:
                        comments = st.session_state.cleaner.clean_file(data_source)
                        report = st.session_state.cleaner.get_report()
                        
                        # 保存到 session state
                        st.session_state.cleaned_comments = comments
                        st.session_state.cleaning_report = report
                        
                        st.success(f"✓ 清洗完成！共 {len(comments)} 条评论")
                        
                    except Exception as e:
                        st.error(f"清洗失败: {str(e)}")
                        import traceback
                        st.code(traceback.format_exc())
    
    with col2:
        if st.button("🔄 重置", use_container_width=True):
            st.session_state.cleaner = DataCleaner()
            st.session_state.cleaned_comments = None
            st.session_state.cleaning_report = None
            st.rerun()
    
    with col3:
        if st.session_state.cleaned_comments:
            if st.button("➡️ 继续分析", use_container_width=True, type="secondary"):
                st.info("请前往「情感分析」页面继续")
    
    # ========== 显示清洗报告 ==========
    if st.session_state.cleaning_report:
        report = st.session_state.cleaning_report
        
        st.markdown("---")
        st.markdown('<p class="step-header">📊 清洗报告</p>', unsafe_allow_html=True)
        
        # 基本统计
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.metric("原始数据", f"{report.total_raw} 条")
        
        with col2:
            st.metric("清洗后", f"{report.total_cleaned} 条")
        
        with col3:
            increase = report.total_cleaned - report.total_raw
            st.metric("增量", f"+{increase} 条", f"含回复")
        
        with col4:
            platform_str = ", ".join([f"{k}: {v}" for k, v in report.platform_stats.items()])
            st.metric("平台", platform_str if platform_str else "-")
        
        # 质量统计
        if report.quality_stats:
            st.markdown("#### 质量统计")
            
            col1, col2, col3 = st.columns(3)
            
            with col1:
                ratio = report.quality_stats.get('with_ip_ratio', 0)
                st.metric("含IP属地", f"{ratio:.1%}")
                st.progress(ratio)
            
            with col2:
                ratio = report.quality_stats.get('with_time_ratio', 0)
                st.metric("含发布时间", f"{ratio:.1%}")
                st.progress(ratio)
            
            with col3:
                ratio = report.quality_stats.get('with_user_level_ratio', 0)
                st.metric("含用户等级", f"{ratio:.1%}")
                st.progress(ratio)
        
        # 清洗统计
        if report.cleaning_stats:
            st.markdown("#### 清洗操作统计")
            
            stats = report.cleaning_stats
            col1, col2, col3, col4 = st.columns(4)
            
            with col1:
                st.metric("HTML标签移除", stats.get('html_removed', 0))
            
            with col2:
                st.metric("URL标记", stats.get('url_marked', 0))
            
            with col3:
                st.metric("@提及标记", stats.get('mention_marked', 0))
            
            with col4:
                st.metric("表情标准化", stats.get('emoji_normalized', 0))
        
        # 错误信息
        if report.errors:
            with st.expander(f"⚠️ 查看错误信息 ({len(report.errors)} 条)"):
                for error in report.errors[:10]:
                    st.warning(error)
    
    # ========== 数据预览 ==========
    if st.session_state.cleaned_comments:
        st.markdown("---")
        st.markdown('<p class="step-header">👁️ 数据预览</p>', unsafe_allow_html=True)
        
        comments = st.session_state.cleaned_comments
        
        # 筛选器
        col1, col2, col3 = st.columns([2, 2, 1])
        
        with col1:
            # 平台筛选
            platforms = list(set(c.platform for c in comments))
            selected_platform = st.multiselect(
                "筛选平台",
                platforms,
                default=platforms
            )
        
        with col2:
            # 是否回复
            reply_filter = st.radio(
                "评论类型",
                ["全部", "主评论", "回复"],
                horizontal=True
            )
        
        with col3:
            show_count = st.number_input(
                "显示数量",
                min_value=10,
                max_value=len(comments),
                value=min(50, len(comments))
            )
        
        # 应用筛选
        filtered_comments = comments
        
        if selected_platform:
            filtered_comments = [c for c in filtered_comments if c.platform in selected_platform]
        
        if reply_filter == "主评论":
            filtered_comments = [c for c in filtered_comments if not c.is_reply]
        elif reply_filter == "回复":
            filtered_comments = [c for c in filtered_comments if c.is_reply]
        
        # 转换为 DataFrame
        data = []
        for c in filtered_comments[:show_count]:
            data.append({
                'ID': c.comment_id[:20] + '...' if len(c.comment_id) > 20 else c.comment_id,
                '平台': c.platform,
                '用户': c.user_name,
                '等级': c.user_level if c.user_level else '-',
                '内容': c.content[:50] + '...' if len(c.content) > 50 else c.content,
                'IP属地': c.ip_location if c.ip_location else '-',
                '点赞': c.like_count,
                '回复数': c.reply_count,
                '是否回复': '是' if c.is_reply else '否'
            })
        
        df = pd.DataFrame(data)
        
        st.dataframe(
            df,
            use_container_width=True,
            height=400
        )
        
        # 导出
        st.markdown("#### 导出数据")
        
        col1, col2, col3 = st.columns([1, 1, 2])
        
        # 准备导出数据
        export_data = []
        for c in filtered_comments:
            item = safe_to_dict(c)
            if item:
                export_data.append(item)
        
        with col1:
            if export_data:
                export_df = pd.DataFrame(export_data)
                csv = export_df.to_csv(index=False).encode('utf-8-sig')
                
                st.download_button(
                    label="📥 导出为 CSV",
                    data=csv,
                    file_name=f"cleaned_data_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
                    mime="text/csv",
                    use_container_width=True
                )
            else:
                st.info("无数据可导出")
        
        with col2:
            if export_data:
                import json
                json_str = json.dumps(export_data, ensure_ascii=False, indent=2)
                
                st.download_button(
                    label="📥 导出为 JSON",
                    data=json_str,
                    file_name=f"cleaned_data_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json",
                    mime="application/json",
                    use_container_width=True
                )
            else:
                st.info("无数据可导出")


# 渲染页面
render_data_cleaning_page()
