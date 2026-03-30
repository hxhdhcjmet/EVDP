"""
EVDP 情感分析模块
高效精准的中文情感分析引擎

算法特性:
- SnowNLP 核心算法 (准确度 70%+)
- 多维度风险评分
- 智能敏感词检测
- 高性能批量处理
"""

import re
import json
from pathlib import Path
from typing import List, Dict, Optional, Tuple
from dataclasses import dataclass
from collections import Counter
import logging

logger = logging.getLogger(__name__)


@dataclass
class SentimentResult:
    """情感分析结果"""
    
    # 基本信息
    comment_id: str                    # 评论ID
    content: str                       # 评论内容
    
    # 情感分析
    sentiment: str                     # positive/negative/neutral
    sentiment_score: float             # 0-1, 接近0为负面, 接近1为正面
    confidence: float                  # 置信度 0-1
    
    # 敏感词检测
    sensitive_words: List[Dict]        # [{word, category}, ...]
    sensitive_count: int               # 敏感词数量
    sensitive_categories: List[str]    # 涉及的敏感词类别
    
    # 风险评分
    risk_score: int                    # 0-100
    risk_level: str                    # low/medium/high/critical
    risk_factors: Dict[str, int]       # 风险因素分解
    
    # 关键词
    keywords: List[str]                # 提取的关键词


class SensitiveWordLoader:
    """敏感词加载器 - 高效加载和管理敏感词库"""
    
    def __init__(self, assets_dir: str = None):
        """
        初始化
        
        Args:
            assets_dir: assets 目录路径
        """
        if assets_dir is None:
            # 自动查找 assets 目录
            current_dir = Path(__file__).parent
            assets_dir = current_dir.parent.parent / 'assets'
        
        self.assets_dir = Path(assets_dir)
        self.sensitive_dir = self.assets_dir / 'sensitive_words'
        
        # 敏感词库: {category: set(words)}
        self.word_categories: Dict[str, set] = {}
        
        # 反向索引: {word: category}
        self.word_to_category: Dict[str, str] = {}
        
        # 加载敏感词
        self._load_all()
    
    def _load_all(self):
        """加载所有敏感词库"""
        if not self.sensitive_dir.exists():
            logger.warning(f"敏感词目录不存在: {self.sensitive_dir}")
            self._load_default()
            return
        
        # 定义文件映射
        file_mapping = {
            'rumor_words.txt': '谣言类',
            'attack_words.txt': '攻击类',
            'incitement_words.txt': '煽动类',
            'extreme_words.txt': '极端情绪'
        }
        
        for filename, category in file_mapping.items():
            file_path = self.sensitive_dir / filename
            
            if file_path.exists():
                words = self._load_file(file_path)
                self.word_categories[category] = words
                
                # 建立反向索引
                for word in words:
                    self.word_to_category[word] = category
                
                logger.info(f"加载 {category}: {len(words)} 个敏感词")
            else:
                logger.warning(f"敏感词文件不存在: {file_path}")
        
        # 如果没有加载到任何词库,使用默认
        if not self.word_categories:
            self._load_default()
    
    def _load_file(self, file_path: Path) -> set:
        """加载单个文件"""
        words = set()
        
        with open(file_path, 'r', encoding='utf-8') as f:
            for line in f:
                word = line.strip()
                if word and not word.startswith('#'):  # 忽略注释
                    words.add(word)
        
        return words
    
    def _load_default(self):
        """加载默认敏感词库"""
        self.word_categories = {
            '谣言类': {'谣言', '真相', '辟谣', '反转', '阴谋', '洗地', '带节奏'},
            '攻击类': {'垃圾', '傻逼', '脑残', '智障', '废物', '白痴'},
            '煽动类': {'转发', '扩散', '让更多人知道', '必须曝光'},
            '极端情绪': {'恶心', '呕吐', '愤怒', '气愤', '忍无可忍'}
        }
        
        # 建立反向索引
        for category, words in self.word_categories.items():
            for word in words:
                self.word_to_category[word] = category
        
        logger.info("使用默认敏感词库")
    
    def detect(self, content: str) -> Tuple[List[Dict], List[str]]:
        """
        检测敏感词
        
        Returns:
            (敏感词列表, 类别列表)
        """
        found_words = []
        categories = set()
        
        for word, category in self.word_to_category.items():
            if word in content:
                found_words.append({
                    'word': word,
                    'category': category
                })
                categories.add(category)
        
        return found_words, list(categories)
    
    def get_stats(self) -> Dict:
        """获取统计信息"""
        return {
            'total_words': len(self.word_to_category),
            'categories': {
                category: len(words)
                for category, words in self.word_categories.items()
            }
        }


