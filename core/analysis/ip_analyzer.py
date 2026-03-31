"""
IP 地域溯源与传播路径分析模块

功能:
- 统计评论 IP 属地省级分布
- 计算地域集中度（基尼系数）
- 识别跨地域协同传播特征
- 输出传播路径可疑度评分
"""

from typing import List, Dict, Optional, Tuple
from dataclasses import dataclass, field
from collections import Counter, defaultdict
from datetime import datetime
import logging

logger = logging.getLogger(__name__)


@dataclass
class IPAnalysisResult:
    """IP 地域分析结果"""

    # 数据覆盖情况
    total_comments: int = 0
    comments_with_ip: int = 0
    ip_coverage_ratio: float = 0.0
    has_sufficient_ip: bool = False      # 是否有足够 IP 数据做分析

    # 地域分布
    province_distribution: Dict[str, int] = field(default_factory=dict)   # {省份: 数量}
    top_provinces: List[Tuple[str, int]] = field(default_factory=list)     # 前5省份

    # 集中度指标
    gini_coefficient: float = 0.0        # 基尼系数 0=完全分散 1=完全集中
    concentration_score: int = 0         # 集中度评分 0-100
    top3_ratio: float = 0.0              # 前3省份占比

    # 时间 × 地域传播特征
    time_geo_pattern: str = "unknown"    # normal / concentrated / wave_spread
    wave_detected: bool = False          # 是否检测到波浪式扩散

    # 综合可疑度
    suspicion_score: int = 0             # 0-100
    suspicion_level: str = "low"         # low / medium / high
    findings: List[str] = field(default_factory=list)   # 分析发现


