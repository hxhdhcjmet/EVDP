# EVDP项目状态报告

## 项目概述
EVDP（Easy and Visually Achieve Data Process）是一个数据处理和可视化项目，旨在提供简单易用的数据处理工具。

## 项目结构
```
/home/EVDP/
├── core/                      # 核心功能模块
│   ├── spider/               # 爬虫模块
│   │   ├── media.py          # 百度贴吧图片爬虫（已完成）
│   │   ├── weather.py        # 天气数据爬虫
│   │   ├── airQuality.py     # 空气质量数据爬虫
│   │   ├── movieTop250.py    # 电影Top250爬虫
│   │   └── utils.py          # 爬虫工具函数
│   ├── PreProcessing.py      # 数据预处理模块
│   ├── visualize.py          # 数据可视化模块
│   ├── predict.py            # 预测模块（单元回归、插值）
│   ├── MultiRegression.py    # 多元回归模块（线性、PLS、Ridge）
│   ├── PCAAnalyzer.py        # 主成分分析模块
│   ├── FactorAnalyzer.py     # 因子分析模块（简化版）
│   └── ClusterAnalyzer.py    # 聚类分析模块（KMeans/层次/DBSCAN）
│   └── watermark_utils.py    # 水印工具模块
├── pages/                    # 页面模块
│   └── visualize.py          # 可视化页面
├── image/                    # 图片存储目录
├── icon/                     # 图标资源
├── app.py                    # 应用入口
├── requirements.txt          # 依赖清单
└── README.md                 # 项目说明文档
```

## 已完成功能

### 1. 百度贴吧图片爬虫（media.py）
- ✅ 使用requests和BeautifulSoup实现页面爬取
- ✅ 支持指定帖子URL和爬取页数
- ✅ 自动提取帖子信息（用户ID、用户名、内容、时间等）
- ✅ 支持下载帖子中的图片
- ✅ 实现JSON/CSV/SQLite三种数据格式保存
- ✅ 处理404页面和反爬限制
- ✅ 使用Cookie认证访问页面

### 2. 其他爬虫模块
- ✅ 天气数据爬虫（weather.py）
- ✅ 空气质量数据爬虫（airQuality.py）
- ✅ 电影Top250爬虫（movieTop250.py）

### 3. 数据处理功能
- ✅ 数据预处理（PreProcessing.py）
- ✅ 数据可视化（visualize.py）
- ✅ 单元回归与插值（predict.py）
- ✅ 多元回归（MultiRegression.py）：线性回归、PLS、Ridge，含指标与可视化
- ✅ PCA 主成分分析（PCAAnalyzer.py）：方差贡献率、双标图
- ✅ 因子分析（FactorAnalyzer.py）：载荷热图（简化实现）
- ✅ 聚类分析（ClusterAnalyzer.py）：KMeans、层次聚类、DBSCAN 及散点可视化
- ✅ 水印处理（watermark_utils.py）

## 优缺点分析

### 优点
1. **模块化设计**：功能模块分离清晰，便于维护和扩展
2. **多格式支持**：数据保存支持JSON、CSV和SQLite多种格式
3. **多种数据源**：集成了贴吧、天气、空气质量和电影等多种数据源
4. **可视化支持**：提供数据可视化功能，便于数据分析

### 缺点
1. **文档不足**：README.md内容简单，缺乏详细的使用说明和API文档
2. **模块整合**：各功能模块之间的整合不够紧密，缺乏统一的用户界面
3. **配置管理**：缺乏统一的配置文件，参数设置分散在代码中
4. **爬虫维护**：爬虫模块需要定期维护以应对网站结构变化
5. **测试覆盖**：缺乏单元测试和集成测试，代码质量难以保证

## 待办事项（Todo List）

### 1. 文档完善
- [ ] 编写详细的README.md，包含项目介绍、安装说明、使用示例
- [ ] 为每个模块编写API文档
- [ ] 创建用户手册和教程

### 2. 功能优化
- [ ] 实现统一的用户界面，整合各功能模块
- [ ] 添加配置文件支持，集中管理参数设置
- [ ] 优化数据处理算法，提高处理效率
- [ ] 增强可视化功能，支持更多图表类型

### 3. 测试与质量
- [ ] 为核心功能编写单元测试
- [ ] 添加集成测试，确保模块间的协同工作
- [ ] 进行性能测试，优化代码效率
- [ ] 进行代码审查，提高代码质量

### 4. 爬虫维护
- [ ] 定期检查和更新各爬虫模块，应对网站结构变化
- [ ] 增强反爬机制处理能力
- [ ] 添加爬虫任务调度功能

### 5. 新功能开发
- [ ] 支持更多数据源的爬取
- [ ] 实现数据清洗和转换功能
- [ ] 添加数据导出功能
- [ ] 支持批量处理功能

## 技术栈
- **编程语言**：Python
- **Web框架**：Streamlit
- **爬虫库**：requests, BeautifulSoup
- **数据处理**：pandas, numpy
- **可视化**：matplotlib, seaborn（推测）
- **数据库**：SQLite

