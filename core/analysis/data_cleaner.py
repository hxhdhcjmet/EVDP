"""
EVDP 数据清洗模块
高性能数据清洗与标准化引擎

特性:
- 多平台支持 (B站/贴吧/知乎/抖音)
- 智能字段映射
- 内容清洗与规范化
- 高性能批量处理
"""

import json
import re
import hashlib
from datetime import datetime
from typing import List, Dict, Optional, Generator, Any
from pathlib import Path
from dataclasses import asdict
import logging

# 导入模型
import sys
sys.path.insert(0, str(Path(__file__).parent.parent.parent))
from core.analysis.models import UnifiedComment, CleaningReport

logger = logging.getLogger(__name__)


class ContentCleaner:
    """内容清洗器 - 高效清洗评论内容"""
    
    # 编译正则表达式 (性能优化)
    HTML_TAG_PATTERN = re.compile(r'<[^>]+>')
    URL_PATTERN = re.compile(r'https?://\S+')
    MENTION_PATTERN = re.compile(r'@[\w\u4e00-\u9fa5]+')
    EMOJI_PATTERN = re.compile(r'\[[\w\u4e00-\u9fa5]+\]')
    MULTI_SPACE_PATTERN = re.compile(r'\s+')
    MULTI_NEWLINE_PATTERN = re.compile(r'\n+')
    
    def __init__(self):
        self.stats = {
            'html_removed': 0,
            'url_marked': 0,
            'mention_marked': 0,
            'emoji_normalized': 0,
            'whitespace_normalized': 0
        }
    
    def clean(self, content: str) -> tuple:
        """
        清洗内容
        
        Returns:
            (清洗后内容, 元数据)
        """
        if not content:
            return '', self._empty_metadata()
        
        original_length = len(content)
        metadata = {
            'length': original_length,
            'has_emoji': False,
            'has_url': False,
            'has_mention': False,
            'emoji_count': 0,
            'url_count': 0,
            'mention_count': 0
        }
        
        # 1. 去除HTML标签
        content, count = self._remove_html(content)
        self.stats['html_removed'] += count
        
        # 2. 标记URL
        urls = self.URL_PATTERN.findall(content)
        metadata['url_count'] = len(urls)
        metadata['has_url'] = len(urls) > 0
        self.stats['url_marked'] += len(urls)
        
        # 3. 标记@提及
        mentions = self.MENTION_PATTERN.findall(content)
        metadata['mention_count'] = len(mentions)
        metadata['has_mention'] = len(mentions) > 0
        self.stats['mention_marked'] += len(mentions)
        
        # 4. 标准化表情符号 [doge] 等
        emojis = self.EMOJI_PATTERN.findall(content)
        metadata['emoji_count'] = len(emojis)
        metadata['has_emoji'] = len(emojis) > 0
        self.stats['emoji_normalized'] += len(emojis)
        
        # 5. 标准化空白字符
        content = self.MULTI_SPACE_PATTERN.sub(' ', content)
        content = self.MULTI_NEWLINE_PATTERN.sub('\n', content)
        content = content.strip()
        self.stats['whitespace_normalized'] += 1
        
        # 更新长度
        metadata['length'] = len(content)
        
        return content, metadata
    
    def _remove_html(self, content: str) -> tuple:
        """去除HTML标签"""
        cleaned = self.HTML_TAG_PATTERN.sub('', content)
        count = len(content) - len(cleaned)
        return cleaned, count
    
    def _empty_metadata(self) -> Dict:
        """空元数据"""
        return {
            'length': 0,
            'has_emoji': False,
            'has_url': False,
            'has_mention': False,
            'emoji_count': 0,
            'url_count': 0,
            'mention_count': 0
        }
    
    def get_stats(self) -> Dict:
        """获取清洗统计"""
        return self.stats.copy()


