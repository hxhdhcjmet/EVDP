"""
AI 舆情分析
通过用户配置的 OpenAI-compatible API 对本地采集数据进行摘要、风险研判和问答。
"""

from datetime import datetime
from pathlib import Path

import streamlit as st

from core.ai import (
    AIAnalyzer,
    AIProviderConfig,
    OpenAICompatibleClient,
    build_data_context,
)
from core.paths import DATA_DIR, ensure_runtime_dirs


ensure_runtime_dirs()

st.set_page_config(
    page_title="AI 舆情分析",
    layout="wide",
    page_icon="🤖",
)


def list_jsonl_files() -> list[Path]:
    return sorted(DATA_DIR.rglob("*.jsonl"), key=lambda p: p.stat().st_mtime, reverse=True)


def render_config_panel() -> AIProviderConfig | None:
    with st.sidebar:
        st.header("模型配置")
        base_url = st.text_input(
            "Base URL",
            value=st.session_state.get("ai_base_url", "https://api.openai.com/v1"),
            help="兼容 OpenAI Chat Completions 的服务地址",
        )
        model = st.text_input(
            "Model",
            value=st.session_state.get("ai_model", ""),
            placeholder="例如 gpt-4o-mini / deepseek-chat",
        )
        api_key = st.text_input(
            "API Key",
            value="",
            type="password",
            help="默认仅在当前会话中使用，不写入本地文件",
        )
        temperature = st.slider("Temperature", 0.0, 1.0, 0.2, 0.1)
        timeout = st.slider("超时时间（秒）", 15, 180, 60, 5)

        st.session_state.ai_base_url = base_url
        st.session_state.ai_model = model

        st.caption("提示：评论样本和统计摘要会发送到你配置的模型服务。")

        if not api_key or not model:
            return None

        return AIProviderConfig(
            api_key=api_key,
            model=model,
            base_url=base_url,
            temperature=temperature,
            timeout=timeout,
        )


def render_ai_analysis_page() -> None:
    st.title("🤖 AI 舆情分析")

    config = render_config_panel()
    files = list_jsonl_files()
    if not files:
        st.info("暂无可分析的 JSONL 数据文件。")
        return

    selected = st.selectbox(
        "选择数据文件",
        files,
        format_func=lambda p: str(p.relative_to(DATA_DIR)),
    )

    col_a, col_b, col_c = st.columns(3)
    with col_a:
        sample_size = st.slider("抽样评论数", 20, 200, 80, 10)
    with col_b:
        max_rows = st.slider("最多读取行数", 500, 20000, 5000, 500)
    with col_c:
        max_tokens = st.slider("最大输出 Tokens", 500, 4000, 1600, 100)

    context = build_data_context(selected, sample_size=sample_size, max_rows=max_rows)

    with st.expander("数据上下文预览", expanded=False):
        st.json({
            "source_file": str(selected.relative_to(DATA_DIR)),
            "platform": context.platform,
            "total_rows": context.total_rows,
            "sampled_rows": context.sampled_rows,
            "stats": context.stats,
        })

    task = st.radio(
        "分析任务",
        ["summary", "risk", "recommendation", "qa"],
        format_func={
            "summary": "舆情摘要",
            "risk": "风险研判",
            "recommendation": "处置建议",
            "qa": "自定义问答",
        }.get,
        horizontal=True,
    )

    question = ""
    if task == "qa":
        question = st.text_area(
            "你的问题",
            placeholder="例如：负面评论主要围绕哪些观点？是否存在疑似组织化传播？",
            height=100,
        )

    col_run, col_test = st.columns([3, 1])
    with col_test:
        test_clicked = st.button("测试连接", use_container_width=True)
    with col_run:
        run_clicked = st.button("开始 AI 分析", type="primary", use_container_width=True)

    if (test_clicked or run_clicked) and config is None:
        st.error("请先在侧边栏填写 API Key 和模型名称。")
        return

    if config:
        client = OpenAICompatibleClient(config)

        if test_clicked:
            with st.spinner("正在测试模型连接..."):
                try:
                    reply = client.test_connection()
                    st.success(f"连接成功：{reply}")
                except Exception as exc:
                    st.error(f"连接失败：{exc}")

        if run_clicked:
            if task == "qa" and not question.strip():
                st.error("请输入自定义问题。")
                return
            if context.total_rows == 0:
                st.error("当前文件没有可分析内容。")
                return

            with st.spinner("正在请求 AI 模型分析..."):
                try:
                    analyzer = AIAnalyzer(client)
                    result = analyzer.analyze(
                        context=context,
                        task=task,
                        question=question.strip(),
                        max_tokens=max_tokens,
                    )
                    st.session_state.ai_last_result = result.content
                    st.session_state.ai_last_task = task
                    st.session_state.ai_last_file = str(selected.relative_to(DATA_DIR))
                except Exception as exc:
                    st.error(f"AI 分析失败：{exc}")

    if st.session_state.get("ai_last_result"):
        st.markdown("---")
        st.subheader("分析结果")
        st.markdown(st.session_state.ai_last_result)
        st.download_button(
            "下载 Markdown",
            data=(
                f"# AI 舆情分析结果\n\n"
                f"- 数据文件: {st.session_state.get('ai_last_file', '-')}\n"
                f"- 任务: {st.session_state.get('ai_last_task', '-')}\n"
                f"- 生成时间: {datetime.now().isoformat()}\n\n"
                f"{st.session_state.ai_last_result}\n"
            ),
            file_name=f"ai_analysis_{datetime.now().strftime('%Y%m%d_%H%M%S')}.md",
            mime="text/markdown",
            use_container_width=True,
        )


render_ai_analysis_page()
