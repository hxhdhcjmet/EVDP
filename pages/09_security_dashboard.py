"""
舆情安全分析仪表盘
一键式完整安全分析页面
"""

import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
from pathlib import Path
import sys
import os
from datetime import datetime
import json

# 添加项目路径
sys.path.insert(0, '/home/EVDP')

from core.analysis import SecurityPipeline

# 页面配置
st.set_page_config(
    page_title="舆情安全分析仪表盘",
    layout="wide",
    page_icon="🔒"
)

# 自定义样式
st.markdown("""
<style>
    .metric-card {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        padding: 20px;
        border-radius: 10px;
        color: white;
        margin: 10px 0;
    }
    .risk-critical { color: #dc2626; font-weight: bold; }
    .risk-high { color: #ef4444; font-weight: bold; }
    .risk-medium { color: #f59e0b; font-weight: bold; }
    .risk-low { color: #10b981; font-weight: bold; }
    .step-header {
        font-size: 1.3em;
        font-weight: bold;
        margin-top: 1.5em;
        margin-bottom: 0.5em;
        color: #1f77b4;
    }
</style>
""", unsafe_allow_html=True)


def get_risk_color(level):
    """获取风险等级颜色"""
    colors = {
        'critical': '#dc2626',
        'high': '#ef4444',
        'medium': '#f59e0b',
        'low': '#10b981'
    }
    return colors.get(level, '#6b7280')


def generate_markdown_report(report) -> str:
    """生成 Markdown 格式报告"""
    md = f"""# 舆情安全分析报告

**生成时间**: {report.generated_at}  
**数据源**: {report.source_file}  
**平台**: {report.platform}

---

## 📊 综合评分

| 指标 | 数值 |
|------|------|
| 综合风险评分 | {report.overall_score}/100 |
| 风险等级 | **{report.overall_level.upper()}** |
| 总评论数 | {report.total_comments} |
| 高风险评论 | {report.high_risk_comments} |
| 可疑账号 | {report.suspicious_users} |

### 评分分解

- 情感风险: {report.score_breakdown.get('sentiment', 0)}/100
- IP 地域: {report.score_breakdown.get('ip', 0)}/100
- 用户画像: {report.score_breakdown.get('user', 0)}/100
- 异常检测: {report.score_breakdown.get('anomaly', 0)}/100

---

## 🔍 关键发现

"""
    for finding in report.key_findings:
        md += f"- {finding}\n"

    md += "\n## 💡 建议\n\n"
    for i, rec in enumerate(report.recommendations, 1):
        md += f"{i}. {rec}\n"

    return md


