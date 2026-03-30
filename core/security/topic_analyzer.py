"""
话题分析模块
分析热门话题、舆论导向和传播链路
"""

import re
from typing import List, Dict, Optional
from dataclasses import dataclass
from collections import Counter, defaultdict
import logging

logger = logging.getLogger(__name__)


@dataclass
class TopicResult:
    """话题分析结果"""
    top_keywords: List[tuple]      # 热门关键词 [(keyword, count), ...]
    topic_clusters: Dict           # 话题聚类
    sentiment_orientation: Dict    # 舆论导向
    sensitive_keywords: List[tuple] # 敏感关键词
    trending_score: float          # 热度评分


class TopicAnalyzer:
    """话题分析器"""
    
    # 停用词
    STOPWORDS = {
        '的', '了', '是', '我', '你', '他', '她', '它', '们',
        '这', '那', '就', '也', '都', '在', '有', '和', '与',
        '或', '但', '而', '如果', '因为', '所以', '虽然', '但是',
        '什么', '怎么', '为什么', '哪', '谁', '多少', '几',
        '啊', '呢', '吧', '吗', '呀', '哦', '嗯', '哈',
        '一个', '这个', '那个', '不是', '没有', '可以', '已经',
        '还', '会', '要', '能', '说', '对', '好', '很', '都',
    }
    
    # 敏感词库
    SENSITIVE_KEYWORDS = {
        '谣言', '真相', '辟谣', '反转', '阴谋',
        '转发', '扩散', '让更多人知道', '必须曝光',
        '洗地', '带节奏', '水军', '机器人',
    }
    
    def __init__(self, use_jieba: bool = True):
        """
        初始化
        
        Args:
            use_jieba: 是否使用 jieba 分词
        """
        self.use_jieba = use_jieba
        if use_jieba:
            try:
                import jieba
                import jieba.analyse
                self.jieba = jieba
                self.jieba_analyse = jieba.analyse
            except ImportError:
                logger.warning("jieba 未安装, 使用简单分词")
                self.use_jieba = False
    
    def analyze(self, 
                comments: List[Dict], 
                sentiment_results: List[Dict] = None,
                top_n: int = 20) -> TopicResult:
        """
        分析话题
        
        Args:
            comments: 评论列表
            sentiment_results: 情感分析结果 (可选)
            top_n: 返回前N个关键词
        
        Returns:
            TopicResult
        """
        # 提取文本
        texts = [comment.get('content', '') for comment in comments]
        
        # 1. 关键词提取
        top_keywords = self._extract_keywords(texts, top_n)
        
        # 2. 话题聚类
        topic_clusters = self._cluster_topics(texts, top_keywords)
        
        # 3. 舆论导向分析
        sentiment_orientation = self._analyze_sentiment_orientation(
            comments, sentiment_results, top_keywords
        )
        
        # 4. 敏感关键词检测
        sensitive_keywords = self._detect_sensitive_keywords(texts)
        
        # 5. 热度评分
        trending_score = self._calculate_trending_score(
            len(comments), top_keywords, sentiment_orientation
        )
        
        return TopicResult(
            top_keywords=top_keywords,
            topic_clusters=topic_clusters,
            sentiment_orientation=sentiment_orientation,
            sensitive_keywords=sensitive_keywords,
            trending_score=trending_score
        )
    
    def _extract_keywords(self, texts: List[str], top_n: int) -> List[tuple]:
        """提取关键词"""
        if self.use_jieba:
            return self._jieba_keywords(texts, top_n)
        else:
            return self._simple_keywords(texts, top_n)
    
    def _jieba_keywords(self, texts: List[str], top_n: int) -> List[tuple]:
        """使用 jieba 提取关键词"""
        # 合并文本
        full_text = ' '.join(texts)
        
        # TF-IDF 提取
        keywords = self.jieba_analyse.extract_tags(
            full_text, 
            topK=top_n * 2,  # 多提取一些,后面过滤
            withWeight=True
        )
        
        # 过滤停用词
        filtered = [
            (word, weight) 
            for word, weight in keywords 
            if word not in self.STOPWORDS and len(word) > 1
        ]
        
        return filtered[:top_n]
    
    def _simple_keywords(self, texts: List[str], top_n: int) -> List[tuple]:
        """简单关键词提取"""
        word_counts = Counter()
        
        for text in texts:
            # 简单分割 (按空格和标点)
            words = re.split(r'[\s\.,!?;:\'"()（），。！？；：""''、]+', text)
            
            for word in words:
                word = word.strip()
                if len(word) > 1 and word not in self.STOPWORDS:
                    word_counts[word] += 1
        
        return word_counts.most_common(top_n)
    
    def _cluster_topics(self, texts: List[str], keywords: List[tuple]) -> Dict:
        """话题聚类 (简化版)"""
        # 简单实现: 基于关键词的聚类
        keyword_list = [kw[0] for kw in keywords[:10]]
        
        topic_clusters = defaultdict(int)
        
        for text in texts:
            # 找到文本中的关键词
            found_keywords = []
            for keyword in keyword_list:
                if keyword in text:
                    found_keywords.append(keyword)
            
            # 生成话题标签
            if len(found_keywords) >= 2:
                topic_label = '+'.join(sorted(found_keywords[:3]))
            elif len(found_keywords) == 1:
                topic_label = found_keywords[0]
            else:
                topic_label = '其他'
            
            topic_clusters[topic_label] += 1
        
        # 转换为排序后的字典
        sorted_clusters = dict(
            sorted(topic_clusters.items(), key=lambda x: x[1], reverse=True)[:10]
        )
        
        # 计算比例
        total = sum(sorted_clusters.values())
        result = {
            topic: {
                'count': count,
                'ratio': count / total if total > 0 else 0
            }
            for topic, count in sorted_clusters.items()
        }
        
        return result
    
    def _analyze_sentiment_orientation(self,
                                       comments: List[Dict],
                                       sentiment_results: List[Dict],
                                       keywords: List[tuple]) -> Dict:
        """分析舆论导向"""
        if not sentiment_results:
            return {}
        
        # 总体情感分布
        sentiment_counts = Counter(r.get('sentiment', 'neutral') for r in sentiment_results)
        total = len(sentiment_results)
        
        # 计算导向
        positive_ratio = sentiment_counts.get('positive', 0) / total if total > 0 else 0
        negative_ratio = sentiment_counts.get('negative', 0) / total if total > 0 else 0
        
        # 确定导向
        if positive_ratio > 0.6:
            orientation = 'strongly_positive'
            orientation_label = '强烈支持'
        elif positive_ratio > 0.4:
            orientation = 'positive'
            orientation_label = '偏向支持'
        elif negative_ratio > 0.6:
            orientation = 'strongly_negative'
            orientation_label = '强烈反对'
        elif negative_ratio > 0.4:
            orientation = 'negative'
            orientation_label = '偏向反对'
        else:
            orientation = 'neutral'
            orientation_label = '中立'
        
        return {
            'orientation': orientation,
            'orientation_label': orientation_label,
            'positive_ratio': positive_ratio,
            'negative_ratio': negative_ratio,
            'neutral_ratio': sentiment_counts.get('neutral', 0) / total if total > 0 else 0,
            'sentiment_counts': dict(sentiment_counts)
        }
    
    def _detect_sensitive_keywords(self, texts: List[str]) -> List[tuple]:
        """检测敏感关键词"""
        keyword_counts = Counter()
        
        for text in texts:
            for sensitive_word in self.SENSITIVE_KEYWORDS:
                if sensitive_word in text:
                    keyword_counts[sensitive_word] += 1
        
        # 返回排序结果,附带风险等级
        results = []
        for keyword, count in keyword_counts.most_common(10):
            # 简单判断风险等级
            if count > 50:
                risk_level = 'high'
            elif count > 20:
                risk_level = 'medium'
            else:
                risk_level = 'low'
            
            results.append((keyword, count, risk_level))
        
        return results
    
    def _calculate_trending_score(self,
                                  comment_count: int,
                                  keywords: List[tuple],
                                  orientation: Dict) -> float:
        """计算热度评分 (0-100)"""
        score = 0.0
        
        # 评论数量因素 (40分)
        if comment_count > 10000:
            score += 40
        elif comment_count > 5000:
            score += 35
        elif comment_count > 1000:
            score += 30
        elif comment_count > 500:
            score += 25
        elif comment_count > 100:
            score += 20
        else:
            score += min(comment_count / 5, 20)
        
        # 关键词热度 (30分)
        if keywords:
            # 计算关键词总权重
            keyword_weight = sum(weight for _, weight in keywords[:10])
            score += min(keyword_weight * 10, 30)
        
        # 情感强度 (30分)
        if orientation:
            # 极端情感 (强烈支持/反对) 热度更高
            if orientation.get('orientation') in ['strongly_positive', 'strongly_negative']:
                score += 30
            elif orientation.get('orientation') in ['positive', 'negative']:
                score += 20
            else:
                score += 10
        
        return min(score, 100)
    
    def get_summary(self, result: TopicResult) -> Dict:
        """获取话题分析摘要"""
        return {
            'top_keywords_count': len(result.top_keywords),
            'top_5_keywords': [kw[0] for kw in result.top_keywords[:5]],
            'topic_clusters_count': len(result.topic_clusters),
            'orientation': result.sentiment_orientation.get('orientation_label', '未知'),
            'sensitive_keywords_count': len(result.sensitive_keywords),
            'has_sensitive': len(result.sensitive_keywords) > 0,
            'trending_score': result.trending_score,
            'trending_level': self._get_trending_level(result.trending_score)
        }
    
    def _get_trending_level(self, score: float) -> str:
        """获取热度等级"""
        if score >= 80:
            return '极热'
        elif score >= 60:
            return '热门'
        elif score >= 40:
            return '一般'
        else:
            return '冷门'
