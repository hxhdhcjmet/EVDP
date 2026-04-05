# EVDP (Easy & Visual Data Processor) 🚀

EVDP 是一款专注于**舆情安全分析**的全栈数据流水线工具，集成多平台数据采集、清洗、分析与可视化报告导出能力。

---

## 🌟 核心优势

- **全平台爬虫矩阵**：深度适配 **B站、抖音、百度贴吧、知乎**，支持多链接并行/顺序采集。
- **一站式安全分析**：整合情感分析、IP溯源、用户画像、异常检测、风险评估于统一仪表盘。
- **极致的爬虫风控**：内置自适应请求延迟、IP 属地伪装及多级并发限制策略，保证采集稳定性。
- **简易可视化设计**：基于 Streamlit 框架搭建交互式网页，操作简单，文件查看处理明了。
- **精美报告导出**：一键生成词云图、时间分布图、IP 地理分布、情感分析报告，支持 MD/JSON/HTML/TXT 格式导出。

---

## 🛠️ 快速开始

本章节提供跨平台的部署指南，确保新用户能快速上手。

### 1. 代码获取
使用 Git 克隆仓库或直接下载压缩包：
```bash
# HTTPS 克隆
git clone https://github.com/EVDP-ORG/EVDP.git
# 或 SSH 克隆
git clone git@github.com:EVDP-ORG/EVDP.git
```

### 2. 推荐部署方式：Docker（推荐 ✅）

#### Windows
```powershell
# PowerShell 运行
.\run.ps1
```

#### Linux / macOS / WSL
```bash
# Bash 运行
bash ./run.sh
```

> **一行命令自动完成**：检测 Docker → 构建镜像 → 启动容器 → 打印访问地址

#### 手动 Docker 部署
```bash
# 构建镜像
docker build -t evdp .

# 运行容器
docker run -d -p 8501:8501 -v ./data:/home/EVDP/data -v ./assets:/home/EVDP/assets evdp
```

---

### 3. 本地 Python 环境部署

如果不想用 Docker，也可以本地安装：

#### Windows
```powershell
# 创建虚拟环境
python -m venv venv
# 激活
.\venv\Scripts\activate
# 安装依赖
pip install -r requirements.txt
# 安装浏览器
playwright install chromium
# 启动
streamlit run app.py
```

#### Linux / macOS
```bash
# 创建虚拟环境
python3 -m venv venv
# 激活
source venv/bin/activate
# 安装依赖
pip install -r requirements.txt
# 安装浏览器
playwright install chromium
# 启动
streamlit run app.py
```

> 💡 脚本版：直接运行 `setup.sh` / `setup.ps1` 可自动完成以上步骤

---

### 4. 配置与登录

#### Cookie 获取（B站、贴吧）
1. 登录目标平台（bilibili.com / tieba.baidu.com）
2. 按 F12 打开开发者工具 → 切换到 "网络" 标签
3. 刷新页面 → 点击第一个请求 → 复制 Request Headers 中的 Cookie
4. 在对应页面粘贴 Cookie 即可

#### 扫码登录（抖音、知乎）
- 抖音：弹出二维码窗口，扫码后自动保存 Cookie
- 知乎：扫码登录，支持匿名/登录模式

> ⚠️ 所有采集数据存放在 `data/` 目录中

---

## 📂 项目结构
```text
/EVDP
├── app.py                 # 主入口（主页导航）
├── pages/                 # 功能页面（Streamlit 自动发现）
│   ├── 01_bilibili_page   # B站评论采集
│   ├── 02_douyin_page     # 抖音评论采集
│   ├── 03_tieba_page      # 贴吧帖子采集
│   ├── 04_zhihu_page      # 知乎回答采集
│   ├── 05_file_page       # 文件管理
│   ├── 06_security_dashboard  # 舆情安全分析（核心）
│   ├── 07_sentiment_analysis   # 情感分析
│   └── 08_data_cleaning       # 数据清洗
├── core/                  # 核心逻辑库
│   ├── spider/            # 爬虫引擎
│   ├── analysis/          # 统计分析
│   └── security/          # 安全分析模块
├── assets/                # 静态资源（字体、词库、敏感词）
├── data/                  # 采集数据存储
├── run.sh / run.ps1       # Docker 一键启动脚本
├── setup.sh / setup.ps1   # 本地环境安装脚本
├── Dockerfile             # 容器构建文件
└── requirements.txt       # Python 依赖
```

---

## 📊 功能概览

| 模块 | 功能描述 |
|------|----------|
| 数据采集 | 支持 B站、抖音、贴吧、知乎四平台评论/帖子采集 |
| 数据清洗 | 去重、去噪、格式标准化处理 |
| 情感分析 | 正面/负面/中立评论识别，批量处理 |
| IP溯源 | 评论地域分布、基尼系数分析 |
| 用户画像 | 可疑账号识别、机器人检测 |
| 异常检测 | 发现异常行为模式 |
| 风险评估 | 综合评分与风险等级判定 |
| 报告导出 | Markdown / JSON / HTML / TXT 四种格式 |

---
## 界面展示
#### 主界面
<div align="center">
  <img src="https://github.com/hxhdhcjmet/blogimage/blob/main/%E4%B8%BB%E7%95%8C%E9%9D%A2.png?raw=true" width="600">
</div>



#### 文本查看
<div align="center">
  <img src="https://github.com/hxhdhcjmet/blogimage/blob/main/comment.png?raw=true" width="600">
</div>

#### 评论分析
<div align="center">
  <img src="https://raw.githubusercontent.com/hxhdhcjmet/blogimage/7e70420f9b515b4545b0e69d2dba124f741e2ee2/analysize.png" width="600">
</div>

#### 贴吧图片下载查看
<div align="center">
  <img src="https://raw.githubusercontent.com/hxhdhcjmet/blogimage/bd2766e6ea4b5690fd2be08f96f4e7c9c318f215/image_download.png" width="600">
</div>

## 🔧 常见问题排查

| 错误现象 | 可能原因 | 解决方案 |
| :--- | :--- | :--- |
| `ModuleNotFoundError` | 虚拟环境未激活 | 重新执行 `activate` 并确认终端前缀有 `(venv)` |
| `Playwright Error` | 浏览器未安装 | 执行 `playwright install chromium` |
| `Port 8501 busy` | 端口被占用 | Linux: `fuser -k 8501/tcp`，Windows: 检查端口占用 |
| 字体显示乱码 | 缺少中文字体 | 确保 `assets/fonts/` 目录包含 `simhei.ttf` |
| Docker 构建失败 | 网络问题或权限 | 检查 Docker Desktop 是否启动，确保已开启 2375 端口 |

---

## 📝 后续开发计划

- 增加更多主流平台（如微博、小红书）爬虫
- 开发线程池提高防封能力与并发速度
- 增加更多深度数据分析模块
- ...

---

## ⚠️ 免责声明

本工具仅供学习研究及数据分析使用，严禁用于任何商业目的或对目标平台造成压力的恶意爬取。请自觉遵守各平台的 Robots 协议及相关法律法规。