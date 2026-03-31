"""
用户行为画像与可疑账号识别模块

功能:
- 按平台分别构建用户画像（有字段才有功能）
- 多维度可疑特征打分：发言频率、内容重复、等级异常、行为规律性
- 输出可疑账号列表 + 置信度
"""

import re
from typing import List, Dict, Optional, Tuple
from dataclasses import dataclass, field
from collections import Counter, defaultdict
from datetime import datetime
import logging

logger = logging.getLogger(__name__)


@dataclass
class UserProfile:
    """单个用户画像"""

    user_id: str
    user_name: str
    platform: str

    # 基础统计
    total_comments: int = 0
    is_reply: int = 0                    # 回复数
    total_likes: int = 0                 # 获赞总数
    avg_content_length: float = 0.0      # 平均内容长度

    # 平台特有字段（有则填，无则 None）
    user_level: Optional[int] = None     # B站用户等级
    avg_like_per_comment: float = 0.0    # 平均每条获赞

    # 内容特征
    unique_content_ratio: float = 1.0    # 唯一内容比例（1=全不重复）
    emoji_heavy: bool = False            # 是否大量使用表情
    short_content_ratio: float = 0.0     # 短评论（<5字）占比
    at_mention_ratio: float = 0.0        # 含@提及的评论占比

    # 时间特征（有时间数据才有）
    has_time_data: bool = False
    active_hours: List[int] = field(default_factory=list)   # 活跃小时分布
    time_regularity_score: float = 0.0   # 时间规律性 0=随机 1=极规律

    # 可疑度评分
    suspicion_score: int = 0             # 0-100
    suspicion_level: str = "low"         # low / medium / high
    suspicion_reasons: List[str] = field(default_factory=list)


@dataclass
class UserProfilingResult:
    """用户画像分析结果"""

    platform: str
    total_users: int = 0
    analyzed_users: int = 0              # 评论数 >= min_comments 的用户

    # 可疑账号
    suspicious_users: List[UserProfile] = field(default_factory=list)
    high_risk_count: int = 0
    medium_risk_count: int = 0

    # 整体特征
    avg_suspicion_score: float = 0.0
    level_distribution: Dict[str, int] = field(default_factory=dict)  # B站等级分布

    findings: List[str] = field(default_factory=list)