class PlatformParser:
    """平台解析器基类"""
    
    @staticmethod
    def detect(file_path: str) -> bool:
        """检测是否匹配该平台"""
        raise NotImplementedError
    
    @staticmethod
    def parse(data: Dict, cleaner: ContentCleaner) -> List[UnifiedComment]:
        """解析单条数据"""
        raise NotImplementedError


class BilibiliParser(PlatformParser):
    """B站解析器"""
    
    @staticmethod
    def detect(file_path: str) -> bool:
        path_lower = file_path.lower()
        return 'bili' in path_lower or 'bilibili' in path_lower
    
    @staticmethod
    def parse(data: Dict, cleaner: ContentCleaner) -> List[UnifiedComment]:
        """解析B站评论"""
        comments = []
        
        # 主评论
        user_info = data.get('user', {})
        ip_raw = user_info.get('ip', '')
        ip_location = ip_raw.replace('IP属地：', '') if ip_raw else None
        
        # 清洗内容
        content, metadata = cleaner.clean(data.get('comment', ''))
        
        # 解析时间
        publish_time = None
        if data.get('ctime'):
            try:
                publish_time = datetime.fromtimestamp(data['ctime'])
            except:
                pass
        
        # 生成评论ID
        comment_id = data.get('rpid')
        if not comment_id:
            # 使用内容hash生成ID
            comment_id = f"bili_{hashlib.md5(content.encode()).hexdigest()[:12]}"
        
        main_comment = UnifiedComment(
            comment_id=str(comment_id),
            platform='bilibili',
            content=content,
            user_name=user_info.get('name', '未知用户'),
            user_id=str(user_info.get('mid', '')) if user_info.get('mid') else None,
            user_level=user_info.get('level'),
            like_count=data.get('like', 0),
            reply_count=data.get('reply_count', 0),
            publish_time=publish_time,
            ip_location=ip_location,
            is_reply=False,
            parent_id=None,
            content_metadata=metadata,
            raw_data=data
        )
        comments.append(main_comment)
        
        # 解析子回复
        for idx, reply in enumerate(data.get('replies', [])):
            reply_user = reply
            if isinstance(reply.get('user'), dict):
                reply_user = reply['user']
                reply_name = reply_user.get('name', '未知用户')
            else:
                reply_name = reply.get('user', '未知用户')
            
            reply_ip = reply.get('ip', '').replace('IP属地：', '') if reply.get('ip') else None
            
            # 清洗回复内容
            reply_content, reply_metadata = cleaner.clean(reply.get('comment', ''))
            
            reply_comment = UnifiedComment(
                comment_id=f"{main_comment.comment_id}_reply_{idx}",
                platform='bilibili',
                content=reply_content,
                user_name=reply_name,
                user_level=reply_user.get('level') if isinstance(reply_user, dict) else None,
                like_count=reply.get('like', 0),
                ip_location=reply_ip,
                is_reply=True,
                parent_id=main_comment.comment_id,
                content_metadata=reply_metadata,
                raw_data=reply
            )
            comments.append(reply_comment)
        
        return comments


