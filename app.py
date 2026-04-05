"""
EVDP 主页 - 导航与教程
展示各功能模块的使用指南
"""

import streamlit as st
from pathlib import Path

# 页面配置
st.set_page_config(
    page_title="EVDP - 舆情安全分析平台",
    layout="wide",
    page_icon="🏠"
)

# 自定义样式
st.markdown("""
<style>
    .main-title {
        font-size: 2.5em;
        font-weight: bold;
        text-align: center;
        margin-bottom: 0.5em;
        color: #1f77b4;
    }
    .sub-title {
        font-size: 1.2em;
        text-align: center;
        color: #666;
        margin-bottom: 2em;
    }
    .module-card {
        background: #f8f9fa;
        border-radius: 10px;
        padding: 20px;
        margin: 10px 0;
        border-left: 4px solid #1f77b4;
    }
    .module-title {
        font-size: 1.3em;
        font-weight: bold;
        color: #333;
        margin-bottom: 10px;
    }
    .module-name {
        font-family: monospace;
        background: #e9ecef;
        padding: 2px 8px;
        border-radius: 4px;
        color: #d63384;
    }
    .feature-item {
        margin: 5px 0;
        padding-left: 15px;
    }
    .quick-start {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white;
        padding: 30px;
        border-radius: 15px;
        text-align: center;
        margin: 20px 0;
    }
    .theme-toggle {
        position: fixed;
        top: 60px;
        right: 20px;
        z-index: 999;
    }
</style>
""", unsafe_allow_html=True)

# 主题切换功能（通过 Streamlit 配置）
with st.sidebar:
    st.markdown("---")
    st.markdown("### 🎨 外观设置")
    theme_mode = st.radio(
        "主题模式",
        ["跟随系统", "浅色模式", "深色模式"],
        index=0,
        key="theme_mode_select"
    )

    # 保存主题偏好
    if theme_mode != st.session_state.get("last_theme", "跟随系统"):
        st.session_state["last_theme"] = theme_mode
        if theme_mode == "深色模式":
            st.markdown("""
            <style>
            .stApp { background-color: #1a1a2e; color: #eee; }
            .module-card { background: #16213e; border-left-color: #4361ee; }
            .module-title { color: #eee; }
            .sub-title { color: #aaa; }
            </style>
            """, unsafe_allow_html=True)
        elif theme_mode == "浅色模式":
            st.markdown("""
            <style>
            .stApp { background-color: #ffffff; color: #333; }
            </style>
            """, unsafe_allow_html=True)

# 主标题
st.markdown('<p class="main-title">🏠 EVDP 舆情安全分析平台</p>', unsafe_allow_html=True)
st.markdown('<p class="sub-title">Easy and Visually Achieve Data Process</p>', unsafe_allow_html=True)

# 快速开始
st.markdown("""
<div class="quick-start">
    <h2>🚀 快速开始</h2>
    <p>从左侧边栏选择功能模块，或在下方查看各模块使用指南</p>
</div>
""", unsafe_allow_html=True)

# 功能概览
st.markdown("## 📋 功能概览")

col1, col2, col3 = st.columns(3)

with col1:
    st.metric("📥 数据获取", "4个平台", "B站/抖音/贴吧/知乎")

with col2:
    st.metric("🔍 安全分析", "6个维度", "情感/IP/用户/异常...")

with col3:
    st.metric("📊 报告导出", "4种格式", "MD/JSON/HTML/TXT")

st.markdown("---")

# 模块指南
st.markdown("## 📚 模块使用指南")

# ============ 数据获取模块 ============
st.markdown("""
<div class="module-card">
    <p class="module-title">📥 数据获取模块</p>
</div>
""", unsafe_allow_html=True)

data_col1, data_col2 = st.columns(2)