class StopwordLoader:
    """停用词加载器"""
    
    def __init__(self, assets_dir: str = None):
        if assets_dir is None:
            current_dir = Path(__file__).parent
            assets_dir = current_dir.parent.parent / 'assets'
        
        self.assets_dir = Path(assets_dir)
        self.stopwords_dir = self.assets_dir / 'stopwords'
        
        self.stopwords = set()
        self._load_all()
    
    def _load_all(self):
        """加载所有停用词"""
        # 基础停用词
        self.stopwords = {
            '的', '了', '是', '我', '你', '他', '她', '它', '们',
            '这', '那', '就', '也', '都', '在', '有', '和', '与',
            '或', '但', '而', '如果', '因为', '所以', '虽然', '但是',
            '什么', '怎么', '为什么', '哪', '谁', '多少', '几',
            '啊', '呢', '吧', '吗', '呀', '哦', '嗯', '哈',
            '一个', '这个', '那个', '不是', '没有', '可以', '已经'
        }
        
        # 加载平台停用词
        if self.stopwords_dir.exists():
            for file_path in self.stopwords_dir.glob('*.txt'):
                words = self._load_file(file_path)
                self.stopwords.update(words)
        
        logger.info(f"加载停用词: {len(self.stopwords)} 个")
    
    def _load_file(self, file_path: Path) -> set:
        """加载停用词文件"""
        words = set()
        
        with open(file_path, 'r', encoding='utf-8') as f:
            for line in f:
                word = line.strip()
                if word:
                    words.add(word)
        
        return words