class TiebaParser(PlatformParser):
    """贴吧解析器"""
    
    @staticmethod
    def detect(file_path: str) -> bool:
        path_lower = file_path.lower()
        return 'tieba' in path_lower or 'tid_' in path_lower
    
    @staticmethod
    def parse(data: Dict, cleaner: ContentCleaner) -> List[UnifiedComment]:
        """解析贴吧评论"""
        comments = []
        
        # 解析时间
        time_str = data.get('time', '')
        publish_time = None
        if time_str:
            try:
                publish_time = datetime.strptime(time_str, '%Y-%m-%d %H:%M')
            except:
                pass
        
        # 清洗内容
        content, metadata = cleaner.clean(data.get('content', ''))
        
        main_comment = UnifiedComment(
            comment_id=str(data.get('pid', '')),
            platform='tieba',
            content=content,
            user_name=data.get('author', '未知用户'),
            user_id=str(data.get('user_id', '')),
            like_count=0,  # 贴吧无点赞数据
            reply_count=data.get('total_lzl', 0),
            publish_time=publish_time,
            ip_location=data.get('ip_location'),
            is_reply=False,
            parent_id=None,
            content_metadata=metadata,
            raw_data=data
        )
        comments.append(main_comment)
        
        # 解析子回复 (如果有)
        for idx, sub_reply in enumerate(data.get('sub_replies', [])):
            sub_content, sub_metadata = cleaner.clean(sub_reply.get('content', ''))
            
            sub_comment = UnifiedComment(
                comment_id=f"{main_comment.comment_id}_sub_{idx}",
                platform='tieba',
                content=sub_content,
                user_name=sub_reply.get('author', '未知用户'),
                is_reply=True,
                parent_id=main_comment.comment_id,
                content_metadata=sub_metadata,
                raw_data=sub_reply
            )
            comments.append(sub_comment)
        
        return comments


class ZhihuParser(PlatformParser):
    """知乎解析器"""
    
    @staticmethod
    def detect(file_path: str) -> bool:
        return 'zhihu' in file_path.lower()
    
    @staticmethod
    def parse(data: Dict, cleaner: ContentCleaner) -> List[UnifiedComment]:
        """解析知乎内容"""
        content, metadata = cleaner.clean(data.get('content', ''))
        
        # 知乎数据特殊,可能是文章内容而非评论
        return [UnifiedComment(
            comment_id=f"zhihu_{hashlib.md5(content[:100].encode()).hexdigest()[:12]}",
            platform='zhihu',
            content=content,
            user_name='知乎用户',
            source_url=data.get('url'),
            content_metadata=metadata,
            raw_data=data
        )]


