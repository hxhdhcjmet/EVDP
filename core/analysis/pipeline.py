"""
舆情安全分析流水线

将所有分析模块串联为一条完整链路：
清洗 → 情感分析 → IP溯源 → 用户画像 → 综合评分
"""

from typing import List, Dict, Optional
from dataclasses import dataclass, field
from datetime import datetime
import logging

logger = logging.getLogger(__name__)


@dataclass
class PipelineReport:
    """流水线完整分析报告"""

    # 元信息
    source_file: str = ""
    platform: str = ""
    generated_at: str = ""

    # 各阶段结果（原始对象）
    cleaning_report: object = None
    sentiment_distribution: Dict = field(default_factory=dict)
    ip_result: object = None
    user_profiling: Dict = field(default_factory=dict)   # {platform: UserProfilingResult}
    anomalies: List = field(default_factory=list)

    # 综合评分
    overall_score: int = 0           # 0-100，越高越危险
    overall_level: str = "low"       # low / medium / high / critical
    score_breakdown: Dict = field(default_factory=dict)

    # 关键发现（汇总）
    key_findings: List[str] = field(default_factory=list)
    recommendations: List[str] = field(default_factory=list)

    # 统计摘要
    total_comments: int = 0
    high_risk_comments: int = 0
    suspicious_users: int = 0


