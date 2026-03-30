#!/usr/bin/env python3
"""
测试安全分析模块
使用现有的 B站评论数据进行测试
"""

import sys
import os

# 添加项目路径
sys.path.insert(0, '/home/EVDP')

from core.security import (
    DataNormalizer,
    SentimentAnalyzer,
    BotDetector,
    AnomalyDetector,
    RiskAssessment,
    TopicAnalyzer,
    ReportGenerator,
    SecurityAnalyzer
)

def test_data_normalizer():
    """测试数据标准化"""
    print("=" * 50)
    print("测试数据标准化模块")
    print("=" * 50)
    
    normalizer = DataNormalizer()
    
    # 测试 B站数据
    bili_file = "/home/EVDP/data/bili_BV1A6ZMB3Ebd_0/bili_BV1A6ZMB3Ebd_0.jsonl"
    if os.path.exists(bili_file):
        comments = normalizer.normalize_file(bili_file, 'bilibili')
        print(f"✓ 成功加载 {len(comments)} 条 B站评论")
        
        # 显示前3条
        for i, comment in enumerate(comments[:3], 1):
            print(f"\n评论 {i}:")
            print(f"  用户: {comment.user_name}")
            print(f"  内容: {comment.content[:50]}...")
            print(f"  IP: {comment.ip_location}")
            print(f"  点赞: {comment.like_count}")
        
        return comments
    else:
        print(f"✗ 文件不存在: {bili_file}")
        return []


def test_sentiment_analyzer(comments):
    """测试情感分析"""
    print("\n" + "=" * 50)
    print("测试情感分析模块")
    print("=" * 50)
    
    if not comments:
        print("✗ 没有评论数据")
        return []
    
    analyzer = SentimentAnalyzer()
    
    # 分析前10条
    contents = [c.content for c in comments[:10]]
    results = analyzer.analyze_batch(contents)
    
    print(f"✓ 成功分析 {len(results)} 条评论")
    
    # 显示结果
    for i, result in enumerate(results[:5], 1):
        print(f"\n评论 {i}:")
        print(f"  情感: {result.sentiment} (分数: {result.score:.3f})")
        print(f"  风险: {result.risk_level} (评分: {result.risk_score})")
        if result.sensitive_words:
            print(f"  敏感词: {result.sensitive_words}")
    
    # 获取分布
    all_results = analyzer.analyze_batch([c.content for c in comments])
    distribution = analyzer.get_sentiment_distribution(all_results)
    
    print("\n情感分布:")
    print(f"  正面: {distribution['positive']} ({distribution['positive_ratio']:.1%})")
    print(f"  负面: {distribution['negative']} ({distribution['negative_ratio']:.1%})")
    print(f"  中立: {distribution['neutral']} ({distribution['neutral_ratio']:.1%})")
    
    return all_results


def test_bot_detector(comments):
    """测试机器人检测"""
    print("\n" + "=" * 50)
    print("测试机器人检测模块")
    print("=" * 50)
    
    if not comments:
        print("✗ 没有评论数据")
        return {}
    
    detector = BotDetector()
    
    # 转换为字典
    comment_dicts = [
        {
            'comment_id': c.comment_id,
            'user_id': c.user_id,
            'user_name': c.user_name,
            'content': c.content,
            'publish_time': c.publish_time,
            'platform': c.platform,
            'user_level': c.user_level,
            'ip_location': c.ip_location
        }
        for c in comments
    ]
    
    results = detector.detect(comment_dicts)
    
    print(f"✓ 成功检测 {len(results)} 个用户")
    
    # 显示高风险用户
    high_risk = [r for r in results.values() if r.risk_level == 'high']
    medium_risk = [r for r in results.values() if r.risk_level == 'medium']
    
    print(f"\n高风险账号: {len(high_risk)}")
    print(f"中风险账号: {len(medium_risk)}")
    
    if high_risk:
        print("\n高风险账号详情:")
        for r in high_risk[:3]:
            print(f"  - {r.user_name}: 风险 {r.overall_risk_score}/100")
            print(f"    理由: {', '.join(r.reasons)}")
    
    return results


def test_anomaly_detector(comments, sentiment_results):
    """测试异常检测"""
    print("\n" + "=" * 50)
    print("测试异常检测模块")
    print("=" * 50)
    
    if not comments:
        print("✗ 没有评论数据")
        return []
    
    detector = AnomalyDetector()
    
    # 转换为字典
    comment_dicts = [
        {
            'comment_id': c.comment_id,
            'content': c.content,
            'publish_time': c.publish_time,
            'ip_location': c.ip_location
        }
        for c in comments
    ]
    
    sentiment_dicts = [
        {
            'sentiment': r.sentiment,
            'risk_score': r.risk_score
        }
        for r in sentiment_results
    ]
    
    results = detector.detect(comment_dicts, sentiment_dicts)
    
    print(f"✓ 检测到 {len(results)} 个异常")
    
    # 显示异常
    for r in results[:5]:
        print(f"\n  - 类型: {r.anomaly_type}")
        print(f"    严重程度: {r.severity}")
        print(f"    描述: {r.description}")
        print(f"    影响数量: {r.affected_count}")
    
    return results


def test_full_analysis():
    """测试完整分析流程"""
    print("\n" + "=" * 50)
    print("测试完整分析流程")
    print("=" * 50)
    
    analyzer = SecurityAnalyzer()
    
    bili_file = "/home/EVDP/data/bili_BV1A6ZMB3Ebd_0/bili_BV1A6ZMB3Ebd_0.jsonl"
    
    if not os.path.exists(bili_file):
        print(f"✗ 文件不存在: {bili_file}")
        return
    
    # 执行完整分析
    result = analyzer.analyze_file(bili_file)
    
    print("\n✓ 完整分析完成!")
    print(f"\n总评论数: {len(result['comments'])}")
    print(f"风险评分: {result['risk_result']['overall_score']}/100")
    print(f"风险等级: {result['risk_result']['risk_level']}")
    
    print("\n预警信息:")
    for warning in result['risk_result']['warnings']:
        print(f"  - {warning}")
    
    print("\n建议措施:")
    for rec in result['risk_result']['recommendations']:
        print(f"  - {rec}")
    
    # 保存报告
    if result['report']:
        report_path = "/home/EVDP/data/security_report.md"
        with open(report_path, 'w', encoding='utf-8') as f:
            f.write(result['report'])
        print(f"\n✓ 报告已保存: {report_path}")


def main():
    """主测试函数"""
    print("\n" + "=" * 60)
    print("EVDP 安全分析模块测试")
    print("=" * 60)
    
    # 1. 测试数据标准化
    comments = test_data_normalizer()
    
    if not comments:
        print("\n没有测试数据,测试终止")
        return
    
    # 2. 测试情感分析
    sentiment_results = test_sentiment_analyzer(comments)
    
    # 3. 测试机器人检测
    bot_results = test_bot_detector(comments)
    
    # 4. 测试异常检测
    anomaly_results = test_anomaly_detector(comments, sentiment_results)
    
    # 5. 测试完整流程
    test_full_analysis()
    
    print("\n" + "=" * 60)
    print("测试完成!")
    print("=" * 60)


if __name__ == "__main__":
    main()
