"""
机器人检测模块
识别可疑账号和机器人行为
"""

import re
from typing import List, Dict, Optional
from dataclasses import dataclass
from collections import Counter, defaultdict
from datetime import datetime, timedelta
import logging

logger = logging.getLogger(__name__)


@dataclass
class BotDetectionResult:
    """机器人检测结果"""
    user_id: str
    user_name: str
    platform: str
    
    # 风险评分
    overall_risk_score: int      # 0-100
    risk_level: str              # low/medium/high
    
    # 各维度评分
    frequency_score: int         # 发言频率评分
    repetition_score: int        # 内容重复度评分
    account_score: int           # 账号特征评分
    behavior_score: int          # 行为模式评分
    
    # 详细信息
    total_comments: int          # 总评论数
    avg_comments_per_hour: float # 平均每小时评论数
    content_similarity: float    # 内容相似度
    unique_contents: int         # 唯一内容数
    
    # 判断依据
    reasons: List[str]           # 判断为机器人的理由


class BotDetector:
    """机器人检测器"""
    
    def __init__(self, 
                 frequency_threshold: float = 10.0,  # 每小时评论数阈值
                 similarity_threshold: float = 0.7,  # 内容相似度阈值
                 min_comments: int = 3):             # 最少评论数才检测
        """
        初始化
        
        Args:
            frequency_threshold: 发言频率阈值 (评论/小时)
            similarity_threshold: 内容相似度阈值
            min_comments: 最少评论数才进行检测
        """
        self.frequency_threshold = frequency_threshold
        self.similarity_threshold = similarity_threshold
        self.min_comments = min_comments
    
    def detect(self, comments: List[Dict]) -> Dict[str, BotDetectionResult]:
        """
        检测所有用户的机器人风险
        
        Args:
            comments: 评论列表 (需包含 user_id, user_name, content, publish_time)
        
        Returns:
            {user_id: BotDetectionResult}
        """
        # 按用户分组
        user_comments = self._group_by_user(comments)
        
        results = {}
        for user_id, user_data in user_comments.items():
            if len(user_data['comments']) < self.min_comments:
                continue
            
            result = self._analyze_user(
                user_id=user_id,
                user_name=user_data['user_name'],
                platform=user_data['platform'],
                comments=user_data['comments']
            )
            results[user_id] = result
        
        return results
    
    def _group_by_user(self, comments: List[Dict]) -> Dict:
        """按用户分组评论"""
        user_data = defaultdict(lambda: {
            'user_name': '',
            'platform': '',
            'comments': []
        })
        
        for comment in comments:
            user_id = comment.get('user_id', comment.get('comment_id', ''))
            user_data[user_id]['user_name'] = comment.get('user_name', '未知用户')
            user_data[user_id]['platform'] = comment.get('platform', 'unknown')
            user_data[user_id]['comments'].append(comment)
        
        return user_data
    
    def _analyze_user(self, user_id: str, user_name: str, 
                      platform: str, comments: List[Dict]) -> BotDetectionResult:
        """分析单个用户"""
        
        # 1. 发言频率分析
        frequency_score, avg_per_hour = self._analyze_frequency(comments)
        
        # 2. 内容重复度分析
        repetition_score, similarity, unique_contents = self._analyze_repetition(comments)
        
        # 3. 账号特征分析
        account_score = self._analyze_account_features(user_name, comments)
        
        # 4. 行为模式分析
        behavior_score = self._analyze_behavior_patterns(comments)
        
        # 综合评分 (加权平均)
        overall_score = int(
            frequency_score * 0.3 +
            repetition_score * 0.3 +
            account_score * 0.2 +
            behavior_score * 0.2
        )
        
        # 风险等级
        if overall_score < 30:
            risk_level = 'low'
        elif overall_score < 60:
            risk_level = 'medium'
        else:
            risk_level = 'high'
        
        # 判断理由
        reasons = self._generate_reasons(
            frequency_score, repetition_score, 
            account_score, behavior_score,
            avg_per_hour, similarity
        )
        
        return BotDetectionResult(
            user_id=user_id,
            user_name=user_name,
            platform=platform,
            overall_risk_score=overall_score,
            risk_level=risk_level,
            frequency_score=frequency_score,
            repetition_score=repetition_score,
            account_score=account_score,
            behavior_score=behavior_score,
            total_comments=len(comments),
            avg_comments_per_hour=avg_per_hour,
            content_similarity=similarity,
            unique_contents=unique_contents,
            reasons=reasons
        )
    
    def _analyze_frequency(self, comments: List[Dict]) -> tuple:
        """分析发言频率"""
        if len(comments) < 2:
            return 0, 0.0
        
        # 提取时间
        times = []
        for comment in comments:
            publish_time = comment.get('publish_time')
            if publish_time:
                if isinstance(publish_time, str):
                    try:
                        publish_time = datetime.fromisoformat(publish_time)
                    except:
                        continue
                times.append(publish_time)
        
        if len(times) < 2:
            return 0, 0.0
        
        # 计算时间跨度
        times.sort()
        time_span = (times[-1] - times[0]).total_seconds() / 3600  # 小时
        
        if time_span == 0:
            return 100, float(len(comments))  # 瞬间发多条
        
        avg_per_hour = len(comments) / time_span
        
        # 评分
        if avg_per_hour > 20:
            score = 100
        elif avg_per_hour > 10:
            score = 80
        elif avg_per_hour > 5:
            score = 60
        elif avg_per_hour > 2:
            score = 30
        else:
            score = 0
        
        return score, avg_per_hour
    
    def _analyze_repetition(self, comments: List[Dict]) -> tuple:
        """分析内容重复度"""
        contents = [comment.get('content', '') for comment in comments]
        
        if len(contents) < 2:
            return 0, 0.0, len(set(contents))
        
        # 去重
        unique_contents = set(contents)
        similarity = 1 - (len(unique_contents) / len(contents))
        
        # 评分
        if similarity > 0.8:
            score = 100
        elif similarity > 0.6:
            score = 80
        elif similarity > 0.4:
            score = 50
        else:
            score = int(similarity * 50)
        
        return score, similarity, len(unique_contents)
    
    def _analyze_account_features(self, user_name: str, comments: List[Dict]) -> int:
        """分析账号特征"""
        score = 0
        
        # 1. 用户名规律性
        # 全数字/字母
        if re.match(r'^[0-9]+$', user_name):
            score += 30
        elif re.match(r'^[a-zA-Z0-9]+$', user_name):
            score += 20
        
        # 用户名包含常见机器人前缀
        bot_prefixes = ['user_', 'bot_', 'auto_', 'test_', 'demo_']
        if any(user_name.lower().startswith(prefix) for prefix in bot_prefixes):
            score += 30
        
        # 2. 用户等级异常
        user_levels = [c.get('user_level') for c in comments if c.get('user_level')]
        if user_levels:
            avg_level = sum(user_levels) / len(user_levels)
            if avg_level < 2:
                score += 20
        
        # 3. IP 属地异常
        ip_locations = [c.get('ip_location') for c in comments if c.get('ip_location')]
        if len(set(ip_locations)) == 1 and len(ip_locations) > 5:
            # 所有评论来自同一地区,可能集中操作
            score += 10
        
        return min(score, 100)
    
    def _analyze_behavior_patterns(self, comments: List[Dict]) -> int:
        """分析行为模式"""
        score = 0
        
        # 1. 时间分布异常
        times = []
        for comment in comments:
            publish_time = comment.get('publish_time')
            if publish_time:
                if isinstance(publish_time, str):
                    try:
                        publish_time = datetime.fromisoformat(publish_time)
                    except:
                        continue
                times.append(publish_time.hour)
        
        if times:
            hour_dist = Counter(times)
            # 如果集中在某几个小时
            if len(hour_dist) > 0:
                max_concentration = max(hour_dist.values()) / len(times)
                if max_concentration > 0.8:
                    score += 30
        
        # 2. 表情使用模式
        emoji_pattern = re.compile(
            r'[\U0001F600-\U0001F64F\U0001F300-\U0001F5FF\U0001F680-\U0001F6FF]'
        )
        
        emoji_counts = []
        for comment in comments:
            content = comment.get('content', '')
            emoji_count = len(emoji_pattern.findall(content))
            emoji_counts.append(emoji_count)
        
        if emoji_counts:
            avg_emoji = sum(emoji_counts) / len(emoji_counts)
            if avg_emoji > 5:
                score += 20
        
        # 3. @ 提及频率
        at_pattern = re.compile(r'@\S+')
        at_counts = []
        for comment in comments:
            content = comment.get('content', '')
            at_count = len(at_pattern.findall(content))
            at_counts.append(at_count)
        
        if at_counts and sum(at_counts) > 0:
            avg_at = sum(at_counts) / len(at_counts)
            if avg_at > 2:
                score += 20
        
        return min(score, 100)
    
    def _generate_reasons(self, freq_score: int, rep_score: int,
                         acc_score: int, beh_score: int,
                         avg_per_hour: float, similarity: float) -> List[str]:
        """生成判断理由"""
        reasons = []
        
        if freq_score >= 60:
            reasons.append(f"发言频率异常: 平均 {avg_per_hour:.1f} 条/小时")
        
        if rep_score >= 60:
            reasons.append(f"内容重复度高: {similarity:.1%}")
        
        if acc_score >= 50:
            reasons.append("账号特征异常")
        
        if beh_score >= 50:
            reasons.append("行为模式异常")
        
        if not reasons:
            reasons.append("未发现明显异常")
        
        return reasons
    
    def get_summary(self, results: Dict[str, BotDetectionResult]) -> Dict:
        """获取检测结果摘要"""
        if not results:
            return {}
        
        total = len(results)
        high_risk = sum(1 for r in results.values() if r.risk_level == 'high')
        medium_risk = sum(1 for r in results.values() if r.risk_level == 'medium')
        low_risk = sum(1 for r in results.values() if r.risk_level == 'low')
        
        return {
            'total_users': total,
            'high_risk': high_risk,
            'high_risk_ratio': high_risk / total,
            'medium_risk': medium_risk,
            'medium_risk_ratio': medium_risk / total,
            'low_risk': low_risk,
            'low_risk_ratio': low_risk / total,
            'avg_risk_score': sum(r.overall_risk_score for r in results.values()) / total,
        }
