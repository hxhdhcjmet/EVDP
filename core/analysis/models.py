from dataclasses import dataclass
from typing import Dict, List, Optional
from datetime import datetime

@dataclass
class UnifiedComment:
    """统一评论数据结构"""
    
    # 基本信息
    comment_id: str                    # 评论唯一标识
    platform: str                      # 平台: bilibili/tieba/zhihu/douyin
    content: str                       # 评论内容 (已清洗)
    
    # 用户信息
    user_name: str                     # 用户名
    user_id: Optional[str] = None      # 用户ID
    user_level: Optional[int] = None   # 用户等级
    
    # 互动数据
    like_count: int = 0                # 点赞数
    reply_count: int = 0               # 回复数
    
    # 时间和位置
    publish_time: Optional[datetime] = None  # 发布时间
    ip_location: Optional[str] = None        # IP属地
    
    # 层级关系
    is_reply: bool = False             # 是否是回复
    parent_id: Optional[str] = None    # 父评论ID
    
    # 内容元数据
    content_metadata: Optional[Dict] = None  # 内容特征
    
    # 原始数据 (调试用)
    raw_data: Optional[Dict] = None
    
    def to_dict(self) -> Dict:
        """转换为字典"""
        data = {
            'comment_id': self.comment_id,
            'platform': self.platform,
            'content': self.content,
            'user_name': self.user_name,
            'user_id': self.user_id,
            'user_level': self.user_level,
            'like_count': self.like_count,
            'reply_count': self.reply_count,
            'publish_time': self.publish_time.isoformat() if self.publish_time else None,
            'ip_location': self.ip_location,
            'is_reply': self.is_reply,
            'parent_id': self.parent_id,
            'content_metadata': self.content_metadata,
        }
        return data


@dataclass
class CleaningReport:
    """数据清洗报告"""
    
    # 统计信息
    total_raw: int = 0                 # 原始数据条数
    total_cleaned: int = 0             # 清洗后数据条数
    
    # 平台统计
    platform_stats: Dict[str, int] = None  # {platform: count}
    
    # 质量统计
    quality_stats: Dict = None         # 质量相关统计
    
    # 清洗统计
    cleaning_stats: Dict = None        # 清洗操作统计
    
    # 错误信息
    errors: List[str] = None           # 错误信息列表
    
    def __post_init__(self):
        if self.platform_stats is None:
            self.platform_stats = {}
        if self.quality_stats is None:
            self.quality_stats = {}
        if self.cleaning_stats is None:
            self.cleaning_stats = {}
        if self.errors is None:
            self.errors = []
    
    def to_dict(self) -> Dict:
        """转换为字典"""
        return {
            'total_raw': self.total_raw,
            'total_cleaned': self.total_cleaned,
            'platform_stats': self.platform_stats,
            'quality_stats': self.quality_stats,
            'cleaning_stats': self.cleaning_stats,
            'errors': self.errors
        }