## 使用示例

### 百度贴吧图片爬虫
```python
from core.spider.media import tieba_crawl_all

# 爬取指定帖子的图片和信息
url = "https://tieba.baidu.com/p/8419121896"
tieba_crawl_all(url, max_pages=5)  # 爬取5页内容
```

## 最近更新（2025-12-06）

- 统一爬虫模块导入：兼容两种运行方式，模块运行与直接脚本运行均可。
  - 模块运行（推荐）：在项目根目录执行 `python -m core.spider.media`、`python -m core.spider.airQuality`、`python -m core.spider.movieTop250`
  - 直接脚本运行：`python /home/EVDP/core/spider/media.py` 等也可正常执行
- 图片命名策略优化：依据响应 `Content-Type`/URL 扩展名 + 时间戳 + 内容 MD5 前缀，避免同名覆盖与重复下载（实现位置：`core/spider/utils.py` 的 `get_image_name`）
- 空气质量 Token 配置：支持通过环境变量覆盖，设置 `WAQI_TOKEN` 可替换默认值（实现位置：`core/spider/airQuality.py`）
- 依赖精简：移除 `movieTop250.py` 未使用的 `parsel` 依赖，保证直接可运行
- 输出目录统一：所有爬虫数据输出至 `/home/EVDP/data/...`，与项目规范保持一致

### Streamlit 集成与高级分析新增（2025-12-07）
- 新增分析模块文件：`core/PCAAnalyzer.py`、`core/FactorAnalyzer.py`、`core/ClusterAnalyzer.py`
- 在 `app.py` 集成“7. 高级分析”分区，支持：
  - PCA 主成分分析：方差贡献率表、柱状图与双标图（修复 Slider 边界问题：仅在选择≥2列时渲染成分数控件）
  - 因子分析：因子载荷热图（修复 Slider 边界问题：仅在选择≥2列时渲染因子数控件）
  - 聚类分析：KMeans、层次聚类、DBSCAN 与二维散点可视化（参数控件提前渲染，按钮回调稳定取值）
- 单元回归与插值适配：
  - `core/predict.py` 移除交互输入，使用 UI 设置的 `degree`；插值前对 `x` 排序并生成 `new_x`
  - `app.py` 单元回归初始化仅接受单列 `Series` 作为 `x_col`，避免 `DataFrame` 引发插值错误
- 修复 `app.py` 语法缩进错误：拟合区 `try/except` 与指标展示缩进一致，避免编译错误

### 交互与可视化改进（2025-12-09）
- 三步交互流程上线：
  - 步骤一（数据加载）：进度指示与10秒超时读取（`core/ui_utils.py:load_file_with_timeout`），在 `app.py` 中展示加载状态
  - 步骤二（清洗决策）：模态/单选确认清洗；显示质量评估报告（缺失统计与异常值检测，`core/ui_utils.py:quality_report`）
  - 步骤三（分析选项）：插值/拟合/PCA 条件渲染与互斥/依赖校验（`core/ui_utils.py:validate_mutual_exclusive`、`validate_dependencies`）
- 可视化中文显示统一：
  - 全局字体自动选择：Windows 使用 `SimHei`，macOS 使用 `PingFang SC`，其他平台使用 `DejaVu Sans`（`core/visualize.py:apply_global_style`）
  - 字号分级：标题14pt/轴标签12pt/图例10pt；图例弹性布局并限制最大宽度40%，长文本自动换行（`core/visualize.py:wrap_text`、`apply_legend_style`）
  - 响应式布局：统一 `tight_layout` 封装（`core/visualize.py:responsive_tight_layout`）
- 模块适配：
  - PCA、聚类、PLS 绘图均采用统一样式与文本换行（`core/PCAAnalyzer.py`、`core/ClusterAnalyzer.py`、`core/MultiRegression.py`）
- 测试补充：
  - 新增 `tests/test_ui_utils.py` 覆盖文件加载、质量评估与互斥/依赖校验逻辑

### 命令行运行示例
- 贴吧爬虫：`python -m core.spider.media`
- 空气质量爬虫：`python -m core.spider.airQuality`
- 电影 Top250：`python -m core.spider.movieTop250`

## 后续计划
1. 优先完善文档和测试
2. 实现统一的用户界面
3. 优化现有功能，提高稳定性和性能
4. 开发新功能，扩展项目能力
5. 建立定期维护机制，特别是爬虫模块

### 注意事项
- PCA/因子分析的成分数与因子数需基于已选特征列数量动态限定，避免 Slider 边界异常
- 单元回归时必须选择一个且仅一个自变量；否则不初始化 `DataPredict`
- 聚类参数控件需在按钮之前渲染，以确保回调中能正确读取参数值

### 待办
- 将高级分析图形统一接入 `pages/visualize.py` 的下载管线
- 多元回归区添加“特征重要性”图按钮（调用 `core/MultiRegression.py:185`）

## 联系方式
（待补充）
