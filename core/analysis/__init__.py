"""
EVDP 分析模块
数据清洗与情感分析
"""

from .models import UnifiedComment, CleaningReport
from .data_cleaner import DataCleaner, clean_file, clean_dir
from .sentiment_analyzer import (
    SentimentAnalyzer,
    SentimentResult,
    analyze_sentiment,
    analyze_sentiment_batch
)

__all__ = [
    "UnifiedComment",
    "CleaningReport",
    "DataCleaner",
    "clean_file",
    "clean_dir",
    "SentimentAnalyzer",
    "SentimentResult",
    "analyze_sentiment",
    "analyze_sentiment_batch"
]

__version__ = "1.0.0"
