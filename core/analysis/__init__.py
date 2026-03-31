"""
EVDP 分析模块
数据清洗、情感分析、IP溯源、用户画像、异常检测、综合流水线
"""

from .models import UnifiedComment, CleaningReport
from .data_cleaner import DataCleaner, clean_file, clean_dir
from .sentiment_analyzer import (
    SentimentAnalyzer,
    SentimentResult,
    analyze_sentiment,
    analyze_sentiment_batch
)
from .ip_analyzer import IPAnalyzer, IPAnalysisResult
from .user_profiler import UserProfiler, UserProfile, UserProfilingResult
from .pipeline import SecurityPipeline, PipelineReport

__all__ = [
    # 数据模型
    "UnifiedComment",
    "CleaningReport",
    
    # 数据清洗
    "DataCleaner",
    "clean_file",
    "clean_dir",
    
    # 情感分析
    "SentimentAnalyzer",
    "SentimentResult",
    "analyze_sentiment",
    "analyze_sentiment_batch",
    
    # IP 地域分析
    "IPAnalyzer",
    "IPAnalysisResult",
    
    # 用户画像
    "UserProfiler",
    "UserProfile",
    "UserProfilingResult",
    
    # 综合流水线
    "SecurityPipeline",
    "PipelineReport",
]

__version__ = "2.0.0"
