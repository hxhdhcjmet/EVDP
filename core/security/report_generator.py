"""
报告生成模块
生成专业的安全分析报告
"""

from typing import List, Dict, Optional
from datetime import datetime
from dataclasses import dataclass
import json
import logging

logger = logging.getLogger(__name__)


@dataclass
class Report:
    """安全分析报告"""
    report_id: str
    generated_at: datetime
    data_source: str
    time_range: Dict
    
    # 基本统计
    total_comments: int
    platform: str
    
    # 风险评估
    overall_risk_score: int
    risk_level: str
    risk_breakdown: Dict
    
    # 详细分析
    sentiment_analysis: Dict
    bot_detection: Dict
    anomaly_detection: Dict
    topic_analysis: Dict
    
    # 预警和建议
    warnings: List[str]
    recommendations: List[str]
    
    # 附录
    high_risk_accounts: List[Dict]
    sensitive_content: List[Dict]


class ReportGenerator:
    """报告生成器"""
    
    def __init__(self):
        pass
    
    def generate(self,
                 data_source: str,
                 time_range: Dict,
                 platform: str,
                 total_comments: int,
                 risk_assessment,
                 sentiment_results: List[Dict],
                 bot_results: Dict,
                 anomaly_results: List,
                 topic_result) -> Report:
        """
        生成报告
        
        Args:
            data_source: 数据源
            time_range: 时间范围
            platform: 平台
            total_comments: 总评论数
            risk_assessment: 风险评估结果
            sentiment_results: 情感分析结果
            bot_results: 机器人检测结果
            anomaly_results: 异常检测结果
            topic_result: 话题分析结果
        
        Returns:
            Report
        """
        # 生成报告ID
        report_id = f"RPT_{datetime.now().strftime('%Y%m%d%H%M%S')}"
        
        # 整合情感分析
        sentiment_analysis = self._summarize_sentiment(sentiment_results)
        
        # 整合机器人检测
        bot_detection = self._summarize_bot_detection(bot_results)
        
        # 整合异常检测
        anomaly_detection = self._summarize_anomaly(anomaly_results)
        
        # 整合话题分析
        topic_analysis = self._summarize_topic(topic_result)
        
        # 提取高风险账号
        high_risk_accounts = self._extract_high_risk_accounts(bot_results)
        
        # 提取敏感内容
        sensitive_content = self._extract_sensitive_content(sentiment_results)
        
        return Report(
            report_id=report_id,
            generated_at=datetime.now(),
            data_source=data_source,
            time_range=time_range,
            total_comments=total_comments,
            platform=platform,
            overall_risk_score=risk_assessment.overall_score,
            risk_level=risk_assessment.risk_level,
            risk_breakdown={
                'sentiment_risk': risk_assessment.sentiment_risk,
                'account_risk': risk_assessment.account_risk,
                'behavior_risk': risk_assessment.behavior_risk,
                'content_risk': risk_assessment.content_risk
            },
            sentiment_analysis=sentiment_analysis,
            bot_detection=bot_detection,
            anomaly_detection=anomaly_detection,
            topic_analysis=topic_analysis,
            warnings=risk_assessment.warnings,
            recommendations=risk_assessment.recommendations,
            high_risk_accounts=high_risk_accounts,
            sensitive_content=sensitive_content
        )
    
    def _summarize_sentiment(self, results: List[Dict]) -> Dict:
        """总结情感分析"""
        if not results:
            return {}
        
        total = len(results)
        positive = sum(1 for r in results if r.get('sentiment') == 'positive')
        negative = sum(1 for r in results if r.get('sentiment') == 'negative')
        neutral = sum(1 for r in results if r.get('sentiment') == 'neutral')
        
        avg_score = sum(r.get('score', 0.5) for r in results) / total
        avg_risk = sum(r.get('risk_score', 0) for r in results) / total
        
        return {
            'total': total,
            'positive': positive,
            'positive_ratio': positive / total,
            'negative': negative,
            'negative_ratio': negative / total,
            'neutral': neutral,
            'neutral_ratio': neutral / total,
            'avg_sentiment_score': avg_score,
            'avg_risk_score': avg_risk
        }
    
    def _summarize_bot_detection(self, results: Dict) -> Dict:
        """总结机器人检测"""
        if not results:
            return {}
        
        total = len(results)
        high_risk = sum(1 for r in results.values() if r.risk_level == 'high')
        medium_risk = sum(1 for r in results.values() if r.risk_level == 'medium')
        low_risk = sum(1 for r in results.values() if r.risk_level == 'low')
        
        avg_risk = sum(r.overall_risk_score for r in results.values()) / total
        
        return {
            'total_users': total,
            'high_risk': high_risk,
            'medium_risk': medium_risk,
            'low_risk': low_risk,
            'avg_risk_score': avg_risk
        }
    
    def _summarize_anomaly(self, results: List) -> Dict:
        """总结异常检测"""
        if not results:
            return {}
        
        from collections import Counter
        severity_counts = Counter(r.severity for r in results)
        type_counts = Counter(r.anomaly_type for r in results)
        
        return {
            'total_anomalies': len(results),
            'severity_distribution': dict(severity_counts),
            'type_distribution': dict(type_counts)
        }
    
    def _summarize_topic(self, result) -> Dict:
        """总结话题分析"""
        if not result:
            return {}
        
        return {
            'top_keywords': result.top_keywords[:10],
            'orientation': result.sentiment_orientation.get('orientation_label', '未知'),
            'trending_score': result.trending_score,
            'sensitive_keywords_count': len(result.sensitive_keywords)
        }
    
    def _extract_high_risk_accounts(self, bot_results: Dict) -> List[Dict]:
        """提取高风险账号"""
        high_risk = []
        
        for user_id, result in bot_results.items():
            if result.risk_level in ['high', 'critical']:
                high_risk.append({
                    'user_id': user_id,
                    'user_name': result.user_name,
                    'risk_score': result.overall_risk_score,
                    'risk_level': result.risk_level,
                    'total_comments': result.total_comments,
                    'reasons': result.reasons
                })
        
        # 按风险评分排序
        high_risk.sort(key=lambda x: x['risk_score'], reverse=True)
        return high_risk[:20]  # 最多返回20个
    
    def _extract_sensitive_content(self, sentiment_results: List[Dict]) -> List[Dict]:
        """提取敏感内容"""
        sensitive = []
        
        for idx, result in enumerate(sentiment_results):
            if result.get('risk_score', 0) >= 60:
                sensitive.append({
                    'index': idx,
                    'content': result.get('content', '')[:100],  # 截断
                    'risk_score': result.get('risk_score', 0),
                    'sensitive_words': result.get('sensitive_words', [])
                })
        
        # 按风险评分排序
        sensitive.sort(key=lambda x: x['risk_score'], reverse=True)
        return sensitive[:50]  # 最多返回50条
    
    def to_markdown(self, report: Report) -> str:
        """转换为 Markdown 格式"""
        md = f"""# EVDP 安全监测报告

**报告ID**: {report.report_id}  
**生成时间**: {report.generated_at.strftime('%Y-%m-%d %H:%M:%S')}  
**数据源**: {report.data_source}  
**平台**: {report.platform}  

---

## 📊 基本统计

- **总评论数**: {report.total_comments}
- **时间范围**: {report.time_range.get('start', '未知')} ~ {report.time_range.get('end', '未知')}

---

## 🔒 风险评估

### 总体风险

- **风险评分**: {report.overall_risk_score}/100
- **风险等级**: {self._risk_level_emoji(report.risk_level)} {report.risk_level.upper()}

### 风险分解

| 维度 | 评分 | 说明 |
|------|------|------|
| 情感风险 | {report.risk_breakdown.get('sentiment_risk', 0)}/100 | 基于负面情感比例 |
| 账号风险 | {report.risk_breakdown.get('account_risk', 0)}/100 | 基于可疑账号比例 |
| 行为风险 | {report.risk_breakdown.get('behavior_risk', 0)}/100 | 基于异常行为检测 |
| 内容风险 | {report.risk_breakdown.get('content_risk', 0)}/100 | 基于敏感词检测 |

---

## 📈 情感分析

- **正面情感**: {report.sentiment_analysis.get('positive', 0)} ({report.sentiment_analysis.get('positive_ratio', 0):.1%})
- **负面情感**: {report.sentiment_analysis.get('negative', 0)} ({report.sentiment_analysis.get('negative_ratio', 0):.1%})
- **中立情感**: {report.sentiment_analysis.get('neutral', 0)} ({report.sentiment_analysis.get('neutral_ratio', 0):.1%})
- **平均风险评分**: {report.sentiment_analysis.get('avg_risk_score', 0):.1f}/100

---

## 🤖 机器人检测

- **总用户数**: {report.bot_detection.get('total_users', 0)}
- **高风险账号**: {report.bot_detection.get('high_risk', 0)} ({report.bot_detection.get('high_risk', 0)/max(report.bot_detection.get('total_users', 1), 1):.1%})
- **中风险账号**: {report.bot_detection.get('medium_risk', 0)}
- **低风险账号**: {report.bot_detection.get('low_risk', 0)}

---

## ⚠️ 异常检测

- **异常总数**: {report.anomaly_detection.get('total_anomalies', 0)}
- **严重程度分布**: {report.anomaly_detection.get('severity_distribution', {})}
- **异常类型**: {list(report.anomaly_detection.get('type_distribution', {}).keys())}

---

## 📋 话题分析

- **舆论导向**: {report.topic_analysis.get('orientation', '未知')}
- **热度评分**: {report.topic_analysis.get('trending_score', 0):.1f}/100
- **敏感关键词数**: {report.topic_analysis.get('sensitive_keywords_count', 0)}

**热门关键词**:
{self._format_keywords(report.topic_analysis.get('top_keywords', []))}

---

## 🚨 预警信息

"""
        for idx, warning in enumerate(report.warnings, 1):
            md += f"{idx}. {warning}\n"
        
        md += "\n---\n\n## 💡 建议措施\n\n"
        for idx, rec in enumerate(report.recommendations, 1):
            md += f"{idx}. {rec}\n"
        
        md += "\n---\n\n## 📎 附录\n\n"
        md += f"### 高风险账号 (前 {len(report.high_risk_accounts)} 个)\n\n"
        
        for idx, account in enumerate(report.high_risk_accounts[:10], 1):
            md += f"{idx}. **{account['user_name']}** (风险: {account['risk_score']}/100)\n"
            md += f"   - 评论数: {account['total_comments']}\n"
            md += f"   - 理由: {', '.join(account['reasons'])}\n\n"
        
        md += f"\n### 敏感内容 (前 {len(report.sensitive_content)} 条)\n\n"
        
        for idx, content in enumerate(report.sensitive_content[:10], 1):
            md += f"{idx}. 风险 {content['risk_score']}/100: \"{content['content'][:50]}...\"\n"
        
        md += f"\n---\n\n**报告生成完毕** | EVDP 安全监测平台\n"
        
        return md
    
    def _risk_level_emoji(self, level: str) -> str:
        """获取风险等级 emoji"""
        emojis = {
            'low': '🟢',
            'medium': '🟡',
            'high': '🔴',
            'critical': '💀'
        }
        return emojis.get(level, '⚪')
    
    def _format_keywords(self, keywords: List[tuple]) -> str:
        """格式化关键词列表"""
        if not keywords:
            return "无"
        
        lines = []
        for keyword, weight in keywords[:10]:
            if isinstance(weight, float):
                lines.append(f"- **{keyword}**: {weight:.2f}")
            else:
                lines.append(f"- **{keyword}**: {weight}")
        
        return '\n'.join(lines)
    
    def to_json(self, report: Report) -> str:
        """转换为 JSON 格式"""
        data = {
            'report_id': report.report_id,
            'generated_at': report.generated_at.isoformat(),
            'data_source': report.data_source,
            'time_range': report.time_range,
            'total_comments': report.total_comments,
            'platform': report.platform,
            'overall_risk_score': report.overall_risk_score,
            'risk_level': report.risk_level,
            'risk_breakdown': report.risk_breakdown,
            'sentiment_analysis': report.sentiment_analysis,
            'bot_detection': report.bot_detection,
            'anomaly_detection': report.anomaly_detection,
            'topic_analysis': report.topic_analysis,
            'warnings': report.warnings,
            'recommendations': report.recommendations,
            'high_risk_accounts': report.high_risk_accounts,
            'sensitive_content': report.sensitive_content
        }
        
        return json.dumps(data, ensure_ascii=False, indent=2)