class IPAnalyzer:
    """
    IP 地域溯源分析器

    注意: 仅支持省级精度（如"安徽"、"浙江"）
    当 IP 覆盖率低于阈值时，自动跳过分析并给出提示
    """

    # IP 覆盖率最低阈值，低于此值不做分析
    MIN_IP_COVERAGE = 0.3

    def __init__(self, min_ip_coverage: float = 0.3):
        self.min_ip_coverage = min_ip_coverage

    def analyze(self, comments: List[Dict]) -> IPAnalysisResult:
        """
        分析评论的 IP 地域分布

        Args:
            comments: 统一格式的评论字典列表，需含 ip_location 字段

        Returns:
            IPAnalysisResult
        """
        result = IPAnalysisResult()
        result.total_comments = len(comments)

        if not comments:
            result.findings.append("无评论数据")
            return result

        # 提取有效 IP 属地
        ip_list = [
            c.get("ip_location", "").strip()
            for c in comments
            if c.get("ip_location") and c.get("ip_location").strip()
        ]

        result.comments_with_ip = len(ip_list)
        result.ip_coverage_ratio = len(ip_list) / result.total_comments

        # 覆盖率不足 → 标记并返回
        if result.ip_coverage_ratio < self.min_ip_coverage:
            result.has_sufficient_ip = False
            result.findings.append(
                f"IP 属地覆盖率仅 {result.ip_coverage_ratio:.1%}（{result.comments_with_ip}/{result.total_comments} 条），"
                f"低于分析阈值 {self.min_ip_coverage:.0%}，跳过地域分析"
            )
            return result

        result.has_sufficient_ip = True

        # 省份分布统计
        province_counter = Counter(ip_list)
        result.province_distribution = dict(province_counter)
        result.top_provinces = province_counter.most_common(5)

        # 集中度分析
        result.gini_coefficient = self._calc_gini(list(province_counter.values()))
        result.top3_ratio = sum(v for _, v in province_counter.most_common(3)) / len(ip_list)
        result.concentration_score = self._gini_to_score(result.gini_coefficient)

        # 时间 × 地域传播模式
        result.wave_detected, result.time_geo_pattern = self._detect_wave_spread(comments)

        # 综合可疑度评分
        result.suspicion_score, result.suspicion_level, findings = self._calc_suspicion(result)
        result.findings.extend(findings)

        return result

    # ------------------------------------------------------------------ #
    #  内部方法
    # ------------------------------------------------------------------ #

    def _calc_gini(self, counts: List[int]) -> float:
        """计算基尼系数（衡量地域集中度）"""
        if not counts or len(counts) == 1:
            return 1.0  # 只有一个省份 → 完全集中

        counts_sorted = sorted(counts)
        n = len(counts_sorted)
        total = sum(counts_sorted)
        if total == 0:
            return 0.0

        cumulative = 0.0
        for i, v in enumerate(counts_sorted, 1):
            cumulative += v * (2 * i - n - 1)

        return cumulative / (n * total)

    def _gini_to_score(self, gini: float) -> int:
        """基尼系数转 0-100 集中度评分"""
        # gini 0.0 → score 0（完全分散，正常）
        # gini 1.0 → score 100（完全集中，可疑）
        return int(gini * 100)

    def _detect_wave_spread(self, comments: List[Dict]) -> Tuple[bool, str]:
        """
        检测波浪式扩散：
        正常讨论 → 地域随时间均匀出现
        组织传播 → 先从少数省份爆发，再向外扩散
        """
        # 提取带时间 + IP 的评论
        timed = []
        for c in comments:
            t = c.get("publish_time")
            ip = c.get("ip_location", "").strip()
            if not t or not ip:
                continue
            if isinstance(t, str):
                try:
                    t = datetime.fromisoformat(t)
                except Exception:
                    continue
            timed.append((t, ip))

        if len(timed) < 10:
            return False, "unknown"

        timed.sort(key=lambda x: x[0])

        # 将时间轴三等分，看各段的省份多样性
        n = len(timed)
        thirds = [
            timed[:n // 3],
            timed[n // 3: 2 * n // 3],
            timed[2 * n // 3:]
        ]

        diversity = [len(set(ip for _, ip in seg)) for seg in thirds]

        # 波浪式：第一段省份少，后续增多
        if diversity[0] <= 2 and diversity[2] >= diversity[0] * 2:
            return True, "wave_spread"

        # 集中式：始终只有少数省份
        if max(diversity) <= 3:
            return False, "concentrated"

        return False, "normal"

    def _calc_suspicion(self, r: "IPAnalysisResult") -> Tuple[int, str, List[str]]:
        """综合计算可疑度"""
        score = 0
        findings = []

        # 1. 地域高度集中
        if r.concentration_score >= 80:
            score += 40
            top1 = r.top_provinces[0] if r.top_provinces else ("?", 0)
            findings.append(
                f"地域高度集中：{top1[0]} 占 {top1[1]/r.comments_with_ip:.1%}，"
                f"基尼系数 {r.gini_coefficient:.2f}"
            )
        elif r.concentration_score >= 50:
            score += 20
            findings.append(f"地域较集中（基尼系数 {r.gini_coefficient:.2f}）")

        # 2. 前3省份占比过高
        if r.top3_ratio >= 0.85:
            score += 25
            findings.append(f"前3省份占比 {r.top3_ratio:.1%}，疑似区域性集中操作")
        elif r.top3_ratio >= 0.70:
            score += 10

        # 3. 波浪式扩散
        if r.wave_detected:
            score += 25
            findings.append("检测到波浪式扩散模式：评论从少数省份向外扩散，疑似有组织传播")

        # 4. 省份数量极少
        province_count = len(r.province_distribution)
        if province_count == 1:
            score += 20
            findings.append(f"所有评论仅来自 1 个省份（{list(r.province_distribution.keys())[0]}）")
        elif province_count <= 3:
            score += 10
            findings.append(f"评论仅来自 {province_count} 个省份，地域多样性极低")

        score = min(score, 100)

        if score >= 70:
            level = "high"
        elif score >= 40:
            level = "medium"
        else:
            level = "low"

        if not findings:
            findings.append("地域分布正常，未发现明显集中传播特征")

        return score, level, findings