with data_col1:
    st.markdown("""
**B站评论爬取** <span class="module-name">01_bilibili_page</span>

- 输入视频 BV 号获取评论
- 支持Cookie认证获取更多数据
- 自动保存评论、用户信息、IP属地
""", unsafe_allow_html=True)

with data_col2:
    st.markdown("""
**抖音评论爬取** <span class="module-name">02_douyin_page</span>

- 需要先登录获取Cookie
- 支持视频链接或视频ID
- 包含评论点赞数、回复数
""", unsafe_allow_html=True)

data_col3, data_col4 = st.columns(2)

with data_col3:
    st.markdown("""
**贴吧帖子爬取** <span class="module-name">03_tieba_page</span>

- 输入帖子链接或TID
- 支持图片下载
- 获取楼层、用户、IP属地
""", unsafe_allow_html=True)

with data_col4:
    st.markdown("""
**知乎回答爬取** <span class="module-name">04_zhihu_page</span>

- 输入问题链接
- 获取回答及评论
- 支持匿名/登录模式
""", unsafe_allow_html=True)

# ============ 数据处理模块 ============
st.markdown("""
<div class="module-card">
    <p class="module-title">🔧 数据处理模块</p>
</div>
""", unsafe_allow_html=True)

proc_col1, proc_col2 = st.columns(2)

with proc_col1:
    st.markdown("""
**文件管理** <span class="module-name">05_file_page</span>

- 查看已爬取的数据文件
- 预览JSONL数据内容
- 删除/导出数据文件

**数据清洗** <span class="module-name">08_data_cleaning</span>

- 去除重复评论
- 过滤无效内容
- 数据标准化处理
""", unsafe_allow_html=True)

with proc_col2:
    st.markdown("""
**情感分析** <span class="module-name">07_sentiment_analysis</span>

- 分析评论情感倾向（正面/负面/中立）
- 批量处理大量评论
- 情感分布可视化
""", unsafe_allow_html=True)

# ============ 安全分析模块（核心） ============
st.markdown("""
<div class="module-card">
    <p class="module-title">🔒 安全分析模块（核心功能）</p>
</div>
""", unsafe_allow_html=True)

st.markdown("""
**舆情安全分析仪表盘** <span class="module-name">06_security_dashboard</span>

**这是一站式完整分析入口，整合了以下所有分析功能：**

| 分析步骤 | 功能说明 |
|----------|----------|
| 数据清洗 | 去重、去噪、格式标准化 |
| 情感分析 | 识别正面/负面/中立评论 |
| IP溯源 | 分析评论地域分布、基尼系数 |
| 用户画像 | 识别可疑账号、机器人检测 |
| 异常检测 | 发现异常行为模式 |
| 风险评估 | 综合评分与风险等级判定 |
| 报告导出 | 生成 Markdown/JSON/HTML/TXT 报告 |

**使用流程：**
1. 选择数据源（已有文件或上传新文件）
2. 配置分析参数（分析全部/限制数量、风险阈值）
3. 点击"开始完整分析"
4. 查看结果并导出报告
""", unsafe_allow_html=True)

st.markdown("---")

# 使用提示
st.markdown("## 💡 使用提示")

tip_col1, tip_col2 = st.columns(2)

with tip_col1:
    st.info("""
    **首次使用建议：**
    1. 先从 `01_bilibili_page` 或 `03_tieba_page` 获取数据
    2. 然后打开 `06_security_dashboard` 进行分析
    3. 最后导出报告查看结果
    """)

with tip_col2:
    st.warning("""
    **注意事项：**
    - 抖音/知乎爬取需要登录Cookie
    - 大量数据分析可能需要较长时间
    - 报告会自动保存到数据文件所在目录
    """)

# 页脚
st.markdown("---")
st.markdown("""
<div style="text-align: center; color: #999; padding: 20px;">
    <p>EVDP v2.1.0 | 舆情安全分析平台</p>
    <p>如有问题，请查看项目文档或提交 Issue</p>
</div>
""", unsafe_allow_html=True)