def render_security_dashboard():
    """渲染安全仪表盘"""

    st.title("🔒 舆情安全分析仪表盘")
    st.markdown("一键式完整安全分析：清洗 → 情感 → IP溯源 → 用户画像 → 异常检测")

    # 初始化 session state
    if 'report' not in st.session_state:
        st.session_state.report = None

    # ========== 数据源选择 ==========
    st.markdown('<p class="step-header">📍 步骤 1: 选择数据源</p>', unsafe_allow_html=True)

    col1, col2 = st.columns(2)

    with col1:
        st.markdown("**方式 1: 从已有数据选择**")
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

    # ========== 分析配置 ==========
    st.markdown('<p class="step-header">⚙️ 步骤 2: 分析配置</p>', unsafe_allow_html=True)

    col1, col2, col3 = st.columns(3)

    with col1:
        analyze_all = st.checkbox("分析全部数据", value=True, help="勾选则分析所有评论，取消可设置数量限制")
        if not analyze_all:
            analysis_limit = st.slider(
                "分析数量限制",
                min_value=50,
                max_value=10000,
                value=500,
                step=50,
                help="情感分析最大条数"
            )
        else:
            analysis_limit = None  # None 表示不限制

    with col2:
        risk_threshold = st.slider(
            "高风险阈值",
            min_value=40,
            max_value=80,
            value=60,
            help="超过此阈值判定为高风险评论"
        )

    with col3:
        st.markdown("**分析选项**")
        enable_ip = st.checkbox("启用 IP 地域分析", value=True)
        enable_user = st.checkbox("启用用户画像", value=True)

    # ========== 执行分析 ==========
    st.markdown('<p class="step-header">🚀 步骤 3: 执行分析</p>', unsafe_allow_html=True)

    col1, col2 = st.columns([3, 1])

    with col1:
        if st.button("🔍 开始完整分析", type="primary", use_container_width=True):
            # 确定数据源
            data_source = None
            if uploaded_file:
                temp_path = f"/tmp/{uploaded_file.name}"
                with open(temp_path, 'wb') as f:
                    f.write(uploaded_file.getbuffer())
                data_source = temp_path
            elif selected_file:
                data_source = selected_file

            if not data_source:
                st.error("请先选择数据源！")
            else:
                # 使用当前配置创建 pipeline
                pipeline = SecurityPipeline(
                    risk_threshold=risk_threshold,
                    analysis_limit=analysis_limit
                )
                # 执行流水线
                with st.spinner("正在执行完整分析流水线..."):
                    try:
                        report = pipeline.run(data_source)
                        st.session_state.report = report
                        st.success("✓ 分析完成！")
                    except Exception as e:
                        st.error(f"分析失败: {str(e)}")
                        import traceback
                        st.code(traceback.format_exc())

    with col2:
        if st.button("🔄 重置", use_container_width=True):
            st.session_state.report = None
            st.rerun()

    # ========== 显示报告 ==========
    if st.session_state.report:
        report = st.session_state.report

        st.markdown("---")
        st.markdown('<p class="step-header">📊 分析结果</p>', unsafe_allow_html=True)

        # ── 综合风险仪表盘 ──
        col1, col2, col3, col4 = st.columns(4)

        risk_color = get_risk_color(report.overall_level)

        with col1:
            st.metric(
                "综合风险评分",
                f"{report.overall_score}/100",
                f"风险等级: {report.overall_level.upper()}",
                delta_color="inverse"
            )

        with col2:
            st.metric(
                "总评论数",
                report.total_comments,
                f"高风险: {report.high_risk_comments}"
            )

        with col3:
            st.metric(
                "可疑账号",
                report.suspicious_users,
                "需关注"
            )

        with col4:
            anomaly_count = len(report.anomalies)
            st.metric(
                "异常检测",
                anomaly_count,
                "项异常"
            )

        # ── 评分分解 ──
        st.markdown("#### 评分分解")
        col1, col2, col3, col4 = st.columns(4)

        with col1:
            st.metric("情感风险", f"{report.score_breakdown.get('sentiment', 0)}/100")

        with col2:
            st.metric("IP 地域", f"{report.score_breakdown.get('ip', 0)}/100")

        with col3:
            st.metric("用户画像", f"{report.score_breakdown.get('user', 0)}/100")

        with col4:
            st.metric("异常检测", f"{report.score_breakdown.get('anomaly', 0)}/100")

        # ── 可视化分析 ──
        st.markdown("---")
        st.markdown('<p class="step-header">📈 可视化分析</p>', unsafe_allow_html=True)

        col1, col2 = st.columns(2)

        with col1:
            # 情感分布
            if report.sentiment_distribution:
                st.markdown("#### 情感分布")
                fig_sentiment = go.Figure(data=[go.Pie(
                    labels=['正面', '负面', '中立'],
                    values=[
                        report.sentiment_distribution.get('positive', 0),
                        report.sentiment_distribution.get('negative', 0),
                        report.sentiment_distribution.get('neutral', 0)
                    ],
                    hole=0.4,
                    marker_colors=['#10b981', '#ef4444', '#6b7280']
                )])
                fig_sentiment.update_layout(height=300, margin=dict(l=20, r=20, t=20, b=20))
                st.plotly_chart(fig_sentiment, use_container_width=True)

        with col2:
            # 评分分解柱状图
            st.markdown("#### 评分分解")
            breakdown = report.score_breakdown
            fig_breakdown = go.Figure(data=[go.Bar(
                x=['情感', 'IP地域', '用户', '异常'],
                y=[
                    breakdown.get('sentiment', 0),
                    breakdown.get('ip', 0),
                    breakdown.get('user', 0),
                    breakdown.get('anomaly', 0)
                ],
                marker_color=['#3b82f6', '#8b5cf6', '#ec4899', '#f59e0b']
            )])
            fig_breakdown.update_layout(
                yaxis_title="评分",
                height=300,
                margin=dict(l=20, r=20, t=20, b=20)
            )
            st.plotly_chart(fig_breakdown, use_container_width=True)

        # ── IP 地域分析 ──
        if report.ip_result and report.ip_result.has_sufficient_ip:
            st.markdown("---")
            st.markdown("#### IP 地域分布")

            col1, col2 = st.columns([2, 1])

            with col1:
                # 省份分布柱状图
                if report.ip_result.province_distribution:
                    top_provinces = sorted(
                        report.ip_result.province_distribution.items(),
                        key=lambda x: x[1],
                        reverse=True
                    )[:10]

                    fig_ip = go.Figure(data=[go.Bar(
                        x=[p[0] for p in top_provinces],
                        y=[p[1] for p in top_provinces],
                        marker_color='#06b6d4'
                    )])
                    fig_ip.update_layout(
                        xaxis_title="省份",
                        yaxis_title="评论数",
                        height=300,
                        margin=dict(l=20, r=20, t=20, b=20)
                    )
                    st.plotly_chart(fig_ip, use_container_width=True)

            with col2:
                st.markdown("**地域指标**")
                st.metric("基尼系数", f"{report.ip_result.gini_coefficient:.3f}")
                st.metric("集中度评分", f"{report.ip_result.concentration_score}/100")
                st.metric("前3占比", f"{report.ip_result.top3_ratio:.1%}")
                if report.ip_result.wave_detected:
                    st.warning("⚠️ 检测到波浪式扩散")

        # ── 用户画像 ──
        if report.user_profiling:
            st.markdown("---")
            st.markdown("#### 用户行为画像")

            for platform, pr in report.user_profiling.items():
                with st.expander(f"📱 {platform.upper()} - {pr.analyzed_users} 个用户"):
                    col1, col2, col3 = st.columns(3)

                    with col1:
                        st.metric("高风险账号", pr.high_risk_count)

                    with col2:
                        st.metric("中风险账号", pr.medium_risk_count)

                    with col3:
                        st.metric("平均可疑度", f"{pr.avg_suspicion_score:.1f}/100")

                    # 可疑账号列表
                    if pr.suspicious_users:
                        st.markdown("**可疑账号列表**")
                        for user in pr.suspicious_users[:10]:
                            with st.expander(
                                f"{user.user_name} - 风险 {user.suspicion_score}/100 ({user.suspicion_level.upper()})"
                            ):
                                col1, col2 = st.columns([2, 1])
                                with col1:
                                    st.markdown("**可疑原因:**")
                                    for reason in user.suspicion_reasons:
                                        st.markdown(f"- {reason}")

                                with col2:
                                    st.metric("评论数", user.total_comments)
                                    st.metric("唯一率", f"{user.unique_content_ratio:.1%}")
                                    st.metric("短评占比", f"{user.short_content_ratio:.1%}")

        # ── 异常检测 ──
        if report.anomalies:
            st.markdown("---")
            st.markdown("#### 异常检测")

            for anomaly in report.anomalies[:10]:
                severity_color = get_risk_color(anomaly.severity)
                st.markdown(
                    f"**[{anomaly.severity.upper()}]** {anomaly.description}",
                    unsafe_allow_html=True
                )
                st.caption(f"影响: {anomaly.affected_count} 条 | 评分: {anomaly.score}/100")

        # ── 关键发现 ──
        st.markdown("---")
        st.markdown("#### 🔍 关键发现")

        for finding in report.key_findings:
            st.info(finding)

        # ── 建议 ──
        st.markdown("#### 💡 建议")

        for i, rec in enumerate(report.recommendations, 1):
            st.markdown(f"{i}. {rec}")

        # ── 导出报告 ──
        st.markdown("---")
        st.markdown("#### 📥 导出报告")

        # 输入来源URL
        source_url = st.text_input("来源链接（可选）", value="", key="source_url_input",
                                   help="输入帖子或视频的原始链接，将记录在报告中")

        # 选择报告格式
        st.markdown("**选择报告格式:**")
        fmt_md = st.checkbox("Markdown (.md)", value=True, key="fmt_md")
        fmt_json = st.checkbox("JSON (.json)", value=True, key="fmt_json")
        fmt_html = st.checkbox("HTML (.html)", value=True, key="fmt_html")
        fmt_txt = st.checkbox("TXT (.txt)", value=False, key="fmt_txt")

        col1, col2 = st.columns(2)

        with col1:
            # 保存到文件
            if st.button("💾 保存报告到数据目录", type="primary", use_container_width=True):
                formats = []
                if fmt_md: formats.append('md')
                if fmt_json: formats.append('json')
                if fmt_html: formats.append('html')
                if fmt_txt: formats.append('txt')
                
                if not formats:
                    st.error("请至少选择一种报告格式！")
                else:
                    try:
                        # 获取数据目录
                        import os
                        data_dir = os.path.dirname(report.source_file) or "/home/EVDP/data"
                        
                        # 保存报告
                        saved_files = report.save_report(
                            output_dir=data_dir,
                            source_url=source_url,
                            formats=formats
                        )
                        
                        st.success("✓ 报告已保存！")
                        for fmt, path in saved_files.items():
                            st.code(path, language=None)
                    except Exception as e:
                        st.error(f"保存失败: {e}")

        with col2:
            # 在线下载
            st.markdown("**或在线下载:**")
            
            # 准备下载内容
            report_json = {
                'source_file': report.source_file,
                'platform': report.platform,
                'generated_at': report.generated_at,
                'overall_score': report.overall_score,
                'overall_level': report.overall_level,
                'score_breakdown': report.score_breakdown,
                'total_comments': report.total_comments,
                'high_risk_comments': report.high_risk_comments,
                'suspicious_users': report.suspicious_users,
                'key_findings': report.key_findings,
                'recommendations': report.recommendations,
            }

            dl_col1, dl_col2 = st.columns(2)
            with dl_col1:
                st.download_button(
                    label="📊 JSON",
                    data=json.dumps(report_json, ensure_ascii=False, indent=2),
                    file_name=f"security_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json",
                    mime="application/json",
                    use_container_width=True
                )
            with dl_col2:
                md_content = generate_markdown_report(report)
                st.download_button(
                    label="📝 Markdown",
                    data=md_content,
                    file_name=f"security_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.md",
                    mime="text/markdown",
                    use_container_width=True
                )


# 渲染页面
render_security_dashboard()