class SentimentAnalyzer:
    """
    情感分析器 - 主控制器
    
    Features:
    - SnowNLP 核心算法
    - 多维度风险评分
    - 智能敏感词检测
    - 高性能批量处理
    """
    
    def __init__(self,
                 use_snownlp: bool = True,
                 assets_dir: str = None):
        """
        初始化
        
        Args:
            use_snownlp: 是否使用 SnowNLP
            assets_dir: assets 目录路径
        """
        self.use_snownlp = use_snownlp
        
        # 加载 SnowNLP
        if use_snownlp:
            try:
                from snownlp import SnowNLP
                self.SnowNLP = SnowNLP
                logger.info("SnowNLP 加载成功")
            except ImportError:
                logger.warning("SnowNLP 未安装, 使用简化版情感分析")
                self.use_snownlp = False
                self.SnowNLP = None
        else:
            self.SnowNLP = None
        
        # 加载敏感词
        self.sensitive_loader = SensitiveWordLoader(assets_dir)
        
        # 加载停用词
        self.stopword_loader = StopwordLoader(assets_dir)
        
        # 统计数据
        self.stats = {
            'total_analyzed': 0,
            'positive': 0,
            'negative': 0,
            'neutral': 0,
            'with_sensitive': 0
        }
    
    def analyze(self, 
                comment_id: str,
                content: str) -> SentimentResult:
        """
        分析单条评论
        
        Args:
            comment_id: 评论ID
            content: 评论内容
        
        Returns:
            SentimentResult
        """
        self.stats['total_analyzed'] += 1
        
        # 1. 情感分析
        sentiment, score, confidence = self._analyze_sentiment(content)
        
        # 更新统计
        self.stats[sentiment] += 1
        
        # 2. 敏感词检测
        sensitive_words, categories = self.sensitive_loader.detect(content)
        
        if sensitive_words:
            self.stats['with_sensitive'] += 1
        
        # 3. 风险评分
        risk_score, risk_level, risk_factors = self._calculate_risk(
            sentiment, score, sensitive_words, content
        )
        
        # 4. 关键词提取
        keywords = self._extract_keywords(content)
        
        return SentimentResult(
            comment_id=comment_id,
            content=content,
            sentiment=sentiment,
            sentiment_score=score,
            confidence=confidence,
            sensitive_words=sensitive_words,
            sensitive_count=len(sensitive_words),
            sensitive_categories=categories,
            risk_score=risk_score,
            risk_level=risk_level,
            risk_factors=risk_factors,
            keywords=keywords
        )
    
    def analyze_batch(self,
                      comments: List[Dict],
                      id_field: str = 'comment_id',
                      content_field: str = 'content') -> List[SentimentResult]:
        """
        批量分析
        
        Args:
            comments: 评论列表
            id_field: ID字段名
            content_field: 内容字段名
        
        Returns:
            结果列表
        """
        results = []
        
        for comment in comments:
            comment_id = comment.get(id_field, '')
            content = comment.get(content_field, '')
            
            if not content:
                continue
            
            result = self.analyze(comment_id, content)
            results.append(result)
        
        return results
    
    def _analyze_sentiment(self, content: str) -> Tuple[str, float, float]:
        """
        情感分析核心算法
        
        Returns:
            (情感标签, 分数, 置信度)
        """
        if self.use_snownlp and self.SnowNLP:
            return self._snownlp_sentiment(content)
        else:
            return self._simple_sentiment(content)
    
    def _snownlp_sentiment(self, content: str) -> Tuple[str, float, float]:
        """SnowNLP 情感分析"""
        try:
            s = self.SnowNLP(content)
            score = s.sentiments
            
            # 计算置信度 (基于情感强度)
            confidence = abs(score - 0.5) * 2  # 0-1
            
            # 分类
            if score < 0.35:
                sentiment = 'negative'
            elif score > 0.65:
                sentiment = 'positive'
            else:
                sentiment = 'neutral'
            
            return sentiment, score, confidence
        
        except Exception as e:
            logger.warning(f"SnowNLP 分析失败: {e}")
            return 'neutral', 0.5, 0.0
    
    def _simple_sentiment(self, content: str) -> Tuple[str, float, float]:
        """简化版情感分析 (基于词典)"""
        # 正面词
        positive_words = {
            '好', '棒', '赞', '优秀', '厉害', '牛逼', '支持', '喜欢',
            '爱', '感谢', '开心', '高兴', '满意', '完美', '精彩',
            '不错', '很好', '真好', '太好了', '赞赞'
        }
        
        # 负面词
        negative_words = {
            '差', '烂', '垃圾', '恶心', '讨厌', '恨', '愤怒', '生气',
            '失望', '糟糕', '废物', '傻', '蠢', '坑', '无语',
            '不好', '很差', '太差', '垃圾'
        }
        
        content_lower = content.lower()
        
        # 统计
        pos_count = sum(1 for word in positive_words if word in content_lower)
        neg_count = sum(1 for word in negative_words if word in content_lower)
        
        total = pos_count + neg_count
        
        if total == 0:
            return 'neutral', 0.5, 0.0
        
        # 计算分数
        score = pos_count / total
        confidence = min(total / 5, 1.0)  # 最多5个词达到最大置信度
        
        # 分类
        if score < 0.35:
            sentiment = 'negative'
        elif score > 0.65:
            sentiment = 'positive'
        else:
            sentiment = 'neutral'
        
        return sentiment, score, confidence
    
    def _calculate_risk(self,
                       sentiment: str,
                       sentiment_score: float,
                       sensitive_words: List[Dict],
                       content: str) -> Tuple[int, str, Dict]:
        """
        风险评分算法
        
        Returns:
            (风险评分, 风险等级, 风险因素)
        """
        risk_factors = {
            'sentiment': 0,
            'sensitive': 0,
            'text_features': 0
        }
        
        # 1. 情感因素 (40分)
        if sentiment == 'negative':
            if sentiment_score < 0.2:
                risk_factors['sentiment'] = 40
            elif sentiment_score < 0.35:
                risk_factors['sentiment'] = 30
            else:
                risk_factors['sentiment'] = 20
        
        # 2. 敏感词因素 (40分)
        sensitive_count = len(sensitive_words)
        if sensitive_count > 0:
            # 不同类别加权
            categories = set(word['category'] for word in sensitive_words)
            category_score = min(len(categories) * 15, 40)
            count_score = min(sensitive_count * 8, 30)
            risk_factors['sensitive'] = min(category_score + count_score, 40)
        
        # 3. 文本特征 (20分)
        # 过短
        if len(content) < 5:
            risk_factors['text_features'] += 10
        # 连续标点
        if re.search(r'[!！?？]{3,}', content):
            risk_factors['text_features'] += 5
        # 连续表情
        if re.search(r'\[[\w\u4e00-\u9fa5]+\]{3,}', content):
            risk_factors['text_features'] += 5
        
        # 总分
        total_score = sum(risk_factors.values())
        total_score = min(total_score, 100)
        
        # 风险等级
        if total_score >= 80:
            risk_level = 'critical'
        elif total_score >= 60:
            risk_level = 'high'
        elif total_score >= 40:
            risk_level = 'medium'
        else:
            risk_level = 'low'
        
        return total_score, risk_level, risk_factors
    
    def _extract_keywords(self, content: str) -> List[str]:
        """提取关键词"""
        # 使用 jieba
        try:
            import jieba
            import jieba.analyse
            
            keywords = jieba.analyse.extract_tags(
                content,
                topK=10,
                withWeight=False
            )
            
            # 过滤停用词
            keywords = [
                word for word in keywords
                if word not in self.stopword_loader.stopwords
            ]
            
            return keywords
        
        except ImportError:
            # 简单提取
            words = re.split(r'[\s\.,!?;:\'"()（），。！？；：""''、]+', content)
            keywords = [
                word for word in words
                if len(word) > 1 and word not in self.stopword_loader.stopwords
            ]
            return keywords[:10]
    
    def get_distribution(self, results: List[SentimentResult]) -> Dict:
        """获取情感分布统计"""
        if not results:
            return {}
        
        total = len(results)
        
        positive = sum(1 for r in results if r.sentiment == 'positive')
        negative = sum(1 for r in results if r.sentiment == 'negative')
        neutral = sum(1 for r in results if r.sentiment == 'neutral')
        
        with_sensitive = sum(1 for r in results if r.sensitive_count > 0)
        high_risk = sum(1 for r in results if r.risk_score >= 60)
        
        avg_sentiment_score = sum(r.sentiment_score for r in results) / total
        avg_risk_score = sum(r.risk_score for r in results) / total
        
        return {
            'total': total,
            'positive': positive,
            'positive_ratio': positive / total,
            'negative': negative,
            'negative_ratio': negative / total,
            'neutral': neutral,
            'neutral_ratio': neutral / total,
            'with_sensitive': with_sensitive,
            'with_sensitive_ratio': with_sensitive / total,
            'high_risk': high_risk,
            'high_risk_ratio': high_risk / total,
            'avg_sentiment_score': avg_sentiment_score,
            'avg_risk_score': avg_risk_score
        }
    
    def get_stats(self) -> Dict:
        """获取统计信息"""
        return self.stats.copy()


# 便捷函数
def analyze_sentiment(comment_id: str, content: str, **kwargs) -> SentimentResult:
    """便捷函数 - 分析单条评论"""
    analyzer = SentimentAnalyzer(**kwargs)
    return analyzer.analyze(comment_id, content)


def analyze_sentiment_batch(comments: List[Dict], **kwargs) -> List[SentimentResult]:
    """便捷函数 - 批量分析"""
    analyzer = SentimentAnalyzer(**kwargs)
    return analyzer.analyze_batch(comments)
