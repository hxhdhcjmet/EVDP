"""
数据标准化模块
统一不同平台的评论数据结构
"""

import json
import re
from datetime import datetime
from typing import List, Dict, Any, Optional
from dataclasses import dataclass, asdict
from pathlib import Path
import logging

logger = logging.getLogger(__name__)


@dataclass
class UnifiedComment:
    """统一的评论数据结构"""
    # 基本信息
    comment_id: str                    # 评论唯一标识
    platform: str                      # 平台: bilibili/douyin/tieba/zhihu
    content: str                       # 评论内容

    # 用户信息
    user_name: str                     # 用户名
    user_id: Optional[str] = None     # 用户ID
    user_level: Optional[int] = None  # 用户等级

    # 互动数据
    like_count: int = 0               # 点赞数
    reply_count: int = 0              # 回复数

    # 时间和位置
    publish_time: Optional[datetime] = None  # 发布时间
    ip_location: Optional[str] = None        # IP属地

    # 元数据
    source_url: Optional[str] = None   # 来源链接
    parent_id: Optional[str] = None    # 父评论ID (如果是回复)

    # 原始数据 (用于调试)
    raw_data: Optional[Dict] = None

    def to_dict(self) -> Dict:
        """转换为字典"""
        data = asdict(self)
        if self.publish_time:
            data['publish_time'] = self.publish_time.isoformat()
        return data


