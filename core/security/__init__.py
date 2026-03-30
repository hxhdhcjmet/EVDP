"""
EVDP 安全分析模块
社交媒体舆情安全监测平台 - 核心分析引擎
"""

from .data_normalizer import DataNormalizer, UnifiedComment
from .sentiment_analyzer import SentimentAnalyzer
from .bot_detector import BotDetector
from .anomaly_detector import AnomalyDetector
from .risk_assessment import RiskAssessment
from .topic_analyzer import TopicAnalyzer
from .report_generator import ReportGenerator
from .security_analyzer import SecurityAnalyzer, analyze, analyze_dir

__all__ = [
    "DataNormalizer",
    "UnifiedComment", 
    "SentimentAnalyzer",
    "BotDetector",
    "AnomalyDetector",
    "RiskAssessment",
    "TopicAnalyzer",
    "ReportGenerator",
    "SecurityAnalyzer",
    "analyze",
    "analyze_dir"
]

__version__ = "1.0.0"