class UserProfiler:
    """
    用户行为画像分析器

    设计原则：有字段才分析，无字段不强行推断
    """

    def __init__(self, min_comments: int = 2):
        """
        Args:
            min_comments: 最少评论数才纳入画像分析
        """
        self.min_comments = min_comments

    def analyze(self, comments: List[Dict]) -> Dict[str, UserProfilingResult]:
        """
        按平台分别分析用户画像

        Args:
            comments: 统一格式评论字典列表

        Returns:
            {platform: UserProfilingResult}
        """
        # 按平台分组
        by_platform: Dict[str, List[Dict]] = defaultdict(list)
        for c in comments:
            by_platform[c.get("platform", "unknown")].append(c)

        results = {}
        for platform, platform_comments in by_platform.items():
            results[platform] = self._analyze_platform(platform, platform_comments)

        return results

    # ------------------------------------------------------------------ #
    #  平台级分析
    # ------------------------------------------------------------------ #

    def _analyze_platform(self, platform: str, comments: List[Dict]) -> UserProfilingResult:
        result = UserProfilingResult(platform=platform)

        # 按用户分组
        by_user: Dict[str, List[Dict]] = defaultdict(list)
        for c in comments:
            uid = c.get("user_id") or c.get("user_name") or "unknown"
            by_user[uid].append(c)

        result.total_users = len(by_user)

        # 等级分布（B站专有）
        if platform == "bilibili":
            levels = [
                c.get("user_level")
                for c in comments
                if c.get("user_level") is not None
            ]
            if levels:
                result.level_distribution = dict(Counter(levels))

        # 逐用户画像
        profiles = []
        for uid, user_comments in by_user.items():
            if len(user_comments) < self.min_comments:
                continue
            profile = self._build_profile(uid, user_comments, platform)
            profiles.append(profile)

        result.analyzed_users = len(profiles)

        if not profiles:
            result.findings.append(f"{platform}: 无用户满足最少评论数（{self.min_comments}条）要求")
            return result

        # 统计可疑账号
        result.suspicious_users = sorted(
            [p for p in profiles if p.suspicion_score >= 40],
            key=lambda x: x.suspicion_score,
            reverse=True
        )
        result.high_risk_count = sum(1 for p in profiles if p.suspicion_level == "high")
        result.medium_risk_count = sum(1 for p in profiles if p.suspicion_level == "medium")
        result.avg_suspicion_score = sum(p.suspicion_score for p in profiles) / len(profiles)

        # 整体发现
        result.findings = self._summarize_findings(result, platform)

        return result

    # ------------------------------------------------------------------ #
    #  单用户画像构建
    # ------------------------------------------------------------------ #

    def _build_profile(self, uid: str, comments: List[Dict], platform: str) -> UserProfile:
        sample = comments[0]
        profile = UserProfile(
            user_id=uid,
            user_name=sample.get("user_name", "未知用户"),
            platform=platform,
            total_comments=len(comments),
        )

        contents = [c.get("content", "") for c in comments]

        # ---- 基础统计 ----
        profile.is_reply = sum(1 for c in comments if c.get("is_reply"))
        profile.total_likes = sum(c.get("like_count", 0) for c in comments)
        profile.avg_like_per_comment = profile.total_likes / len(comments)
        profile.avg_content_length = (
            sum(len(ct) for ct in contents) / len(contents) if contents else 0
        )

        # ---- 平台特有：用户等级（B站）----
        if platform == "bilibili":
            levels = [c.get("user_level") for c in comments if c.get("user_level") is not None]
            if levels:
                profile.user_level = int(sum(levels) / len(levels))

        # ---- 内容特征 ----
        unique_contents = set(ct.strip() for ct in contents if ct.strip())
        profile.unique_content_ratio = len(unique_contents) / len(contents)

        short_count = sum(1 for ct in contents if len(ct.strip()) < 5)
        profile.short_content_ratio = short_count / len(contents)

        at_count = sum(1 for ct in contents if re.search(r"@\S+", ct))
        profile.at_mention_ratio = at_count / len(contents)

        emoji_bracket = re.compile(r"\[[\w\u4e00-\u9fa5_]+\]")
        emoji_unicode = re.compile(
            r"[\U0001F600-\U0001F64F\U0001F300-\U0001F5FF\U0001F680-\U0001F6FF]"
        )
        total_emoji = sum(
            len(emoji_bracket.findall(ct)) + len(emoji_unicode.findall(ct))
            for ct in contents
        )
        profile.emoji_heavy = (total_emoji / len(contents)) > 3

        # ---- 时间特征 ----
        times = self._extract_times(comments)
        if len(times) >= 2:
            profile.has_time_data = True
            profile.active_hours = [t.hour for t in times]
            profile.time_regularity_score = self._calc_time_regularity(times)

        # ---- 可疑度评分 ----
        profile.suspicion_score, profile.suspicion_level, profile.suspicion_reasons = (
            self._score_suspicion(profile)
        )

        return profile

    # ------------------------------------------------------------------ #
    #  辅助计算
    # ------------------------------------------------------------------ #

    def _extract_times(self, comments: List[Dict]) -> List[datetime]:
        times = []
        for c in comments:
            t = c.get("publish_time")
            if not t:
                continue
            if isinstance(t, str):
                try:
                    t = datetime.fromisoformat(t)
                except Exception:
                    continue
            if isinstance(t, datetime):
                times.append(t)
        return sorted(times)

    def _calc_time_regularity(self, times: List[datetime]) -> float:
        """
        计算发言时间规律性
        通过相邻评论时间间隔的变异系数（CV）衡量
        CV 越小 → 间隔越规律 → 越可疑
        """
        if len(times) < 3:
            return 0.0

        intervals = [
            (times[i + 1] - times[i]).total_seconds()
            for i in range(len(times) - 1)
        ]
        mean = sum(intervals) / len(intervals)
        if mean == 0:
            return 1.0  # 瞬间发多条，极度规律

        variance = sum((x - mean) ** 2 for x in intervals) / len(intervals)
        std = variance ** 0.5
        cv = std / mean  # 变异系数

        # CV 越小越规律，转换为 0-1 规律性分数
        regularity = max(0.0, 1.0 - min(cv, 2.0) / 2.0)
        return round(regularity, 3)

    def _score_suspicion(self, p: UserProfile) -> Tuple[int, str, List[str]]:
        """多维度可疑度打分"""
        score = 0
        reasons = []

        # 1. 内容重复（权重高）
        if p.unique_content_ratio < 0.3:
            score += 40
            reasons.append(f"内容高度重复（唯一率 {p.unique_content_ratio:.1%}）")
        elif p.unique_content_ratio < 0.6:
            score += 20
            reasons.append(f"内容存在重复（唯一率 {p.unique_content_ratio:.1%}）")

        # 2. 短评论刷屏
        if p.short_content_ratio > 0.8:
            score += 25
            reasons.append(f"大量极短评论（{p.short_content_ratio:.1%} 少于5字）")
        elif p.short_content_ratio > 0.5:
            score += 10

        # 3. 时间规律性（有时间数据才判断）
        if p.has_time_data:
            if p.time_regularity_score > 0.85:
                score += 25
                reasons.append(f"发言时间高度规律（规律性 {p.time_regularity_score:.2f}）")
            elif p.time_regularity_score > 0.65:
                score += 10

        # 4. 低等级高频（B站专有）
        if p.user_level is not None:
            if p.user_level <= 1 and p.total_comments >= 5:
                score += 20
                reasons.append(f"低等级账号（Lv{p.user_level}）高频发言（{p.total_comments}条）")
            elif p.user_level <= 2 and p.total_comments >= 10:
                score += 10

        # 5. 用户名特征
        name = p.user_name
        if re.match(r"^贴吧用户_[A-Za-z0-9]+$", name):
            score += 15
            reasons.append("用户名为系统生成格式（贴吧匿名用户）")
        elif re.match(r"^[a-zA-Z0-9_]{8,}$", name):
            score += 10
            reasons.append("用户名为纯字母数字（疑似自动注册）")

        score = min(score, 100)

        if score >= 60:
            level = "high"
        elif score >= 40:
            level = "medium"
        else:
            level = "low"

        if not reasons:
            reasons.append("未发现明显异常行为")

        return score, level, reasons

    def _summarize_findings(self, result: UserProfilingResult, platform: str) -> List[str]:
        findings = []

        if result.high_risk_count > 0:
            findings.append(
                f"发现 {result.high_risk_count} 个高风险账号"
                f"（占分析用户 {result.high_risk_count/result.analyzed_users:.1%}）"
            )

        if result.medium_risk_count > 0:
            findings.append(f"发现 {result.medium_risk_count} 个中风险账号")

        if result.avg_suspicion_score > 50:
            findings.append(f"整体账号可疑度偏高（均分 {result.avg_suspicion_score:.1f}/100）")

        # B站等级分布异常
        if platform == "bilibili" and result.level_distribution:
            low_level = sum(v for k, v in result.level_distribution.items() if int(k) <= 2)
            total_with_level = sum(result.level_distribution.values())
            if total_with_level > 0 and low_level / total_with_level > 0.5:
                findings.append(
                    f"低等级用户（Lv0-2）占比 {low_level/total_with_level:.1%}，账号质量偏低"
                )

        if not findings:
            findings.append("用户行为整体正常，未发现明显可疑账号")

        return findings