class SecurityPipeline:
    """
    舆情安全分析流水线

    用法:
        pipeline = SecurityPipeline()
        report = pipeline.run("/path/to/data.jsonl")
    """

    def __init__(self, risk_threshold: int = 60, analysis_limit: int = 500):
        """
        Args:
            risk_threshold: 高风险评论判定阈值
            analysis_limit:  情感分析最大条数（性能保护）
        """
        self.risk_threshold = risk_threshold
        self.analysis_limit = analysis_limit

        # 延迟导入，避免循环依赖
        from core.analysis.data_cleaner import DataCleaner
        from core.analysis.sentiment_analyzer import SentimentAnalyzer
        from core.analysis.ip_analyzer import IPAnalyzer
        from core.analysis.user_profiler import UserProfiler

        self.cleaner = DataCleaner()
        self.sentiment = SentimentAnalyzer()
        self.ip_analyzer = IPAnalyzer()
        self.user_profiler = UserProfiler()

    def run(self, file_path: str, progress_callback=None) -> PipelineReport:
        """
        执行完整分析流水线

        Args:
            file_path: JSONL 数据文件路径
            progress_callback: 可选进度回调 fn(step: int, total: int, msg: str)

        Returns:
            PipelineReport
        """
        report = PipelineReport(
            source_file=file_path,
            generated_at=datetime.now().isoformat()
        )

        def _progress(step, msg):
            if progress_callback:
                progress_callback(step, 4, msg)
            logger.info(f"[Pipeline {step}/4] {msg}")

        # ── Step 1: 数据清洗 ──────────────────────────────────────────
        _progress(1, "数据清洗与标准化...")
        try:
            comments = self.cleaner.clean_file(file_path)
            report.cleaning_report = self.cleaner.get_report()
            report.total_comments = len(comments)
            report.platform = report.cleaning_report.platform_stats and \
                list(report.cleaning_report.platform_stats.keys())[0] or "unknown"

            if not comments:
                report.key_findings.append("数据清洗后无有效评论")
                return report
        except Exception as e:
            logger.error(f"清洗失败: {e}")
            report.key_findings.append(f"数据清洗失败: {e}")
            return report

        # 转为字典列表（后续模块统一使用）
        comment_dicts = [self._comment_to_dict(c) for c in comments]

        # ── Step 2: 情感分析 ──────────────────────────────────────────
        _progress(2, "情感分析与风险评估...")
        try:
            sample = comment_dicts[:self.analysis_limit]
            sentiment_results = self.sentiment.analyze_batch(sample)
            report.sentiment_distribution = self.sentiment.get_distribution(sentiment_results)
            report.high_risk_comments = report.sentiment_distribution.get("high_risk", 0)

            # 将情感结果回写到 comment_dicts（供后续使用）
            sentiment_map = {r.comment_id: r for r in sentiment_results}
            for cd in comment_dicts:
                sr = sentiment_map.get(cd["comment_id"])
                if sr:
                    cd["sentiment"] = sr.sentiment
                    cd["sentiment_score"] = sr.sentiment_score
                    cd["risk_score"] = sr.risk_score
        except Exception as e:
            logger.warning(f"情感分析失败: {e}")

        # ── Step 3: IP 地域溯源 ───────────────────────────────────────
        _progress(3, "IP 地域溯源分析...")
        try:
            report.ip_result = self.ip_analyzer.analyze(comment_dicts)
        except Exception as e:
            logger.warning(f"IP 分析失败: {e}")

        # ── Step 4: 用户行为画像 ──────────────────────────────────────
        _progress(4, "用户行为画像分析...")
        try:
            report.user_profiling = self.user_profiler.analyze(comment_dicts)
            report.suspicious_users = sum(
                len(pr.suspicious_users)
                for pr in report.user_profiling.values()
            )
        except Exception as e:
            logger.warning(f"用户画像失败: {e}")

        # 综合评分
        report.overall_score, report.overall_level, report.score_breakdown = (
            self._calc_overall_score(report)
        )
        report.key_findings = self._collect_findings(report)
        report.recommendations = self._generate_recommendations(report)

        return report

    # ------------------------------------------------------------------ #
    #  综合评分
    # ------------------------------------------------------------------ #

    def _calc_overall_score(self, r: PipelineReport):
        """
        综合评分算法（满分100）

        权重分配:
          情感风险    40%
          IP 地域     30%
          用户画像    30%
        """
        breakdown = {}

        # 1. 情感风险分
        sentiment_score = 0
        if r.sentiment_distribution:
            neg_ratio = r.sentiment_distribution.get("negative_ratio", 0)
            high_risk_ratio = r.sentiment_distribution.get("high_risk_ratio", 0)
            avg_risk = r.sentiment_distribution.get("avg_risk_score", 0)
            sentiment_score = int(
                neg_ratio * 40 + high_risk_ratio * 40 + avg_risk * 0.2
            )
            sentiment_score = min(sentiment_score, 100)
        breakdown["sentiment"] = sentiment_score

        # 2. IP 地域分
        ip_score = 0
        if r.ip_result and r.ip_result.has_sufficient_ip:
            ip_score = r.ip_result.suspicion_score
        elif r.ip_result and not r.ip_result.has_sufficient_ip:
            ip_score = 0   # 数据不足，不计入
        breakdown["ip"] = ip_score

        # 3. 用户画像分
        user_score = 0
        if r.user_profiling:
            all_scores = []
            for pr in r.user_profiling.values():
                if pr.analyzed_users > 0:
                    all_scores.append(pr.avg_suspicion_score)
            if all_scores:
                user_score = int(sum(all_scores) / len(all_scores))
        breakdown["user"] = user_score

        # 加权总分
        # 若 IP 数据不足，将其权重分配给其他维度
        if r.ip_result and not r.ip_result.has_sufficient_ip:
            total = int(
                breakdown["sentiment"] * 0.50 +
                breakdown["user"] * 0.50
            )
        else:
            total = int(
                breakdown["sentiment"] * 0.40 +
                breakdown["ip"] * 0.30 +
                breakdown["user"] * 0.30
            )

        total = min(total, 100)

        if total >= 80:
            level = "critical"
        elif total >= 60:
            level = "high"
        elif total >= 35:
            level = "medium"
        else:
            level = "low"

        # 异常检测分（如果可用）
        breakdown["anomaly"] = 0

        return total, level, breakdown

    # ------------------------------------------------------------------ #
    #  发现汇总 & 建议
    # ------------------------------------------------------------------ #

    def _collect_findings(self, r: PipelineReport) -> List[str]:
        findings = []

        # 情感
        if r.sentiment_distribution:
            neg = r.sentiment_distribution.get("negative_ratio", 0)
            if neg > 0.5:
                findings.append(f"负面情感占比 {neg:.1%}，舆论氛围偏负面")
            hr = r.sentiment_distribution.get("high_risk_ratio", 0)
            if hr > 0.1:
                findings.append(f"高风险评论占比 {hr:.1%}，含敏感内容")

        # IP
        if r.ip_result:
            findings.extend(r.ip_result.findings)

        # 用户画像
        for pr in r.user_profiling.values():
            findings.extend(pr.findings)

        return findings[:15]  # 最多15条

    def _generate_recommendations(self, r: PipelineReport) -> List[str]:
        recs = []

        if r.overall_level in ("high", "critical"):
            recs.append("建议人工复核高风险评论，评估是否需要上报")

        if r.suspicious_users > 0:
            recs.append(f"建议关注 {r.suspicious_users} 个可疑账号，追踪其后续行为")

        if r.ip_result and r.ip_result.wave_detected:
            recs.append("检测到波浪式传播，建议追踪源头省份的账号")

        if r.high_risk_comments > 10:
            recs.append("高风险评论数量较多，建议扩大敏感词库覆盖范围")

        if not recs:
            recs.append("当前数据风险较低，保持常规监测即可")

        return recs

    # ------------------------------------------------------------------ #
    #  工具方法
    # ------------------------------------------------------------------ #

    def _comment_to_dict(self, comment) -> Dict:
        """将 UnifiedComment 对象转为字典"""
        try:
            return {
                "comment_id": comment.comment_id,
                "platform": comment.platform,
                "content": comment.content,
                "user_name": comment.user_name,
                "user_id": comment.user_id,
                "user_level": comment.user_level,
                "like_count": comment.like_count,
                "reply_count": comment.reply_count,
                "publish_time": (
                    comment.publish_time.isoformat()
                    if comment.publish_time else None
                ),
                "ip_location": comment.ip_location,
                "is_reply": comment.is_reply,
                "parent_id": comment.parent_id,
            }
        except Exception:
            return {}
