"""
EVDP 分析模块
数据清洗、情感分析、IP溯源、用户画像、综合流水线、报告生成
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
from .report_generator import ReportGenerator, ReportConfig

# 延迟导入 pipeline 以避免循环依赖
def __getattr__(name):
    if name == "SecurityPipeline":
        from .pipeline import SecurityPipeline
        return SecurityPipeline
    elif name == "PipelineReport":
        from .pipeline import PipelineReport
        return PipelineReport
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")

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

    # 报告生成
    "ReportGenerator",
    "ReportConfig",

    # 综合流水线
    "SecurityPipeline",
    "PipelineReport",
]

__version__ = "2.1.0"
