"""
综合风险评估模块
整合多个分析维度,生成综合风险评分
"""

from typing import List, Dict, Optional
from dataclasses import dataclass
import logging

logger = logging.getLogger(__name__)


@dataclass
class RiskAssessmentResult:
    """风险评估结果"""
    overall_score: int           # 综合风险评分 0-100
    risk_level: str              # low/medium/high/critical
    
    # 各维度评分
    sentiment_risk: int          # 情感风险
    account_risk: int            # 账号风险
    behavior_risk: int           # 行为风险
    content_risk: int            # 内容风险
    
    # 趋势和预警
    trend: str                   # increasing/stable/decreasing
    warnings: List[str]          # 预警信息
    recommendations: List[str]   # 建议措施
    
    # 详细数据
    details: Dict


class RiskAssessment:
    """综合风险评估器"""
    
    # 权重配置
    WEIGHTS = {
        'sentiment': 0.30,  # 情感风险权重
        'account': 0.25,    # 账号风险权重
        'behavior': 0.25,   # 行为风险权重
        'content': 0.20     # 内容风险权重
    }
    
    def __init__(self):
        pass
    
    def assess(self,
               sentiment_summary: Dict,
               bot_summary: Dict,
               anomaly_summary: Dict,
               total_comments: int) -> RiskAssessmentResult:
        """
        综合评估
        
        Args:
            sentiment_summary: 情感分析摘要
            bot_summary: 机器人检测摘要
            anomaly_summary: 异常检测摘要
            total_comments: 总评论数
        
        Returns:
            RiskAssessmentResult
        """
        # 1. 计算各维度风险
        sentiment_risk = self._calculate_sentiment_risk(sentiment_summary)
        account_risk = self._calculate_account_risk(bot_summary)
        behavior_risk = self._calculate_behavior_risk(anomaly_summary)
        content_risk = self._calculate_content_risk(sentiment_summary, anomaly_summary)
        
        # 2. 计算综合风险 (加权平均)
        overall_score = int(
            sentiment_risk * self.WEIGHTS['sentiment'] +
            account_risk * self.WEIGHTS['account'] +
            behavior_risk * self.WEIGHTS['behavior'] +
            content_risk * self.WEIGHTS['content']
        )
        
        # 3. 确定风险等级
        risk_level = self._determine_risk_level(overall_score)
        
        # 4. 生成预警信息
        warnings = self._generate_warnings(
            sentiment_risk, account_risk, 
            behavior_risk, content_risk,
            sentiment_summary, bot_summary, anomaly_summary
        )
        
        # 5. 生成建议
        recommendations = self._generate_recommendations(
            overall_score, risk_level, warnings
        )
        
        return RiskAssessmentResult(
            overall_score=overall_score,
            risk_level=risk_level,
            sentiment_risk=sentiment_risk,
            account_risk=account_risk,
            behavior_risk=behavior_risk,
            content_risk=content_risk,
            trend='stable',  # 需要历史数据才能判断趋势
            warnings=warnings,
            recommendations=recommendations,
            details={
                'sentiment_summary': sentiment_summary,
                'bot_summary': bot_summary,
                'anomaly_summary': anomaly_summary,
                'total_comments': total_comments
            }
        )
    
    def _calculate_sentiment_risk(self, summary: Dict) -> int:
        """计算情感风险评分"""
        if not summary:
            return 0
        
        score = 0
        
        # 负面情感比例
        negative_ratio = summary.get('negative_ratio', 0)
        if negative_ratio > 0.7:
            score += 40
        elif negative_ratio > 0.5:
            score += 30
        elif negative_ratio > 0.3:
            score += 20
        
        # 平均风险评分
        avg_risk = summary.get('avg_risk_score', 0)
        score += int(avg_risk * 0.6)
        
        return min(score, 100)
    
    def _calculate_account_risk(self, summary: Dict) -> int:
        """计算账号风险评分"""
        if not summary:
            return 0
        
        score = 0
        
        # 高风险账号比例
        high_risk_ratio = summary.get('high_risk_ratio', 0)
        if high_risk_ratio > 0.1:
            score += 50
        elif high_risk_ratio > 0.05:
            score += 30
        elif high_risk_ratio > 0.01:
            score += 15
        
        # 平均风险评分
        avg_risk = summary.get('avg_risk_score', 0)
        score += int(avg_risk * 0.5)
        
        return min(score, 100)
    
    def _calculate_behavior_risk(self, summary: Dict) -> int:
        """计算行为风险评分"""
        if not summary:
            return 0
        
        score = 0
        
        # 异常数量
        total_anomalies = summary.get('total_anomalies', 0)
        critical = summary.get('critical', 0)
        high = summary.get('high', 0)
        
        if critical > 0:
            score += 50
        if high > 2:
            score += 30
        elif high > 0:
            score += 20
        
        # 异常类型数量
        anomaly_types = summary.get('anomaly_types', [])
        score += min(len(anomaly_types) * 10, 30)
        
        return min(score, 100)
    
    def _calculate_content_risk(self, sentiment_summary: Dict, anomaly_summary: Dict) -> int:
        """计算内容风险评分"""
        score = 0
        
        # 基于情感和异常综合判断
        if sentiment_summary:
            # 高风险内容比例
            pass  # 这里可以根据实际需求调整
        
        if anomaly_summary:
            # 内容重复异常
            anomaly_types = anomaly_summary.get('anomaly_types', [])
            if 'content_duplication' in anomaly_types:
                score += 30
            if 'sensitive_keyword_concentration' in anomaly_types:
                score += 25
            if 'spam_short_content' in anomaly_types:
                score += 20
        
        return min(score, 100)
    
    def _determine_risk_level(self, score: int) -> str:
        """确定风险等级"""
        if score >= 80:
            return 'critical'
        elif score >= 60:
            return 'high'
        elif score >= 40:
            return 'medium'
        else:
            return 'low'
    
    def _generate_warnings(self, 
                          sentiment_risk: int,
                          account_risk: int,
                          behavior_risk: int,
                          content_risk: int,
                          sentiment_summary: Dict,
                          bot_summary: Dict,
                          anomaly_summary: Dict) -> List[str]:
        """生成预警信息"""
        warnings = []
        
        # 情感预警
        if sentiment_risk > 60:
            negative_ratio = sentiment_summary.get('negative_ratio', 0)
            warnings.append(f"负面情绪占比过高 ({negative_ratio:.1%})")
        
        # 账号预警
        if account_risk > 50:
            high_risk = bot_summary.get('high_risk', 0)
            warnings.append(f"检测到 {high_risk} 个高风险账号")
        
        # 行为预警
        if behavior_risk > 50:
            critical = anomaly_summary.get('critical', 0)
            high = anomaly_summary.get('high', 0)
            if critical > 0:
                warnings.append(f"发现 {critical} 个严重异常")
            if high > 0:
                warnings.append(f"发现 {high} 个高危异常")
        
        # 内容预警
        if content_risk > 40:
            anomaly_types = anomaly_summary.get('anomaly_types', [])
            if 'content_duplication' in anomaly_types:
                warnings.append("存在内容重复刷屏行为")
            if 'sensitive_keyword_concentration' in anomaly_types:
                warnings.append("敏感词出现频率异常")
        
        return warnings
    
    def _generate_recommendations(self,
                                  overall_score: int,
                                  risk_level: str,
                                  warnings: List[str]) -> List[str]:
        """生成建议措施"""
        recommendations = []
        
        if risk_level == 'critical':
            recommendations.append("立即启动人工审核流程")
            recommendations.append("重点关注并标记高风险内容")
            recommendations.append("考虑限制高风险账号的发言权限")
        
        elif risk_level == 'high':
            recommendations.append("加强内容审核力度")
            recommendations.append("标记并跟踪高风险账号")
            recommendations.append("准备舆情应对预案")
        
        elif risk_level == 'medium':
            recommendations.append("持续监测舆情动态")
            recommendations.append("关注异常行为模式")
        
        else:
            recommendations.append("保持正常监测")
        
        # 根据具体警告添加针对性建议
        if "负面情绪占比过高" in warnings:
            recommendations.append("分析负面情绪来源,考虑正面引导")
        
        if "检测到" in str(warnings) and "高风险账号" in str(warnings):
            recommendations.append("核查高风险账号的真实性")
        
        return recommendations