class DataNormalizer:
    """数据标准化器 - 统一不同平台的评论格式"""

    def __init__(self):
        self.platform_handlers = {
            'bilibili': self._normalize_bilibili,
            'tieba': self._normalize_tieba,
            'zhihu': self._normalize_zhihu,
            'douyin': self._normalize_douyin
        }

    def normalize_file(self, file_path: str, platform: str = None) -> List[UnifiedComment]:
        """
        标准化 JSONL 文件

        Args:
            file_path: JSONL 文件路径
            platform: 平台名称 (如果为None则自动检测)

        Returns:
            统一格式的评论列表
        """
        # 自动检测平台
        if platform is None:
            platform = self._detect_platform(file_path)

        if platform not in self.platform_handlers:
            raise ValueError(f"不支持的平台: {platform}")

        comments = []
        path = Path(file_path)

        if not path.exists():
            logger.error(f"文件不存在: {file_path}")
            return comments

        with open(path, 'r', encoding='utf-8') as f:
            for line_num, line in enumerate(f, 1):
                line = line.strip()
                if not line:
                    continue

                try:
                    raw_data = json.loads(line)
                    normalized = self.platform_handlers[platform](raw_data)

                    # 处理嵌套回复
                    if isinstance(normalized, list):
                        comments.extend(normalized)
                    else:
                        comments.append(normalized)

                except json.JSONDecodeError as e:
                    logger.warning(f"第 {line_num} 行 JSON 解析失败: {e}")
                except Exception as e:
                    logger.warning(f"第 {line_num} 行处理失败: {e}")

        logger.info(f"成功加载 {len(comments)} 条评论 (平台: {platform})")
        return comments

    def normalize_directory(self, dir_path: str) -> List[UnifiedComment]:
        """
        标准化目录下所有 JSONL 文件

        Args:
            dir_path: 目录路径

        Returns:
            统一格式的评论列表
        """
        all_comments = []
        dir_path = Path(dir_path)

        if not dir_path.exists():
            logger.error(f"目录不存在: {dir_path}")
            return all_comments

        # 递归查找所有 JSONL 文件
        for jsonl_file in dir_path.rglob('*.jsonl'):
            platform = self._detect_platform(str(jsonl_file))
            comments = self.normalize_file(str(jsonl_file), platform)
            all_comments.extend(comments)

        logger.info(f"共加载 {len(all_comments)} 条评论")
        return all_comments

    def _detect_platform(self, file_path: str) -> str:
        """根据文件路径/内容检测平台"""
        path_lower = file_path.lower()

        if 'bili' in path_lower or 'bilibili' in path_lower:
            return 'bilibili'
        elif 'tieba' in path_lower or 'tid_' in path_lower:
            return 'tieba'
        elif 'zhihu' in path_lower:
            return 'zhihu'
        elif 'douyin' in path_lower or 'tiktok' in path_lower:
            return 'douyin'

        # 尝试读取第一行判断
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                first_line = f.readline().strip()
                if first_line:
                    data = json.loads(first_line)

                    # B站特征
                    if 'comment' in data and 'ctime' in data:
                        return 'bilibili'
                    # 贴吧特征
                    elif 'pid' in data and 'floor' in data:
                        return 'tieba'
                    # 知乎特征
                    elif 'type' in data and 'content' in data:
                        return 'zhihu'
        except:
            pass

        return 'unknown'

    def _normalize_bilibili(self, data: Dict) -> List[UnifiedComment]:
        """
        标准化 B站评论
        原始格式: {"comment": "xxx", "like": 7, "reply_count": 0, "ctime": 1771303006,
                  "user": {"name": "xxx", "level": 3, "ip": "IP属地：安徽"}, "replies": [...]}
        """
        comments = []

        # 主评论
        user_info = data.get('user', {})
        ip_raw = user_info.get('ip', '')
        ip_location = ip_raw.replace('IP属地：', '') if ip_raw else None

        main_comment = UnifiedComment(
            comment_id=str(data.get('rpid', data.get('id', ''))),
            platform='bilibili',
            content=data.get('comment', ''),
            user_name=user_info.get('name', '未知用户'),
            user_id=str(user_info.get('mid', '')),
            user_level=user_info.get('level'),
            like_count=data.get('like', 0),
            reply_count=data.get('reply_count', 0),
            publish_time=datetime.fromtimestamp(data.get('ctime', 0)) if data.get('ctime') else None,
            ip_location=ip_location,
            raw_data=data
        )
        comments.append(main_comment)

        # 子回复
        for reply in data.get('replies', []):
            reply_user = reply if isinstance(reply.get('user'), dict) else reply
            reply_ip = reply.get('ip', '').replace('IP属地：', '') if reply.get('ip') else None

            reply_comment = UnifiedComment(
                comment_id=f"{main_comment.comment_id}_reply_{reply.get('id', '')}",
                platform='bilibili',
                content=reply.get('comment', ''),
                user_name=reply_user.get('user', {}).get('name', reply_user.get('name', '未知用户')) if isinstance(reply_user.get('user'), dict) else reply.get('user', '未知用户'),
                user_level=reply_user.get('level'),
                like_count=reply.get('like', 0),
                ip_location=reply_ip,
                parent_id=main_comment.comment_id,
                raw_data=reply
            )
            comments.append(reply_comment)

        return comments

    def _normalize_tieba(self, data: Dict) -> UnifiedComment:
        """
        标准化贴吧评论
        原始格式: {"pid": 144540649992, "floor": 1, "user_id": 3506977221, "author": "呆唯",
                  "ip_location": "山东", "content": "xxx", "time": "2022-06-24 11:11"}
        """
        time_str = data.get('time', '')
        publish_time = None
        if time_str:
            try:
                publish_time = datetime.strptime(time_str, '%Y-%m-%d %H:%M')
            except:
                pass

        return UnifiedComment(
            comment_id=str(data.get('pid', '')),
            platform='tieba',
            content=data.get('content', ''),
            user_name=data.get('author', '未知用户'),
            user_id=str(data.get('user_id', '')),
            like_count=0,  # 贴吧无点赞数据
            reply_count=data.get('total_lzl', 0),
            publish_time=publish_time,
            ip_location=data.get('ip_location'),
            raw_data=data
        )

    def _normalize_zhihu(self, data: Dict) -> UnifiedComment:
        """
        标准化知乎评论
        原始格式: {"type": "article_body", "content": "xxx", "url": "xxx"}
        注意: 知乎数据可能需要根据实际爬虫结构调整
        """
        return UnifiedComment(
            comment_id=str(hash(data.get('content', '')[:100])),  # 使用内容hash作为ID
            platform='zhihu',
            content=data.get('content', ''),
            user_name='知乎用户',  # 需要根据实际爬虫数据调整
            source_url=data.get('url'),
            raw_data=data
        )

    def _normalize_douyin(self, data: Dict) -> UnifiedComment:
        """
        标准化抖音评论
        注意: 需要根据实际爬虫数据结构调整
        """
        return UnifiedComment(
            comment_id=str(data.get('cid', '')),
            platform='douyin',
            content=data.get('text', data.get('content', '')),
            user_name=data.get('nickname', data.get('user_name', '抖音用户')),
            user_id=str(data.get('user_id', '')),
            like_count=data.get('digg_count', data.get('like_count', 0)),
            reply_count=data.get('reply_comment_total', 0),
            ip_location=data.get('ip_label', data.get('ip_location')),
            raw_data=data
        )

    def to_dataframe(self, comments: List[UnifiedComment]):
        """
        转换为 DataFrame (用于后续分析)

        Args:
            comments: 统一格式的评论列表

        Returns:
            pandas DataFrame
        """
        import pandas as pd

        records = []
        for comment in comments:
            record = {
                'comment_id': comment.comment_id,
                'platform': comment.platform,
                'content': comment.content,
                'user_name': comment.user_name,
                'user_id': comment.user_id,
                'user_level': comment.user_level,
                'like_count': comment.like_count,
                'reply_count': comment.reply_count,
                'publish_time': comment.publish_time,
                'ip_location': comment.ip_location,
                'content_length': len(comment.content),
                'has_emoji': bool(re.search(r'[\U0001F600-\U0001F64F\U0001F300-\U0001F5FF\U0001F680-\U0001F6FF\U0001F700-\U0001F77F\U0001F780-\U0001F7FF\U0001F800-\U0001F8FF\U0001F900-\U0001F9FF\U0001FA00-\U0001FA6F\U0001FA70-\U0001FAFF\U00002702-\U000027B0]', comment.content))
            }
            records.append(record)

        df = pd.DataFrame(records)

        # 时间处理
        if 'publish_time' in df.columns:
            df['hour'] = df['publish_time'].dt.hour
            df['weekday'] = df['publish_time'].dt.weekday
            df['date'] = df['publish_time'].dt.date

        return df
