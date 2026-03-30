"""
情感分析模块
分析评论情感倾向 + 风险评分
"""

import re
from typing import List, Dict, Optional
from dataclasses import dataclass
import logging

logger = logging.getLogger(__name__)


@dataclass
class SentimentResult:
    """情感分析结果"""
    sentiment: str           # positive/negative/neutral
    score: float            # 0-1, 接近0为负面, 接近1为正面
    risk_score: int         # 0-100, 风险评分
    risk_level: str         # low/medium/high
    keywords: List[str]     # 关键词
    sensitive_words: List[str]  # 敏感词


class SentimentAnalyzer:
    """情感分析器"""
    
    # 敏感词库 (可扩展)
    SENSITIVE_WORDS = {
        # 谣言相关
        '谣言', '真相', '辟谣', '反转', '阴谋', '洗地', '带节奏',
        # 攻击性词汇
        '垃圾', '傻逼', '脑残', '智障', '弱智', '白痴', '废物',
        # 煽动性词汇
        '转发', '扩散', '让更多人知道', '必须曝光',
        # 极端情绪
        '恶心', '呕吐', '愤怒', '气愤', '忍无可忍',
    }
    
    # 停用词
    STOPWORDS = {
        '的', '了', '是', '我', '你', '他', '她', '它', '们',
        '这', '那', '就', '也', '都', '在', '有', '和', '与',
        '或', '但', '而', '如果', '因为', '所以', '虽然', '但是',
        '什么', '怎么', '为什么', '哪', '谁', '多少', '几',
        '啊', '呢', '吧', '吗', '呀', '哦', '嗯', '哈',
    }
    
    def __init__(self, use_snownlp: bool = True):
        """
        初始化
        
        Args:
            use_snownlp: 是否使用 SnowNLP (推荐)
        """
        self.use_snownlp = use_snownlp
        if use_snownlp:
            try:
                from snownlp import SnowNLP
                self.SnowNLP = SnowNLP
            except ImportError:
                logger.warning("SnowNLP 未安装, 使用简化版情感分析")
                self.use_snownlp = False
    
    def analyze(self, text: str) -> SentimentResult:
        """
        分析单条文本
        
        Args:
            text: 评论内容
        
        Returns:
            SentimentResult
        """
        # 情感分析
        if self.use_snownlp:
            score = self._snownlp_sentiment(text)
        else:
            score = self._simple_sentiment(text)
        
        # 情感分类
        if score < 0.35:
            sentiment = 'negative'
        elif score > 0.65:
            sentiment = 'positive'
        else:
            sentiment = 'neutral'
        
        # 敏感词检测
        sensitive_words = self._detect_sensitive_words(text)
        
        # 关键词提取
        keywords = self._extract_keywords(text)
        
        # 风险评分
        risk_score = self._calculate_risk_score(score, sensitive_words, text)
        
        # 风险等级
        if risk_score < 30:
            risk_level = 'low'
        elif risk_score < 60:
            risk_level = 'medium'
        else:
            risk_level = 'high'
        
        return SentimentResult(
            sentiment=sentiment,
            score=score,
            risk_score=risk_score,
            risk_level=risk_level,
            keywords=keywords,
            sensitive_words=sensitive_words
        )
    
    def analyze_batch(self, texts: List[str]) -> List[SentimentResult]:
        """批量分析"""
        return [self.analyze(text) for text in texts]
    
    def _snownlp_sentiment(self, text: str) -> float:
        """使用 SnowNLP 进行情感分析"""
        try:
            s = self.SnowNLP(text)
            return s.sentiments
        except:
            return 0.5
    
    def _simple_sentiment(self, text: str) -> float:
        """简化版情感分析 (基于词典)"""
        positive_words = {
            '好', '棒', '赞', '优秀', '厉害', '牛逼', '支持', '喜欢',
            '爱', '感谢', '开心', '高兴', '满意', '完美', '精彩'
        }
        negative_words = {
            '差', '烂', '垃圾', '恶心', '讨厌', '恨', '愤怒', '生气',
            '失望', '糟糕', '废物', '垃圾', '傻', '蠢', '坑'
        }
        
        text_lower = text.lower()
        pos_count = sum(1 for word in positive_words if word in text_lower)
        neg_count = sum(1 for word in negative_words if word in text_lower)
        
        total = pos_count + neg_count
        if total == 0:
            return 0.5
        
        return pos_count / total
    
    def _detect_sensitive_words(self, text: str) -> List[str]:
        """检测敏感词"""
        found = []
        for word in self.SENSITIVE_WORDS:
            if word in text:
                found.append(word)
        return found
    
    def _extract_keywords(self, text: str) -> List[str]:
        """提取关键词 (简化版)"""
        # 使用 jieba 分词
        try:
            import jieba
            words = jieba.cut(text)
            keywords = [
                word for word in words
                if len(word) > 1 and word not in self.STOPWORDS
            ]
            return keywords[:10]
        except:
            # 简单分割
            return [word for word in text.split() if len(word) > 1][:10]
    
    def _calculate_risk_score(self, sentiment_score: float, 
                              sensitive_words: List[str], 
                              text: str) -> int:
        """
        计算风险评分 (0-100)
        
        评分因素:
        - 情感倾向 (负面越高风险越高)
        - 敏感词数量
        - 文本长度 (过短可能刷屏)
        - 特殊模式 (大量重复标点、表情等)
        """
        score = 0
        
        # 情感因素 (30分)
        if sentiment_score < 0.2:
            score += 30
        elif sentiment_score < 0.35:
            score += 20
        elif sentiment_score < 0.5:
            score += 10
        
        # 敏感词因素 (40分)
        sensitive_score = min(len(sensitive_words) * 10, 40)
        score += sensitive_score
        
        # 文本长度因素 (15分)
        if len(text) < 5:
            score += 15  # 过短可能是垃圾评论
        elif len(text) > 500:
            score += 5   # 过长可能含大量内容
        
        # 特殊模式 (15分)
        # 连续标点
        if re.search(r'[!！?？]{3,}', text):
            score += 5
        # 连续表情
        if re.search(r'[\U0001F600-\U0001F64F]{3,}', text):
            score += 5
        # 全大写 (英文)
        if text.isupper() and len(text) > 10:
            score += 5
        
        return min(score, 100)
    
    def get_sentiment_distribution(self, results: List[SentimentResult]) -> Dict:
        """获取情感分布统计"""
        total = len(results)
        if total == 0:
            return {}
        
        positive = sum(1 for r in results if r.sentiment == 'positive')
        negative = sum(1 for r in results if r.sentiment == 'negative')
        neutral = sum(1 for r in results if r.sentiment == 'neutral')
        
        return {
            'total': total,
            'positive': positive,
            'positive_ratio': positive / total,
            'negative': negative,
            'negative_ratio': negative / total,
            'neutral': neutral,
            'neutral_ratio': neutral / total,
            'avg_score': sum(r.score for r in results) / total,
            'avg_risk_score': sum(r.risk_score for r in results) / total,
        }
