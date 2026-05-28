"""Load and summarize local EVDP data for AI analysis."""

from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional
from collections import Counter
import json


@dataclass
class AIDataContext:
    source_file: str
    platform: str
    total_rows: int
    sampled_rows: int
    stats: Dict = field(default_factory=dict)
    samples: List[Dict] = field(default_factory=list)

    def to_prompt_text(self) -> str:
        sample_lines = []
        for idx, item in enumerate(self.samples, 1):
            content = str(item.get("content") or item.get("comment") or item.get("text") or "")[:500]
            user = item.get("user_name") or item.get("author") or item.get("user") or "unknown"
            ip = item.get("ip_location") or item.get("ip") or ""
            like = item.get("like_count") or item.get("like") or 0
            sample_lines.append(
                f"{idx}. 用户={user} IP={ip} 点赞={like} 内容={content}"
            )

        stats_text = json.dumps(self.stats, ensure_ascii=False, indent=2)
        return (
            f"数据源: {self.source_file}\n"
            f"平台: {self.platform}\n"
            f"总行数: {self.total_rows}\n"
            f"抽样行数: {self.sampled_rows}\n"
            f"统计摘要:\n{stats_text}\n\n"
            f"抽样评论:\n" + "\n".join(sample_lines)
        )


def infer_platform(path: Path) -> str:
    text = str(path).lower()
    if "bili" in text or "bilibili" in text:
        return "bilibili"
    if "douyin" in text:
        return "douyin"
    if "tieba" in text or "tid_" in text:
        return "tieba"
    if "zhihu" in text:
        return "zhihu"
    return "unknown"


def _extract_content(row: Dict) -> str:
    return str(row.get("content") or row.get("comment") or row.get("text") or "")


def _extract_ip(row: Dict) -> str:
    user = row.get("user")
    if isinstance(user, dict):
        ip = user.get("ip") or ""
        return str(ip).replace("IP属地：", "")
    return str(row.get("ip_location") or row.get("ip") or "")


def _extract_time(row: Dict) -> Optional[str]:
    for key in ("publish_time", "time", "created_at"):
        if row.get(key):
            return str(row[key])
    if row.get("ctime"):
        try:
            return datetime.fromtimestamp(row["ctime"]).isoformat()
        except Exception:
            return None
    return None


def load_jsonl(path: Path, max_rows: int = 5000) -> List[Dict]:
    rows = []
    with path.open("r", encoding="utf-8") as f:
        for line in f:
            if len(rows) >= max_rows:
                break
            line = line.strip()
            if not line:
                continue
            try:
                rows.append(json.loads(line))
            except json.JSONDecodeError:
                continue
    return rows


def build_data_context(path: Path, sample_size: int = 80, max_rows: int = 5000) -> AIDataContext:
    rows = load_jsonl(path, max_rows=max_rows)
    total = len(rows)
    if total == 0:
        return AIDataContext(
            source_file=str(path),
            platform=infer_platform(path),
            total_rows=0,
            sampled_rows=0,
        )

    contents = [_extract_content(row).strip() for row in rows]
    contents = [c for c in contents if c]
    ips = [_extract_ip(row).strip() for row in rows if _extract_ip(row).strip()]
    times = [_extract_time(row) for row in rows]
    times = [t for t in times if t]

    # Deterministic spread sampling keeps the prompt representative and reproducible.
    if total <= sample_size:
        samples = rows
    else:
        step = max(total // sample_size, 1)
        samples = rows[::step][:sample_size]

    content_lengths = [len(c) for c in contents]
    duplicate_count = len(contents) - len(set(contents))
    stats = {
        "content_count": len(contents),
        "avg_content_length": round(sum(content_lengths) / len(content_lengths), 2) if content_lengths else 0,
        "duplicate_ratio": round(duplicate_count / len(contents), 4) if contents else 0,
        "top_ip_locations": Counter(ips).most_common(10),
        "with_ip_ratio": round(len(ips) / total, 4),
        "with_time_ratio": round(len(times) / total, 4),
        "short_comment_ratio": round(sum(1 for c in contents if len(c) < 10) / len(contents), 4) if contents else 0,
    }

    return AIDataContext(
        source_file=str(path),
        platform=infer_platform(path),
        total_rows=total,
        sampled_rows=len(samples),
        stats=stats,
        samples=samples,
    )
