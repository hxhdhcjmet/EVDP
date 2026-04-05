"""
情感分析页面
提供可视化的情感分析和风险评估功能
"""

import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from pathlib import Path
import sys
import os
from datetime import datetime

# 添加项目路径
sys.path.insert(0, '/home/EVDP')

from core.analysis import SentimentAnalyzer, DataCleaner

# 页面配置
st.set_page_config(
    page_title="情感分析与风险评估",
    layout="wide",
    page_icon="😊"
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
    .risk-low { color: #10b981; font-weight: bold; }
    .risk-medium { color: #f59e0b; font-weight: bold; }
    .risk-high { color: #ef4444; font-weight: bold; }
    .risk-critical { color: #dc2626; font-weight: bold; }
</style>
""", unsafe_allow_html=True)


def get_risk_color(risk_level):
    """获取风险等级颜色"""
    colors = {
        'low': '#10b981',
        'medium': '#f59e0b',
        'high': '#ef4444',
        'critical': '#dc2626'
    }
    return colors.get(risk_level, '#6b7280')


def render_sentiment_analysis_page():
    """渲染情感分析页面"""
    
    st.title("😊 情感分析与风险评估")
    st.markdown("深度分析评论情感倾向，识别潜在风险内容")
    
    # 初始化 session state
    if 'analyzer' not in st.session_state:
        st.session_state.analyzer = SentimentAnalyzer()
    if 'analysis_results' not in st.session_state:
        st.session_state.analysis_results = None
    if 'sentiment_distribution' not in st.session_state:
        st.session_state.sentiment_distribution = None
    
    # ========== 步骤 1: 选择数据源 ==========
    st.markdown('<p class="step-header">📍 步骤 1: 选择数据源</p>', unsafe_allow_html=True)
    
    col1, col2 = st.columns(2)
    
    with col1:
        data_source = st.radio(
            "数据来源",
            ["从已清洗数据选择", "直接清洗新数据"],
            horizontal=True
        )
    
    with col2:
        if data_source == "从已清洗数据选择":
            # 检查是否有清洗后的数据
            if 'cleaned_comments' in st.session_state and st.session_state.cleaned_comments:
                st.success(f"✓ 已加载 {len(st.session_state.cleaned_comments)} 条清洗数据")
            else:
                st.warning("⚠️ 未找到清洗数据，请先进行数据清洗")
        else:
            # 选择新文件
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
    
    # ========== 步骤 2: 分析配置 ==========
    st.markdown('<p class="step-header">⚙️ 步骤 2: 分析配置</p>', unsafe_allow_html=True)
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        enable_sensitive = st.checkbox("启用敏感词检测", value=True)
        enable_keywords = st.checkbox("提取关键词", value=True)
    
    with col2:
        analysis_size = st.slider(
            "分析数量",
            min_value=10,
            max_value=1000,
            value=100,
            help="限制分析数量以提升速度"
        )
    
    with col3:
        risk_threshold = st.slider(
            "风险阈值",
            min_value=40,
            max_value=80,
            value=60,
            help="超过此阈值判定为高风险"
        )
    
    # ========== 执行分析 ==========
    st.markdown('<p class="step-header">🚀 执行分析</p>', unsafe_allow_html=True)
    
    col1, col2 = st.columns([3, 1])
    
    with col1:
        if st.button("🔍 开始分析", type="primary", use_container_width=True):
            # 获取数据
            comments = None
            
            if data_source == "从已清洗数据选择":
                if 'cleaned_comments' in st.session_state:
                    comments = st.session_state.cleaned_comments
            else:
                # 清洗新数据
                if selected_file:
                    with st.spinner("正在清洗数据..."):
                        cleaner = DataCleaner()
                        comments = cleaner.clean_file(selected_file)
            
            if not comments:
                st.error("没有可用的数据！")
            else:
                # 执行分析
                with st.spinner(f"正在分析 {min(len(comments), analysis_size)} 条评论..."):
                    try:
                        # 转换为字典列表
                        comment_dicts = [
                            {
                                'comment_id': c.comment_id,
                                'content': c.content
                            }
                            for c in comments[:analysis_size]
                        ]
                        
                        # 执行分析
                        results = st.session_state.analyzer.analyze_batch(comment_dicts)
                        
                        # 获取分布统计
                        distribution = st.session_state.analyzer.get_distribution(results)
                        
                        # 保存结果
                        st.session_state.analysis_results = results
                        st.session_state.sentiment_distribution = distribution
                        
                        st.success(f"✓ 分析完成！共 {len(results)} 条评论")
                        
                    except Exception as e:
                        st.error(f"分析失败: {str(e)}")
                        import traceback
                        st.code(traceback.format_exc())
    
    with col2:
        if st.button("🔄 重置", use_container_width=True):
            st.session_state.analyzer = SentimentAnalyzer()
            st.session_state.analysis_results = None
            st.session_state.sentiment_distribution = None
            st.rerun()
    
    # ========== 显示分析结果 ==========
    if st.session_state.analysis_results and st.session_state.sentiment_distribution:
        results = st.session_state.analysis_results
        distribution = st.session_state.sentiment_distribution
        
        st.markdown("---")
        st.markdown('<p class="step-header">📊 分析结果概览</p>', unsafe_allow_html=True)
        
        # 关键指标
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.metric(
                "总评论数",
                distribution['total'],
                f"分析 {distribution['total']} 条"
            )
        
        with col2:
            st.metric(
                "平均情感分",
                f"{distribution['avg_sentiment_score']:.3f}",
                "0.5 为中性"
            )
        
        with col3:
            avg_risk = distribution['avg_risk_score']
            st.metric(
                "平均风险分",
                f"{avg_risk:.1f}/100",
                "低风险" if avg_risk < 40 else "需关注"
            )
        
        with col4:
            high_risk = distribution['high_risk']
            st.metric(
                "高风险评论",
                high_risk,
                f"{distribution['high_risk_ratio']:.1%}"
            )
        
        # ========== 可视化图表 ==========
        st.markdown("---")
        st.markdown('<p class="step-header">📈 可视化分析</p>', unsafe_allow_html=True)
        
        col1, col2 = st.columns(2)
        
        with col1:
            # 情感分布饼图
            st.markdown("#### 情感分布")
            
            fig_pie = go.Figure(data=[go.Pie(
                labels=['正面', '负面', '中立'],
                values=[
                    distribution['positive'],
                    distribution['negative'],
                    distribution['neutral']
                ],
                hole=0.4,
                marker_colors=['#10b981', '#ef4444', '#6b7280']
            )])
            
            fig_pie.update_layout(
                height=300,
                margin=dict(l=20, r=20, t=20, b=20)
            )
            
            st.plotly_chart(fig_pie, use_container_width=True)
        
        with col2:
            # 风险评分分布
            st.markdown("#### 风险评分分布")
            
            risk_scores = [r.risk_score for r in results]
            
            fig_hist = go.Figure(data=[go.Histogram(
                x=risk_scores,
                nbinsx=20,
                marker_color='#3b82f6',
                opacity=0.7
            )])
            
            fig_hist.update_layout(
                xaxis_title="风险评分",
                yaxis_title="评论数",
                height=300,
                margin=dict(l=20, r=20, t=20, b=20)
            )
            
            st.plotly_chart(fig_hist, use_container_width=True)
        
        # 敏感词统计
        if enable_sensitive and distribution['with_sensitive'] > 0:
            st.markdown("#### 敏感词统计")
            
            # 统计敏感词类别
            sensitive_categories = {}
            for r in results:
                for category in r.sensitive_categories:
                    sensitive_categories[category] = sensitive_categories.get(category, 0) + 1
            
            if sensitive_categories:
                col1, col2 = st.columns([2, 1])
                
                with col1:
                    # 敏感词类别柱状图
                    fig_sens = go.Figure(data=[go.Bar(
                        x=list(sensitive_categories.keys()),
                        y=list(sensitive_categories.values()),
                        marker_color='#f59e0b'
                    )])
                    
                    fig_sens.update_layout(
                        xaxis_title="类别",
                        yaxis_title="出现次数",
                        height=250,
                        margin=dict(l=20, r=20, t=20, b=20)
                    )
                    
                    st.plotly_chart(fig_sens, use_container_width=True)
                
                with col2:
                    st.metric("含敏感词评论", distribution['with_sensitive'])
                    st.metric("敏感词占比", f"{distribution['with_sensitive_ratio']:.1%}")
        
        # ========== 高风险评论列表 ==========
        st.markdown("---")
        st.markdown('<p class="step-header">⚠️ 高风险评论</p>', unsafe_allow_html=True)
        
        high_risk_comments = [r for r in results if r.risk_score >= risk_threshold]
        
        if high_risk_comments:
            st.warning(f"共发现 {len(high_risk_comments)} 条高风险评论")
            
            # 显示前10条
            for i, result in enumerate(sorted(high_risk_comments, key=lambda x: x.risk_score, reverse=True)[:10], 1):
                with st.expander(
                    f"#{i} - 风险: {result.risk_score}/100 ({result.risk_level.upper()}) - {result.content[:30]}...",
                    expanded=(i <= 3)
                ):
                    col1, col2 = st.columns([3, 1])
                    
                    with col1:
                        st.markdown(f"**完整内容:**")
                        st.text(result.content)
                        
                        if result.sensitive_words:
                            st.markdown(f"**敏感词:**")
                            for word_info in result.sensitive_words:
                                st.markdown(f"- `{word_info['word']}` ({word_info['category']})")
                    
                    with col2:
                        st.metric("情感", result.sentiment)
                        st.metric("情感分", f"{result.sentiment_score:.3f}")
                        st.metric("风险等级", result.risk_level.upper())
                        
                        st.markdown("**风险因素:**")
                        for factor, score in result.risk_factors.items():
                            if score > 0:
                                st.markdown(f"- {factor}: {score}")
        else:
            st.success("🎉 未发现高风险评论！")
        
        # ========== 导出报告 ==========
        st.markdown("---")
        st.markdown('<p class="step-header">📥 导出报告</p>', unsafe_allow_html=True)
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            # 导出分析结果
            export_data = []
            for r in results:
                export_data.append({
                    'comment_id': r.comment_id,
                    'content': r.content,
                    'sentiment': r.sentiment,
                    'sentiment_score': r.sentiment_score,
                    'confidence': r.confidence,
                    'risk_score': r.risk_score,
                    'risk_level': r.risk_level,
                    'sensitive_count': r.sensitive_count,
                    'sensitive_categories': ','.join(r.sensitive_categories),
                    'keywords': ','.join(r.keywords[:5])
                })
            
            export_df = pd.DataFrame(export_data)
            csv = export_df.to_csv(index=False).encode('utf-8-sig')
            
            st.download_button(
                label="📥 导出分析结果 (CSV)",
                data=csv,
                file_name=f"sentiment_analysis_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
                mime="text/csv",
                use_container_width=True
            )
        
        with col2:
            # 导出高风险评论
            if high_risk_comments:
                high_risk_data = [{
                    'comment_id': r.comment_id,
                    'content': r.content,
                    'risk_score': r.risk_score,
                    'risk_level': r.risk_level,
                    'sentiment': r.sentiment,
                    'sensitive_words': ','.join([w['word'] for w in r.sensitive_words])
                } for r in high_risk_comments]
                
                high_risk_df = pd.DataFrame(high_risk_data)
                csv_high = high_risk_df.to_csv(index=False).encode('utf-8-sig')
                
                st.download_button(
                    label="⚠️ 导出高风险评论",
                    data=csv_high,
                    file_name=f"high_risk_comments_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
                    mime="text/csv",
                    use_container_width=True
                )
        
        with col3:
            # 导出统计报告
            import json
            report = {
                'summary': distribution,
                'config': {
                    'analysis_size': analysis_size,
                    'risk_threshold': risk_threshold,
                    'enable_sensitive': enable_sensitive
                },
                'timestamp': datetime.now().isoformat()
            }
            
            st.download_button(
                label="📊 导出统计报告 (JSON)",
                data=json.dumps(report, ensure_ascii=False, indent=2),
                file_name=f"analysis_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json",
                mime="application/json",
                use_container_width=True
            )


# 渲染页面
render_sentiment_analysis_page()
