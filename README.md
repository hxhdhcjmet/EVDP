# EVDP - Easy & Visual Data Processor

[English](README_EN.md)

EVDP 是一个面向舆情数据处理与安全分析的 Streamlit 应用，覆盖多平台数据采集、统一清洗、情感分析、IP 地域分析、用户画像、异常检测、风险评分和报告归档。项目适合用于课程实验、开源展示、数据分析原型和本地化舆情研判演示。

## 核心能力

- 多平台采集：支持 Bilibili、抖音、百度贴吧、知乎的数据采集入口，并提供 Cookie 或扫码登录流程。
- 标准化清洗：将不同平台的评论、回复、IP、时间、用户字段统一为可分析的数据结构。
- 舆情安全分析：整合情感倾向、敏感词、地域集中度、用户可疑度和异常行为检测。
- AI 辅助分析：支持用户配置 OpenAI-compatible API，对本地数据进行摘要、风险研判和问答。
- 可视化仪表盘：基于 Streamlit 提供交互式页面，支持文件预览、分析配置、图表展示和报告下载。
- 报告中心：集中查看本地数据资产、平台分布、空文件风险和已导出的安全分析报告。
- 多格式导出：安全分析报告支持 Markdown、JSON、HTML 和 TXT 格式。

## 功能页面

| 页面 | 功能 |
| --- | --- |
| `01_bilibili_page` | Bilibili 视频评论采集、基础分析、词云和地域分布图 |
| `02_douyin_page` | 抖音视频评论采集、Cookie 验证、评论可视化 |
| `03_tieba_page` | 百度贴吧帖子回复采集，支持图片下载 |
| `04_zhihu_page` | 知乎问题/回答评论采集，支持扫码或手动登录 |
| `05_file_page` | 本地数据文件树状浏览、JSON/JSONL/图片预览、删除和重命名 |
| `06_security_dashboard` | 一站式舆情安全分析，支持清洗、情感、IP、用户、异常、风险评分和报告导出 |
| `07_sentiment_analysis` | 独立情感分析与高风险评论导出 |
| `08_data_cleaning` | 独立数据清洗与质量统计 |
| `09_report_center` | 数据资产统计、平台分布、报告归档和质量概览 |
| `10_ai_analysis` | AI 舆情摘要、风险研判、处置建议和自定义问答 |

## 快速开始

### Docker 推荐

Linux / macOS / WSL:

```bash
bash ./run.sh
```

Windows PowerShell:

```powershell
.\run.ps1
```

手动运行:

```bash
docker build -t evdp .
docker run -d -p 8501:8501 -v ./data:/home/EVDP/data -v ./assets:/home/EVDP/assets evdp
```

启动后访问 `http://localhost:8501`。

### 本地 Python

```bash
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
python -m playwright install chromium
streamlit run app.py
```

Windows 激活虚拟环境:

```powershell
.\venv\Scripts\activate
```

也可以使用 `setup.sh` 或 `setup.ps1` 自动安装依赖。

## 推荐使用流程

1. 在采集页面选择一个平台获取数据，采集结果会保存到 `data/`。
2. 在 `05_file_page` 预览 JSONL、JSON 或图片文件，确认数据格式和内容。
3. 在 `08_data_cleaning` 进行清洗，或直接进入 `06_security_dashboard` 运行完整分析。
4. 根据需要开启或关闭 IP 地域、用户画像、异常检测等分析选项。
5. 导出安全分析报告，并在 `09_report_center` 查看数据与报告归档。
6. 如需模型辅助研判，可在 `10_ai_analysis` 配置 API 并运行 AI 分析。

## 数据与报告

- 采集数据默认保存在 `data/` 目录。
- 上传文件会暂存到系统临时目录下的 `evdp_uploads/`。
- 报告默认保存到被分析数据所在目录。
- 敏感词库位于 `assets/sensitive_words/`，停用词位于 `assets/stopwords/`。
- AI 分析默认只发送统计摘要和抽样评论到用户配置的模型服务，API Key 默认仅在当前会话中使用。

## 项目结构

```text
EVDP/
├── app.py                    # Streamlit 主页
├── pages/                    # 功能页面
├── core/
│   ├── analysis/             # 当前主线分析模块：清洗、情感、IP、用户画像、流水线、报告生成
│   ├── security/             # 安全分析能力模块：异常检测、机器人检测等
│   ├── spider/               # 多平台采集器
│   └── paths.py              # 统一路径管理
├── assets/                   # 字体、敏感词、停用词
├── data/                     # 本地采集数据和导出报告
├── Dockerfile
├── requirements.txt
├── run.sh / run.ps1
└── setup.sh / setup.ps1
```

## 分析说明

EVDP 的风险评分是本地启发式分析结果，用于辅助筛选和演示，不应替代人工判断。当前分析维度包括：

- 情感风险：基于 SnowNLP 或简化词典、敏感词和文本特征。
- IP 地域：统计地域覆盖率、基尼系数、前 3 地域占比和传播模式。
- 用户画像：分析用户评论数量、重复内容、短评占比、时间规律性和等级特征。
- 异常检测：识别评论量突增、地域集中、负面情绪异常、重复刷屏和敏感词集中。
- AI 辅助研判：在本地统计摘要和抽样评论基础上生成自然语言分析，结论仍需人工复核。

## 常见问题

| 问题 | 处理方式 |
| --- | --- |
| `ModuleNotFoundError` | 确认虚拟环境已激活，并重新执行 `pip install -r requirements.txt` |
| Playwright 无法启动浏览器 | 执行 `python -m playwright install chromium` |
| 8501 端口被占用 | 更换端口或关闭占用进程 |
| 中文图表乱码 | 确认 `assets/fonts/simhei.ttf` 存在 |
| 平台登录失效 | 在对应采集页面重新粘贴 Cookie 或扫码登录 |

## 后续计划

- 增加数据库同步页面。
- 增加敏感词库管理页面。
- 增加多文件对比分析能力。
- 优化采集任务状态记录和失败重试。
- 补充更标准的自动化测试。

## 免责声明

本项目仅用于学习研究、数据分析和本地演示。请遵守目标平台服务条款、robots 协议以及相关法律法规，不要用于商业化爬取、绕过访问控制或对平台造成压力的行为。
