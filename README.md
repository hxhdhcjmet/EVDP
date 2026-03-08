


# EVDP (Easy & Visual Data Processor) 🚀

EVDP 是一款以网络爬虫为主，集成化数据处理、分析与采集的工具，旨在为研究人员、开发者及非技术用户提供直观且强大的全栈数据流水线。

---

## 🌟 核心优势

- **全平台爬虫矩阵**：深度适配 **Bilibili、抖音、百度贴吧**，支持多链接并行/顺序采集。
- **极致的爬虫风控**：内置自适应请求延迟、IP 属地伪装及多级并发限制策略，保证采集任务的稳定性。
- **视觉化数据交互**：支持通过**交互式画布**直接点击添加数据点，或一键上传 CSV/Excel 自动导入。
- **平衡性能与使用**：基于cookie登录,初次使用登录一次即可保存登录状态。根据平台严格程度分别采用网页解析、接口获取等不同策略。
- **简易可视化设计**：基于streamlit框架搭建交互式网页,操作、配置简单明了,便于快速开始。
- **高级统计分析**：内置 PCA（主成分分析）、因子分析、聚类分析及多种线性/非线性回归模型，助力深度挖掘数据价值。
- **精美可视化报告**：一键生成词云图、时间分布图、IP 地理分布及情感分析报告。

---

## 🛠️ 快速开始

本章节提供跨平台的部署指南，确保新用户能快速上手。

### 1. 代码获取
使用 Git 克隆仓库或直接下载压缩包：
```bash
# HTTPS 克隆
git clone https://github.com/user/EVDP.git
# 或 SSH 克隆
git clone git@github.com:user/EVDP.git
```

### 2. 分平台配置指南

#### 💻 Windows
1. **环境要求**：Python 3.10+ (建议从 [python.org](https://www.python.org/) 下载)
2. **依赖安装**：
   ```powershell
   python -m venv venv
   .\venv\Scripts\activate
   pip install -r requirements.txt
   playwright install chromium
   ```
3. **配置验证**：
   ```powershell
   streamlit hello  # 验证 Streamlit 基础环境
   ```

#### 🍎 macOS
1. **环境要求**：Python 3.10+ (建议使用 `brew install python@3.10`)
2. **依赖安装**：
   ```bash
   python3 -m venv venv
   source venv/bin/activate
   pip install -r requirements.txt
   playwright install chromium
   ```
3. **配置验证**：
   ```bash
   python3 --version  # 预期输出: Python 3.10.x 或更高
   ```

#### 🐧 Linux
1. **环境要求**：Python 3.10+ 及系统库（如 `libnss3` 用于 Playwright）
2. **依赖安装**：
   ```bash
   # 以 Ubuntu 为例安装系统依赖
   sudo apt-get update && sudo apt-get install -y libnss3 libatk-bridge2.0-0 libxcomposite1
   python3 -m venv venv
   source venv/bin/activate
   pip install -r requirements.txt
   playwright install chromium
   ```
3. **配置验证**：
   ```bash
   pip list | grep streamlit  # 预期输出包含 streamlit 版本信息
   ```

### 3. 配置与启动流程

0. **说明**：
   - 为了平衡项目实现逻辑复杂度和用户使用复杂度，B站、贴吧登录状态通粘贴网页版Cookie实现。抖音登录状态通过用户扫码、输入验证码后，监测Cookie并自动写入实现。其中抖音登录可能无法一次成功，此时可再次尝试，有浏览器弹出，正常扫码登录即可。
   - 所有收集数据，包括爬取到的评论、下载的图片都存放在data文件夹中。

1. **获取身份验证信息 (以 Bilibili 为例)**：

   -  浏览器搜索并登录[bilibili](https://www.bilibili.com/)
   - 按F12打开开发者模式并切换至"网络'标签
   - 搜索（没有可以F5刷新）
   ```text
   www.bilibili.com
   ```
   - 点击第一个，查看标头里Cookie对应字段，将其复制下来，即为启动项目后要粘贴的Cookie。

2. **启动应用**：
   在项目根目录下运行：
   ```bash
   streamlit run app.py
   ```
   **预期输出**：
   ```text
   Local URL: http://localhost:8501
   Network URL: http://192.168.x.x:8501
   ```

### 4. 常见配置错误排查 (FAQ)

| 错误现象 | 可能原因 | 解决方案 |
| :--- | :--- | :--- |
| `ModuleNotFoundError` | 虚拟环境未激活 | 重新执行 `activate` 命令并确认终端前缀有 `(venv)` |
| `Playwright Error` | 浏览器引擎未安装 | 执行 `playwright install chromium` |
| `Port 8501 busy` | 端口被占用 | 运行 `fuser -k 8501/tcp` (Linux) 或重启应用 |
| 字体显示乱码 | 系统缺失中文字体 | 确保安装了 `SimHei` 或参考 `core/visualize.py` 配置 |

---

## 🐳 Docker 部署

如果你希望在容器中运行：
```bash
# 构建镜像
docker build -t evdp-app .

# 运行容器 (映射 8501 端口)
docker run -p 8501:8501 evdp-app
```

---

## 📂 项目结构
```text
/EVDP
├── app.py             # 主入口 (数据处理与拟合)
├── pages/             # 独立功能页面
│   ├── bilibili_page.py
│   ├── douyin_page.py
│   └── tieba_page.py
├── core/              # 核心逻辑库
│   ├── spider/        # 爬虫引擎
│   └── analysis/      # 统计算法
├── assets/            # 静态资源 (字体、样式)
│
└── data/              # 爬取到的评论
```

---

## 📝 后续开发计划

-  1.增加更多主流平台(如知乎、微博、小红书等)的爬虫，获取更丰富的信息
-  2.进一步增加风控能力(开发线程池,提高防封能力,同时提高并发数量,加快爬取速度)
- 3.增加更有用、更深入的数据分析模块。
- ...
---

## ⚠️ 免责声明

本工具仅供学习研究及数据分析使用，严禁用于任何商业目的或对目标平台造成压力的恶意爬取。请自觉遵守各平台的 Robots 协议及相关法律法规。
