"""
综合安全分析器
整合所有分析模块,提供一站式安全分析服务
"""

from typing import List, Dict, Optional
from pathlib import Path
import logging

from .data_normalizer import DataNormalizer, UnifiedComment
from .sentiment_analyzer import SentimentAnalyzer, SentimentResult
from .bot_detector import BotDetector, BotDetectionResult
from .anomaly_detector import AnomalyDetector, AnomalyResult
from .risk_assessment import RiskAssessment, RiskAssessmentResult
from .topic_analyzer import TopicAnalyzer, TopicResult
from .report_generator import ReportGenerator, Report

logger = logging.getLogger(__name__)


class SecurityAnalyzer:
    """综合安全分析器 - 一站式分析服务"""
    
    def __init__(self):
        """初始化所有分析模块"""
        self.normalizer = DataNormalizer()
        self.sentiment_analyzer = SentimentAnalyzer()
        self.bot_detector = BotDetector()
        self.anomaly_detector = AnomalyDetector()
        self.risk_assessment = RiskAssessment()
        self.topic_analyzer = TopicAnalyzer()
        self.report_generator = ReportGenerator()
    
    def analyze_file(self, 
                     file_path: str,
                     platform: str = None,
                     generate_report: bool = True) -> Dict:
        """
        分析单个文件
        
        Args:
            file_path: JSONL 文件路径
            platform: 平台名称 (自动检测)
            generate_report: 是否生成报告
        
        Returns:
            分析结果字典
        """
        logger.info(f"开始分析文件: {file_path}")
        
        # 1. 数据标准化
        comments = self.normalizer.normalize_file(file_path, platform)
        if not comments:
            logger.warning("未找到有效评论数据")
            return {'error': '未找到有效评论数据'}
        
        # 转换为字典列表
        comment_dicts = [c.to_dict() for c in comments]
        
        # 2. 情感分析
        logger.info("执行情感分析...")
        sentiment_results = self.sentiment_analyzer.analyze_batch(
            [c['content'] for c in comment_dicts]
        )
        sentiment_dicts = [
            {
                'sentiment': r.sentiment,
                'score': r.score,
                'risk_score': r.risk_score,
                'risk_level': r.risk_level,
                'keywords': r.keywords,
                'sensitive_words': r.sensitive_words,
                'content': comment_dicts[i]['content'][:100]
            }
            for i, r in enumerate(sentiment_results)
        ]
        
        # 3. 机器人检测
        logger.info("执行机器人检测...")
        bot_results = self.bot_detector.detect(comment_dicts)
        
        # 4. 异常检测
        logger.info("执行异常检测...")
        anomaly_results = self.anomaly_detector.detect(
            comment_dicts, sentiment_dicts
        )
        
        # 5. 话题分析
        logger.info("执行话题分析...")
        topic_result = self.topic_analyzer.analyze(
            comment_dicts, sentiment_dicts
        )
        
        # 6. 风险评估
        logger.info("执行风险评估...")
        sentiment_summary = self.sentiment_analyzer.get_sentiment_distribution(sentiment_results)
        bot_summary = self.bot_detector.get_summary(bot_results)
        anomaly_summary = self.anomaly_detector.get_summary(anomaly_results)
        
        risk_result = self.risk_assessment.assess(
            sentiment_summary=sentiment_summary,
            bot_summary=bot_summary,
            anomaly_summary=anomaly_summary,
            total_comments=len(comments)
        )
        
        # 7. 生成报告
        report = None
        if generate_report:
            logger.info("生成报告...")
            
            # 获取时间范围
            times = [c.get('publish_time') for c in comment_dicts if c.get('publish_time')]
            time_range = {}
            if times:
                time_range = {
                    'start': min(times),
                    'end': max(times)
                }
            
            # 检测平台
            detected_platform = comments[0].platform if comments else 'unknown'
            
            report = self.report_generator.generate(
                data_source=file_path,
                time_range=time_range,
                platform=detected_platform,
                total_comments=len(comments),
                risk_assessment=risk_result,
                sentiment_results=sentiment_dicts,
                bot_results=bot_results,
                anomaly_results=anomaly_results,
                topic_result=topic_result
            )
        
        return {
            'comments': comment_dicts,
            'sentiment_results': sentiment_dicts,
            'sentiment_summary': sentiment_summary,
            'bot_results': {k: self._bot_to_dict(v) for k, v in bot_results.items()},
            'bot_summary': bot_summary,
            'anomaly_results': [self._anomaly_to_dict(a) for a in anomaly_results],
            'anomaly_summary': anomaly_summary,
            'topic_result': self._topic_to_dict(topic_result),
            'risk_result': self._risk_to_dict(risk_result),
            'report': self.report_generator.to_markdown(report) if report else None,
            'report_json': self.report_generator.to_json(report) if report else None
        }
    
    def analyze_directory(self, 
                         dir_path: str,
                         generate_report: bool = True) -> Dict:
        """
        分析目录下所有文件
        
        Args:
            dir_path: 目录路径
            generate_report: 是否生成报告
        
        Returns:
            分析结果字典
        """
        logger.info(f"开始分析目录: {dir_path}")
        
        # 标准化所有评论
        comments = self.normalizer.normalize_directory(dir_path)
        if not comments:
            logger.warning("未找到有效评论数据")
            return {'error': '未找到有效评论数据'}
        
        # 转换为字典列表
        comment_dicts = [c.to_dict() for c in comments]
        
        # 执行分析 (同上)
        sentiment_results = self.sentiment_analyzer.analyze_batch(
            [c['content'] for c in comment_dicts]
        )
        sentiment_dicts = [
            {
                'sentiment': r.sentiment,
                'score': r.score,
                'risk_score': r.risk_score,
                'risk_level': r.risk_level,
                'keywords': r.keywords,
                'sensitive_words': r.sensitive_words,
                'content': comment_dicts[i]['content'][:100]
            }
            for i, r in enumerate(sentiment_results)
        ]
        
        bot_results = self.bot_detector.detect(comment_dicts)
        anomaly_results = self.anomaly_detector.detect(comment_dicts, sentiment_dicts)
        topic_result = self.topic_analyzer.analyze(comment_dicts, sentiment_dicts)
        
        sentiment_summary = self.sentiment_analyzer.get_sentiment_distribution(sentiment_results)
        bot_summary = self.bot_detector.get_summary(bot_results)
        anomaly_summary = self.anomaly_detector.get_summary(anomaly_results)
        
        risk_result = self.risk_assessment.assess(
            sentiment_summary=sentiment_summary,
            bot_summary=bot_summary,
            anomaly_summary=anomaly_summary,
            total_comments=len(comments)
        )
        
        report = None
        if generate_report:
            times = [c.get('publish_time') for c in comment_dicts if c.get('publish_time')]
            time_range = {'start': min(times), 'end': max(times)} if times else {}
            
            # 统计平台分布
            platforms = set(c.get('platform', 'unknown') for c in comment_dicts)
            platform_str = ', '.join(platforms)
            
            report = self.report_generator.generate(
                data_source=dir_path,
                time_range=time_range,
                platform=platform_str,
                total_comments=len(comments),
                risk_assessment=risk_result,
                sentiment_results=sentiment_dicts,
                bot_results=bot_results,
                anomaly_results=anomaly_results,
                topic_result=topic_result
            )
        
        return {
            'comments': comment_dicts,
            'sentiment_results': sentiment_dicts,
            'sentiment_summary': sentiment_summary,
            'bot_results': {k: self._bot_to_dict(v) for k, v in bot_results.items()},
            'bot_summary': bot_summary,
            'anomaly_results': [self._anomaly_to_dict(a) for a in anomaly_results],
            'anomaly_summary': anomaly_summary,
            'topic_result': self._topic_to_dict(topic_result),
            'risk_result': self._risk_to_dict(risk_result),
            'report': self.report_generator.to_markdown(report) if report else None,
            'report_json': self.report_generator.to_json(report) if report else None
        }
    
    def _bot_to_dict(self, result: BotDetectionResult) -> Dict:
        """转换 BotDetectionResult 为字典"""
        return {
            'user_id': result.user_id,
            'user_name': result.user_name,
            'platform': result.platform,
            'overall_risk_score': result.overall_risk_score,
            'risk_level': result.risk_level,
            'frequency_score': result.frequency_score,
            'repetition_score': result.repetition_score,
            'account_score': result.account_score,
            'behavior_score': result.behavior_score,
            'total_comments': result.total_comments,
            'avg_comments_per_hour': result.avg_comments_per_hour,
            'content_similarity': result.content_similarity,
            'unique_contents': result.unique_contents,
            'reasons': result.reasons
        }
    
    def _anomaly_to_dict(self, result: AnomalyResult) -> Dict:
        """转换 AnomalyResult 为字典"""
        return {
            'anomaly_type': result.anomaly_type,
            'severity': result.severity,
            'score': result.score,
            'description': result.description,
            'affected_count': result.affected_count,
            'time_window': result.time_window,
            'details': result.details
        }
    
    def _topic_to_dict(self, result: TopicResult) -> Dict:
        """转换 TopicResult 为字典"""
        return {
            'top_keywords': result.top_keywords,
            'topic_clusters': result.topic_clusters,
            'sentiment_orientation': result.sentiment_orientation,
            'sensitive_keywords': result.sensitive_keywords,
            'trending_score': result.trending_score
        }
    
    def _risk_to_dict(self, result: RiskAssessmentResult) -> Dict:
        """转换 RiskAssessmentResult 为字典"""
        return {
            'overall_score': result.overall_score,
            'risk_level': result.risk_level,
            'sentiment_risk': result.sentiment_risk,
            'account_risk': result.account_risk,
            'behavior_risk': result.behavior_risk,
            'content_risk': result.content_risk,
            'trend': result.trend,
            'warnings': result.warnings,
            'recommendations': result.recommendations
        }


# 便捷函数
def analyze(file_path: str, **kwargs) -> Dict:
    """便捷函数 - 快速分析单个文件"""
    analyzer = SecurityAnalyzer()
    return analyzer.analyze_file(file_path, **kwargs)


def analyze_dir(dir_path: str, **kwargs) -> Dict:
    """便捷函数 - 快速分析目录"""
    analyzer = SecurityAnalyzer()
    return analyzer.analyze_directory(dir_path, **kwargs)
