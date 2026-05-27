"""
数据与报告中心
汇总本地采集数据、分析报告和平台分布，方便提交演示与日常管理。
"""

import json
from collections import Counter
from datetime import datetime
from pathlib import Path

import pandas as pd
import plotly.graph_objects as go
import streamlit as st

from core.paths import DATA_DIR, ensure_runtime_dirs


ensure_runtime_dirs()

st.set_page_config(
    page_title="数据与报告中心",
    layout="wide",
    page_icon="📊"
)


def infer_platform(path: Path) -> str:
    text = str(path).lower()
    if "bili" in text or "bilibili" in text:
        return "bilibili"
    if "douyin" in text:
        return "douyin"
    if "tieba" in text or "tid_" in text:
        return "tieba"
    if "zhihu" in text:
        return "zhihu"
    return "unknown"


def count_jsonl_lines(path: Path) -> int:
    try:
        with path.open("r", encoding="utf-8") as f:
            return sum(1 for line in f if line.strip())
    except Exception:
        return 0


def collect_data_files() -> pd.DataFrame:
    rows = []
    for path in DATA_DIR.rglob("*.jsonl"):
        stat = path.stat()
        rows.append({
            "文件": str(path.relative_to(DATA_DIR)),
            "平台": infer_platform(path),
            "记录数": count_jsonl_lines(path),
            "大小(KB)": round(stat.st_size / 1024, 1),
            "更新时间": datetime.fromtimestamp(stat.st_mtime).strftime("%Y-%m-%d %H:%M"),
            "路径": str(path),
        })
    return pd.DataFrame(rows)


def collect_reports() -> pd.DataFrame:
    rows = []
    for pattern in ("security_report_*.md", "security_report_*.json", "security_report_*.html", "security_report_*.txt"):
        for path in DATA_DIR.rglob(pattern):
            stat = path.stat()
            risk_level = "-"
            score = "-"
            if path.suffix == ".json":
                try:
                    payload = json.loads(path.read_text(encoding="utf-8"))
                    risk = payload.get("risk", {})
                    risk_level = risk.get("level", "-")
                    score = risk.get("score", "-")
                except Exception:
                    pass
            rows.append({
                "报告": str(path.relative_to(DATA_DIR)),
                "格式": path.suffix.lstrip(".").upper(),
                "风险等级": risk_level,
                "评分": score,
                "大小(KB)": round(stat.st_size / 1024, 1),
                "生成时间": datetime.fromtimestamp(stat.st_mtime).strftime("%Y-%m-%d %H:%M"),
                "路径": str(path),
            })
    return pd.DataFrame(rows)


def render_platform_chart(df: pd.DataFrame) -> None:
    if df.empty:
        st.info("暂无数据文件。")
        return

    platform_counts = df.groupby("平台", as_index=False)["记录数"].sum()
    fig = go.Figure(data=[go.Bar(
        x=platform_counts["平台"],
        y=platform_counts["记录数"],
        marker_color=["#2563eb", "#16a34a", "#f97316", "#db2777", "#64748b"][:len(platform_counts)]
    )])
    fig.update_layout(
        height=320,
        margin=dict(l=20, r=20, t=20, b=20),
        xaxis_title="平台",
        yaxis_title="记录数"
    )
    st.plotly_chart(fig, use_container_width=True)


def render_report_center() -> None:
    st.title("📊 数据与报告中心")

    data_df = collect_data_files()
    report_df = collect_reports()

    total_records = int(data_df["记录数"].sum()) if not data_df.empty else 0
    platform_total = data_df["平台"].nunique() if not data_df.empty else 0
    latest_update = data_df["更新时间"].max() if not data_df.empty else "-"

    col1, col2, col3, col4 = st.columns(4)
    col1.metric("数据文件", len(data_df))
    col2.metric("累计记录", total_records)
    col3.metric("覆盖平台", platform_total)
    col4.metric("分析报告", len(report_df), latest_update)

    tab_data, tab_reports, tab_quality = st.tabs(["数据资产", "报告归档", "质量概览"])

    with tab_data:
        col_chart, col_table = st.columns([1, 1])
        with col_chart:
            st.subheader("平台数据分布")
            render_platform_chart(data_df)
        with col_table:
            st.subheader("最近数据文件")
            if data_df.empty:
                st.info("暂无 JSONL 数据。")
            else:
                latest = data_df.sort_values("更新时间", ascending=False).head(10)
                st.dataframe(
                    latest[["文件", "平台", "记录数", "大小(KB)", "更新时间"]],
                    use_container_width=True,
                    hide_index=True
                )

    with tab_reports:
        if report_df.empty:
            st.info("暂无导出的安全分析报告。")
        else:
            st.dataframe(
                report_df.sort_values("生成时间", ascending=False)[["报告", "格式", "风险等级", "评分", "大小(KB)", "生成时间"]],
                use_container_width=True,
                hide_index=True
            )

    with tab_quality:
        if data_df.empty:
            st.info("暂无可评估的数据文件。")
            return

        empty_files = data_df[data_df["记录数"] == 0]
        by_platform = Counter(data_df["平台"])
        col_a, col_b = st.columns(2)
        with col_a:
            st.subheader("平台文件数")
            st.dataframe(
                pd.DataFrame(by_platform.items(), columns=["平台", "文件数"]),
                use_container_width=True,
                hide_index=True
            )
        with col_b:
            st.subheader("需要关注")
            if empty_files.empty:
                st.success("未发现空数据文件。")
            else:
                st.warning(f"发现 {len(empty_files)} 个空数据文件。")
                st.dataframe(empty_files[["文件", "平台", "更新时间"]], use_container_width=True, hide_index=True)


render_report_center()
