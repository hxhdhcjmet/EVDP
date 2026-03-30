# EVDP 安全分析模块使用指南

## 快速开始

### 1. 基本使用

```python
from core.security import analyze, analyze_dir

# 分析单个文件
result = analyze('/path/to/comments.jsonl')

# 分析整个目录
result = analyze_dir('/path/to/data/')

# 查看风险评分
print(f"风险评分: {result['risk_result']['overall_score']}/100")
print(f"风险等级: {result['risk_result']['risk_level']}")

# 查看报告
print(result['report'])

# 保存报告
with open('security_report.md', 'w', encoding='utf-8') as f:
    f.write(result['report'])
```

### 2. 高级使用

```python
from core.security import SecurityAnalyzer

# 创建分析器实例
analyzer = SecurityAnalyzer()

# 自定义参数
result = analyzer.analyze_file(
    file_path='/path/to/comments.jsonl',
    platform='bilibili',  # 可选,自动检测
    generate_report=True  # 是否生成报告
)

# 访问详细结果
comments = result['comments']              # 评论列表
sentiment = result['sentiment_results']   # 情感分析
bot_detection = result['bot_results']      # 机器人检测
anomaly = result['anomaly_results']        # 异常检测
topic = result['topic_result']             # 话题分析
risk = result['risk_result']               # 风险评估
report = result['report']                  # Markdown 报告
report_json = result['report_json']        # JSON 格式报告
```

## 支持的平台

- **B站 (bilibili)**: 自动检测 `bili_` 开头的文件
- **贴吧 (tieba)**: 自动检测 `tid_` 开头的文件
- **知乎 (zhihu)**: 自动检测包含 `zhihu` 的文件
- **抖音 (douyin)**: 自动检测包含 `douyin` 的文件

## 数据格式要求

### B站评论格式

```json
{
  "comment": "评论内容",
  "like": 7,
  "reply_count": 0,
  "ctime": 1771303006,
  "user": {
    "name": "用户名",
    "level": 3,
    "ip": "IP属地：安徽"
  },
  "replies": []
}
```

### 贴吧评论格式

```json
{
  "pid": 144540649992,
  "floor": 1,
  "user_id": 3506977221,
  "author": "用户名",
  "ip_location": "山东",
  "content": "评论内容",
  "time": "2022-06-24 11:11"
}
```

## 输出说明

### 风险等级

- **critical** (80-100): 严重风险,需要立即干预
- **high** (60-79): 高风险,需要重点关注
- **medium** (40-59): 中等风险,需要持续监测
- **low** (0-39): 低风险,正常监测即可

### 风险维度

- **情感风险**: 基于负面情感比例和敏感词
- **账号风险**: 基于可疑账号和机器人检测
- **行为风险**: 基于异常行为模式
- **内容风险**: 基于内容重复度和敏感词

### 预警类型

- **volume_spike**: 评论量突增
- **negative_sentiment_spike**: 负面情感突增
- **location_concentration**: 地域集中异常
- **content_duplication**: 内容重复刷屏
- **sensitive_keyword_concentration**: 敏感词集中

## 示例输出

```
风险评分: 14/100
风险等级: low

预警信息:

建议措施:
  - 保持正常监测

情感分布:
  正面: 20 (6.3%)
  负面: 6 (1.9%)
  中立: 292 (91.8%)

机器人检测:
  总用户数: 2
  高风险账号: 0 (0.0%)

异常检测:
  异常总数: 2
  - volume_spike: 评论量突增
  - spam_short_content: 短评论刷屏
```

## 安装依赖

```bash
pip install snownlp jieba pandas
```

## 注意事项

1. **首次使用**: 需要安装 SnowNLP 和 jieba 用于情感分析和分词
2. **性能**: 大数据集 (>10000 条) 建议分批处理
3. **平台适配**: 不同平台的评论格式会自动标准化
4. **敏感词库**: 可以在 `sentiment_analyzer.py` 中自定义敏感词列表

## 文件结构

```
core/security/
├── __init__.py              # 模块入口
├── data_normalizer.py       # 数据标准化
├── sentiment_analyzer.py    # 情感分析
├── bot_detector.py          # 机器人检测
├── anomaly_detector.py      # 异常检测
├── risk_assessment.py       # 风险评估
├── topic_analyzer.py        # 话题分析
├── report_generator.py      # 报告生成
├── security_analyzer.py     # 综合分析器
└── test_security.py         # 测试脚本
```

## 后续开发计划

- [ ] 集成到 Streamlit UI
- [ ] 添加实时监测功能
- [ ] 支持更多平台 (小红书、微博等)
- [ ] 增强 LLM 驱动的分析能力
- [ ] 添加可视化仪表板