class DataCleaner:
    """
    数据清洗器 - 主控制器
    
    Features:
    - 自动平台检测
    - 高性能批量处理
    - 生成清洗报告
    - 支持流式处理 (大数据集)
    """
    
    def __init__(self, 
                 chunk_size: int = 1000,
                 enable_stats: bool = True):
        """
        初始化
        
        Args:
            chunk_size: 批量处理大小
            enable_stats: 是否启用统计
        """
        self.chunk_size = chunk_size
        self.enable_stats = enable_stats
        
        # 初始化组件
        self.content_cleaner = ContentCleaner()
        
        # 平台解析器
        self.parsers = {
            'bilibili': BilibiliParser(),
            'tieba': TiebaParser(),
            'zhihu': ZhihuParser()
        }
        
        # 统计数据
        self.report = CleaningReport()
    
    def clean_file(self, 
                   file_path: str, 
                   platform: str = None) -> List[UnifiedComment]:
        """
        清洗单个文件
        
        Args:
            file_path: JSONL 文件路径
            platform: 平台名称 (自动检测)
        
        Returns:
            统一格式的评论列表
        """
        path = Path(file_path)
        
        if not path.exists():
            logger.error(f"文件不存在: {file_path}")
            self.report.errors.append(f"文件不存在: {file_path}")
            return []
        
        # 自动检测平台
        if platform is None:
            platform = self._detect_platform(file_path)
        
        if platform not in self.parsers:
            logger.error(f"不支持的平台: {platform}")
            self.report.errors.append(f"不支持的平台: {platform}")
            return []
        
        logger.info(f"开始清洗: {file_path} (平台: {platform})")
        
        comments = []
        parser = self.parsers[platform]
        
        with open(path, 'r', encoding='utf-8') as f:
            for line_num, line in enumerate(f, 1):
                line = line.strip()
                if not line:
                    continue
                
                try:
                    raw_data = json.loads(line)
                    self.report.total_raw += 1
                    
                    # 解析并清洗
                    parsed = parser.parse(raw_data, self.content_cleaner)
                    comments.extend(parsed)
                    self.report.total_cleaned += len(parsed)
                    
                    # 更新平台统计
                    self.report.platform_stats[platform] = \
                        self.report.platform_stats.get(platform, 0) + len(parsed)
                    
                except json.JSONDecodeError as e:
                    error_msg = f"第 {line_num} 行 JSON 解析失败: {e}"
                    logger.warning(error_msg)
                    self.report.errors.append(error_msg)
                except Exception as e:
                    error_msg = f"第 {line_num} 行处理失败: {e}"
                    logger.warning(error_msg)
                    self.report.errors.append(error_msg)
        
        # 更新清洗统计
        self.report.cleaning_stats = self.content_cleaner.get_stats()
        
        # 更新质量统计
        self._update_quality_stats(comments)
        
        logger.info(f"清洗完成: {len(comments)} 条评论")
        return comments
    
    def clean_directory(self, dir_path: str) -> List[UnifiedComment]:
        """
        清洗目录下所有 JSONL 文件
        
        Args:
            dir_path: 目录路径
        
        Returns:
            统一格式的评论列表
        """
        dir_path = Path(dir_path)
        
        if not dir_path.exists():
            logger.error(f"目录不存在: {dir_path}")
            self.report.errors.append(f"目录不存在: {dir_path}")
            return []
        
        all_comments = []
        
        # 递归查找所有 JSONL 文件
        for jsonl_file in dir_path.rglob('*.jsonl'):
            comments = self.clean_file(str(jsonl_file))
            all_comments.extend(comments)
        
        logger.info(f"目录清洗完成: 共 {len(all_comments)} 条评论")
        return all_comments
    
    def clean_file_stream(self, 
                          file_path: str,
                          platform: str = None) -> Generator[UnifiedComment, None, None]:
        """
        流式清洗 (大数据集)
        
        Yields:
            UnifiedComment
        """
        path = Path(file_path)
        
        if not path.exists():
            return
        
        if platform is None:
            platform = self._detect_platform(file_path)
        
        if platform not in self.parsers:
            return
        
        parser = self.parsers[platform]
        
        with open(path, 'r', encoding='utf-8') as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                
                try:
                    raw_data = json.loads(line)
                    comments = parser.parse(raw_data, self.content_cleaner)
                    yield from comments
                except:
                    continue
    
    def _detect_platform(self, file_path: str) -> str:
        """自动检测平台"""
        # 检测文件名
        for platform, parser in self.parsers.items():
            if parser.detect(file_path):
                return platform
        
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
    
    def _update_quality_stats(self, comments: List[UnifiedComment]):
        """更新质量统计"""
        total = len(comments)
        
        if total == 0:
            return
        
        with_ip = sum(1 for c in comments if c.ip_location)
        with_time = sum(1 for c in comments if c.publish_time)
        with_level = sum(1 for c in comments if c.user_level)
        replies = sum(1 for c in comments if c.is_reply)
        
        self.report.quality_stats = {
            'total': total,
            'with_ip': with_ip,
            'with_ip_ratio': with_ip / total,
            'with_time': with_time,
            'with_time_ratio': with_time / total,
            'with_user_level': with_level,
            'with_user_level_ratio': with_level / total,
            'replies': replies,
            'replies_ratio': replies / total
        }
    
    def get_report(self) -> CleaningReport:
        """获取清洗报告"""
        return self.report
    
    def reset_stats(self):
        """重置统计"""
        self.report = CleaningReport()
        self.content_cleaner = ContentCleaner()


# 便捷函数
def clean_file(file_path: str, **kwargs) -> List[UnifiedComment]:
    """便捷函数 - 清洗单个文件"""
    cleaner = DataCleaner()
    return cleaner.clean_file(file_path, **kwargs)


def clean_dir(dir_path: str, **kwargs) -> List[UnifiedComment]:
    """便捷函数 - 清洗目录"""
    cleaner = DataCleaner()
    return cleaner.clean_directory(dir_path, **kwargs)
