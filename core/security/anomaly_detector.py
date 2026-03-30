"""
异常检测模块
检测评论数据中的异常行为和模式
"""

import re
from typing import List, Dict, Optional
from dataclasses import dataclass
from collections import Counter, defaultdict
from datetime import datetime, timedelta
import logging

logger = logging.getLogger(__name__)


@dataclass
class AnomalyResult:
    """异常检测结果"""
    anomaly_type: str          # 异常类型
    severity: str              # 严重程度: low/medium/high/critical
    score: int                 # 异常评分 0-100
    description: str           # 描述
    affected_count: int        # 影响数量
    time_window: Optional[str] = None  # 时间窗口
    details: Optional[Dict] = None     # 详细信息


class AnomalyDetector:
    """异常检测器"""
    
    def __init__(self, 
                 volume_spike_threshold: float = 3.0,  # 评论量突增阈值 (倍数)
                 negative_ratio_threshold: float = 0.7): # 负面比例阈值
        """
        初始化
        
        Args:
            volume_spike_threshold: 评论量突增阈值
            negative_ratio_threshold: 负面情感比例阈值
        """
        self.volume_spike_threshold = volume_spike_threshold
        self.negative_ratio_threshold = negative_ratio_threshold
    
    def detect(self, 
               comments: List[Dict], 
               sentiment_results: List[Dict] = None) -> List[AnomalyResult]:
        """
        检测异常
        
        Args:
            comments: 评论列表
            sentiment_results: 情感分析结果 (可选)
        
        Returns:
            异常结果列表
        """
        anomalies = []
        
        # 1. 时间异常检测
        time_anomalies = self._detect_time_anomalies(comments)
        anomalies.extend(time_anomalies)
        
        # 2. 地域异常检测
        location_anomalies = self._detect_location_anomalies(comments)
        anomalies.extend(location_anomalies)
        
        # 3. 情感异常检测
        if sentiment_results:
            sentiment_anomalies = self._detect_sentiment_anomalies(sentiment_results)
            anomalies.extend(sentiment_anomalies)
        
        # 4. 内容异常检测
        content_anomalies = self._detect_content_anomalies(comments)
        anomalies.extend(content_anomalies)
        
        # 按严重程度排序
        severity_order = {'critical': 0, 'high': 1, 'medium': 2, 'low': 3}
        anomalies.sort(key=lambda x: severity_order.get(x.severity, 4))
        
        return anomalies
    
    def _detect_time_anomalies(self, comments: List[Dict]) -> List[AnomalyResult]:
        """检测时间异常"""
        anomalies = []
        
        # 按小时分组
        hour_counts = defaultdict(int)
        for comment in comments:
            publish_time = comment.get('publish_time')
            if publish_time:
                if isinstance(publish_time, str):
                    try:
                        publish_time = datetime.fromisoformat(publish_time)
                    except:
                        continue
                hour_key = publish_time.strftime('%Y-%m-%d %H:00')
                hour_counts[hour_key] += 1
        
        if len(hour_counts) < 3:
            return anomalies
        
        # 计算平均值和标准差
        counts = list(hour_counts.values())
        avg_count = sum(counts) / len(counts)
        
        # 检测突增
        for hour, count in hour_counts.items():
            if avg_count > 0 and count > avg_count * self.volume_spike_threshold:
                severity = 'high' if count > avg_count * 5 else 'medium'
                anomalies.append(AnomalyResult(
                    anomaly_type='volume_spike',
                    severity=severity,
                    score=min(int((count / avg_count - 1) * 20), 100),
                    description=f"评论量突增: {count} 条 (平均 {avg_count:.1f} 条)",
                    affected_count=count,
                    time_window=hour,
                    details={'ratio': count / avg_count}
                ))
        
        # 检测深夜异常活动
        night_hours = [0, 1, 2, 3, 4, 5]
        night_count = 0
        for comment in comments:
            publish_time = comment.get('publish_time')
            if publish_time:
                if isinstance(publish_time, str):
                    try:
                        publish_time = datetime.fromisoformat(publish_time)
                    except:
                        continue
                if publish_time.hour in night_hours:
                    night_count += 1
        
        if len(comments) > 0:
            night_ratio = night_count / len(comments)
            if night_ratio > 0.3:  # 超过30%的评论在深夜
                anomalies.append(AnomalyResult(
                    anomaly_type='night_activity',
                    severity='medium',
                    score=int(night_ratio * 100),
                    description=f"深夜异常活动: {night_count} 条评论 ({night_ratio:.1%})",
                    affected_count=night_count,
                    details={'night_ratio': night_ratio}
                ))
        
        return anomalies
    
    def _detect_location_anomalies(self, comments: List[Dict]) -> List[AnomalyResult]:
        """检测地域异常"""
        anomalies = []
        
        # 统计IP分布
        ip_counts = Counter()
        for comment in comments:
            ip_location = comment.get('ip_location')
            if ip_location:
                ip_counts[ip_location] += 1
        
        if len(ip_counts) < 2:
            return anomalies
        
        total = sum(ip_counts.values())
        
        # 检测地域集中
        top_location, top_count = ip_counts.most_common(1)[0]
        top_ratio = top_count / total
        
        if top_ratio > 0.5 and total > 20:  # 超过50%集中在某一地区
            anomalies.append(AnomalyResult(
                anomaly_type='location_concentration',
                severity='medium',
                score=int(top_ratio * 100),
                description=f"地域集中异常: {top_location} 占比 {top_ratio:.1%}",
                affected_count=top_count,
                details={'location': top_location, 'ratio': top_ratio}
            ))
        
        # 检测海外异常
        overseas_keywords = ['海外', '美国', '日本', '韩国', '英国', '德国', '法国']
        overseas_count = sum(ip_counts.get(kw, 0) for kw in overseas_keywords)
        
        if overseas_count > 10 and overseas_count / total > 0.1:
            anomalies.append(AnomalyResult(
                anomaly_type='overseas_activity',
                severity='low',
                score=int((overseas_count / total) * 100),
                description=f"海外异常活动: {overseas_count} 条评论 ({overseas_count/total:.1%})",
                affected_count=overseas_count
            ))
        
        return anomalies
    
    def _detect_sentiment_anomalies(self, sentiment_results: List[Dict]) -> List[AnomalyResult]:
        """检测情感异常"""
        anomalies = []
        
        if not sentiment_results:
            return anomalies
        
        # 计算负面比例
        negative_count = sum(1 for r in sentiment_results if r.get('sentiment') == 'negative')
        total = len(sentiment_results)
        negative_ratio = negative_count / total if total > 0 else 0
        
        if negative_ratio > self.negative_ratio_threshold:
            severity = 'critical' if negative_ratio > 0.8 else 'high'
            anomalies.append(AnomalyResult(
                anomaly_type='negative_sentiment_spike',
                severity=severity,
                score=int(negative_ratio * 100),
                description=f"负面情感异常: {negative_count} 条 ({negative_ratio:.1%})",
                affected_count=negative_count,
                details={'negative_ratio': negative_ratio}
            ))
        
        # 检测高风险评论
        high_risk_count = sum(1 for r in sentiment_results if r.get('risk_score', 0) >= 60)
        if high_risk_count > 10:
            anomalies.append(AnomalyResult(
                anomaly_type='high_risk_content',
                severity='high',
                score=min(high_risk_count * 2, 100),
                description=f"高风险评论: {high_risk_count} 条",
                affected_count=high_risk_count
            ))
        
        return anomalies
    
    def _detect_content_anomalies(self, comments: List[Dict]) -> List[AnomalyResult]:
        """检测内容异常"""
        anomalies = []
        
        # 1. 检测重复内容
        contents = [comment.get('content', '') for comment in comments]
        unique_contents = set(contents)
        duplicate_ratio = 1 - (len(unique_contents) / len(contents)) if contents else 0
        
        if duplicate_ratio > 0.3:
            anomalies.append(AnomalyResult(
                anomaly_type='content_duplication',
                severity='high' if duplicate_ratio > 0.5 else 'medium',
                score=int(duplicate_ratio * 100),
                description=f"内容重复异常: 重复率 {duplicate_ratio:.1%}",
                affected_count=int(len(contents) * duplicate_ratio),
                details={'duplicate_ratio': duplicate_ratio}
            ))
        
        # 2. 检测刷屏行为 (短时间大量相似内容)
        # 简化版: 检测内容长度异常
        short_comments = [c for c in contents if len(c) < 10]
        if len(short_comments) / len(contents) > 0.4:
            anomalies.append(AnomalyResult(
                anomaly_type='spam_short_content',
                severity='medium',
                score=int((len(short_comments) / len(contents)) * 100),
                description=f"短评论刷屏: {len(short_comments)} 条 (< 10字)",
                affected_count=len(short_comments)
            ))
        
        # 3. 检测敏感词集中
        sensitive_keywords = ['谣言', '真相', '辟谣', '转发', '扩散']
        keyword_counts = Counter()
        for content in contents:
            for keyword in sensitive_keywords:
                if keyword in content:
                    keyword_counts[keyword] += 1
        
        if keyword_counts:
            top_keyword, top_count = keyword_counts.most_common(1)[0]
            if top_count > 10:
                anomalies.append(AnomalyResult(
                    anomaly_type='sensitive_keyword_concentration',
                    severity='medium',
                    score=min(top_count * 5, 100),
                    description=f"敏感词集中: '{top_keyword}' 出现 {top_count} 次",
                    affected_count=top_count,
                    details={'keyword': top_keyword, 'count': top_count}
                ))
        
        return anomalies
    
    def get_summary(self, anomalies: List[AnomalyResult]) -> Dict:
        """获取异常检测摘要"""
        if not anomalies:
            return {
                'total_anomalies': 0,
                'has_critical': False,
                'has_high': False
            }
        
        severity_counts = Counter(a.severity for a in anomalies)
        
        return {
            'total_anomalies': len(anomalies),
            'critical': severity_counts.get('critical', 0),
            'high': severity_counts.get('high', 0),
            'medium': severity_counts.get('medium', 0),
            'low': severity_counts.get('low', 0),
            'has_critical': severity_counts.get('critical', 0) > 0,
            'has_high': severity_counts.get('high', 0) > 0,
            'anomaly_types': list(set(a.anomaly_type for a in anomalies))
        }
