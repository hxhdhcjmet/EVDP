import json
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Any
from dataclasses import dataclass

@dataclass
class ReportConfig:
    formats: List[str] = None
    def __post_init__(self):
        if self.formats is None:
            self.formats = ['md', 'json']

class ReportGenerator:
    def __init__(self, pipeline_report, config=None):
        self.report = pipeline_report
        self.config = config or ReportConfig()
        self.generated_at = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

    def save(self, output_dir: str, source_url: str = '') -> Dict[str, str]:
        output_path = Path(output_dir)
        output_path.mkdir(parents=True, exist_ok=True)
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        saved_files = {}
        for fmt in self.config.formats:
            if fmt == 'md':
                fp = output_path / f'security_report_{timestamp}.md'
                fp.write_text(self._gen_md(source_url), encoding='utf-8')
                saved_files['markdown'] = str(fp)
            elif fmt == 'json':
                fp = output_path / f'security_report_{timestamp}.json'
                fp.write_text(self._gen_json(source_url), encoding='utf-8')
                saved_files['json'] = str(fp)
            elif fmt == 'html':
                fp = output_path / f'security_report_{timestamp}.html'
                fp.write_text(self._gen_html(source_url), encoding='utf-8')
                saved_files['html'] = str(fp)
            elif fmt == 'txt':
                fp = output_path / f'security_report_{timestamp}.txt'
                fp.write_text(self._gen_txt(source_url), encoding='utf-8')
                saved_files['text'] = str(fp)
        return saved_files

    def _pct(self, v, t): return f'{v/t*100:.1f}%' if t else '0.0%'

    def _basic(self, url):
        return {
            'generated_at': self.generated_at,
            'source_file': getattr(self.report, 'source_file', 'Unknown'),
            'source_url': url,
            'platform': getattr(self.report, 'platform', 'Unknown'),
            'total_comments': getattr(self.report, 'total_comments', 0),
            'high_risk_comments': getattr(self.report, 'high_risk_comments', 0),
            'suspicious_users': getattr(self.report, 'suspicious_users', 0),
        }

    def _risk(self):
        return {
            'score': getattr(self.report, 'overall_score', 0),
            'level': getattr(self.report, 'overall_level', 'unknown'),
            'breakdown': getattr(self.report, 'score_breakdown', {}),
        }

    def _sentiment(self):
        d = getattr(self.report, 'sentiment_distribution', {}) or {}
        return {'positive': d.get('positive', 0), 'negative': d.get('negative', 0), 'neutral': d.get('neutral', 0)}

    def _ip(self):
        ip = getattr(self.report, 'ip_result', None)
        if not ip: return None
        return {
            'provinces': getattr(ip, 'province_distribution', {}),
            'gini': getattr(ip, 'gini_coefficient', 0),
            'top3': getattr(ip, 'top3_ratio', 0),
            'suspicion': getattr(ip, 'suspicion_score', 0),
        }

    def _anomalies(self):
        a = getattr(self.report, 'anomalies', None)
        if not a: return []
        return [{'type': x.type, 'severity': x.severity, 'desc': x.description, 'count': x.affected_count} for x in a[:10]]

    def _findings(self):
        f = getattr(self.report, 'key_findings', None)
        return f if f else []
    
    def _recs(self):
        r = getattr(self.report, 'recommendations', None)
        return r if r else []

    def _gen_md(self, url):
        b, r, s = self._basic(url), self._risk(), self._sentiment()
        ip, a = self._ip(), self._anomalies()
        lines = [
            '# 舆情安全分析报告', '',
            '## 基本信息',
            f'- **分析时间**: {b["generated_at"]}',
            f'- **来源链接**: {url or "未提供"}',
            f'- **平台**: {b["platform"].upper()}',
            f'- **总评论数**: {b["total_comments"]}',
            f'- **高风险评论**: {b["high_risk_comments"]}', '',
            '## 风险评估',
            f'- **评分**: {r["score"]}/100',
            f'- **等级**: {r["level"].upper()}', '',
            '## 情感分析',
            f'- 正面: {s["positive"]} ({self._pct(s["positive"], b["total_comments"])})',
            f'- 负面: {s["negative"]} ({self._pct(s["negative"], b["total_comments"])})',
            f'- 中立: {s["neutral"]} ({self._pct(s["neutral"], b["total_comments"])})',
        ]
        if ip:
            lines.extend(['', '## IP地域分析', f'- 基尼系数: {ip["gini"]:.3f}', f'- 前3省份占比: {ip["top3"]:.1%}'])
        if a:
            lines.append('\n## 异常检测')
            for x in a:
                lines.append(f"- [{x['severity'].upper()}] {x['type']}: {x['desc']}")
        findings = self._findings()
        if findings:
            lines.append('\n## 关键发现')
            for f in findings:
                lines.append(f'- {f}')
        recs = self._recs()
        if recs:
            lines.append('\n## 建议措施')
            for i, rec in enumerate(recs, 1):
                lines.append(f'{i}. {rec}')
        lines.extend(['', '---', f'*报告生成时间: {b["generated_at"]}*', '*EVDP 舆情安全分析系统*'])
        return '\n'.join(lines)

    def _gen_json(self, url):
        return json.dumps({
            'basic': self._basic(url), 'risk': self._risk(), 'sentiment': self._sentiment(),
            'ip': self._ip(), 'anomalies': self._anomalies(),
            'findings': self._findings(), 'recommendations': self._recs()
        }, ensure_ascii=False, indent=2)

    def _gen_html(self, url):
        b, r, s = self._basic(url), self._risk(), self._sentiment()
        return f'''<!DOCTYPE html>
<html><head><meta charset="utf-8"><title>舆情安全分析报告</title>
<style>body{{font-family:sans-serif;max-width:900px;margin:0 auto;padding:20px}}
.card{{background:#f5f5f5;padding:20px;margin:10px 0;border-radius:8px}}
h1{{color:#333}}</style></head>
<body><h1>舆情安全分析报告</h1>
<div class="card"><h2>基本信息</h2>
<p>分析时间: {b["generated_at"]}</p>
<p>来源链接: {url or "未提供"}</p>
<p>平台: {b["platform"].upper()}</p>
<p>总评论数: {b["total_comments"]}</p></div>
<div class="card"><h2>风险评估</h2>
<p>评分: {r["score"]}/100 | 等级: {r["level"].upper()}</p></div>
<div class="card"><h2>情感分析</h2>
<p>正面: {s["positive"]} | 负面: {s["negative"]} | 中立: {s["neutral"]}</p></div>
<hr><p style="color:#999">报告生成时间: {b["generated_at"]} - EVDP 舆情安全分析系统</p>
</body></html>'''

    def _gen_txt(self, url):
        b, r, s = self._basic(url), self._risk(), self._sentiment()
        return f'''========================================
舆情安全分析报告
========================================

【基本信息】
分析时间: {b["generated_at"]}
来源链接: {url or "未提供"}
平台: {b["platform"].upper()}
总评论数: {b["total_comments"]}

【风险评估】
评分: {r["score"]}/100
等级: {r["level"].upper()}

【情感分析】
正面: {s["positive"]}
负面: {s["negative"]}
中立: {s["neutral"]}

========================================
报告生成时间: {b["generated_at"]}
EVDP 舆情安全分析系统
========================================'''
