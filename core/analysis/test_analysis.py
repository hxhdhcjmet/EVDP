#!/usr/bin/env python3
"""
测试数据清洗和情感分析模块
"""

import sys
sys.path.insert(0, '/home/EVDP')

from core.analysis import (
    DataCleaner,
    SentimentAnalyzer,
    UnifiedComment,
    clean_file
)

def test_data_cleaner():
    """测试数据清洗"""
    print("=" * 60)
    print("测试数据清洗模块")
    print("=" * 60)
    
    cleaner = DataCleaner()
    
    # 测试 B站数据
    bili_file = "/home/EVDP/data/bili_BV1A6ZMB3Ebd_0/bili_BV1A6ZMB3Ebd_0.jsonl"
    
    print(f"\n清洗文件: {bili_file}")
    comments = cleaner.clean_file(bili_file)
    
    print(f"\n✓ 成功清洗 {len(comments)} 条评论")
    
    # 显示清洗报告
    report = cleaner.get_report()
    print(f"\n清洗报告:")
    print(f"  原始数据: {report.total_raw} 条")
    print(f"  清洗后: {report.total_cleaned} 条")
    print(f"  平台统计: {report.platform_stats}")
    print(f"\n质量统计:")
    for key, value in report.quality_stats.items():
        if isinstance(value, float):
            print(f"  {key}: {value:.2%}")
        else:
            print(f"  {key}: {value}")
    
    print(f"\n清洗统计:")
    for key, value in report.cleaning_stats.items():
        print(f"  {key}: {value}")
    
    # 显示前3条评论
    print("\n" + "=" * 60)
    print("示例数据 (前3条)")
    print("=" * 60)
    
    for i, comment in enumerate(comments[:3], 1):
        print(f"\n评论 {i}:")
        print(f"  ID: {comment.comment_id}")
        print(f"  平台: {comment.platform}")
        print(f"  用户: {comment.user_name} (等级: {comment.user_level})")
        print(f"  内容: {comment.content[:50]}...")
        print(f"  IP: {comment.ip_location}")
        print(f"  点赞: {comment.like_count}")
        print(f"  是否回复: {comment.is_reply}")
        
        if comment.content_metadata:
            metadata = comment.content_metadata
            print(f"  内容特征:")
            print(f"    - 长度: {metadata.get('length', 0)}")
            print(f"    - 含表情: {metadata.get('has_emoji', False)}")
            print(f"    - 含URL: {metadata.get('has_url', False)}")
            print(f"    - 含@: {metadata.get('has_mention', False)}")
    
    return comments


def test_sentiment_analyzer(comments):
    """测试情感分析"""
    print("\n" + "=" * 60)
    print("测试情感分析模块")
    print("=" * 60)
    
    analyzer = SentimentAnalyzer()
    
    # 转换为字典列表
    comment_dicts = [
        {
            'comment_id': c.comment_id,
            'content': c.content
        }
        for c in comments[:50]  # 只测试前50条
    ]
    
    print(f"\n分析 {len(comment_dicts)} 条评论...")
    
    results = analyzer.analyze_batch(comment_dicts)
    
    print(f"✓ 成功分析 {len(results)} 条评论")
    
    # 显示情感分布
    distribution = analyzer.get_distribution(results)
    
    print(f"\n情感分布:")
    print(f"  总数: {distribution['total']}")
    print(f"  正面: {distribution['positive']} ({distribution['positive_ratio']:.1%})")
    print(f"  负面: {distribution['negative']} ({distribution['negative_ratio']:.1%})")
    print(f"  中立: {distribution['neutral']} ({distribution['neutral_ratio']:.1%})")
    print(f"\n  含敏感词: {distribution['with_sensitive']} ({distribution['with_sensitive_ratio']:.1%})")
    print(f"  高风险: {distribution['high_risk']} ({distribution['high_risk_ratio']:.1%})")
    print(f"\n  平均情感分数: {distribution['avg_sentiment_score']:.3f}")
    print(f"  平均风险分数: {distribution['avg_risk_score']:.1f}")
    
    # 显示高风险评论
    high_risk = [r for r in results if r.risk_score >= 60]
    
    if high_risk:
        print(f"\n" + "=" * 60)
        print(f"高风险评论 (共 {len(high_risk)} 条)")
        print("=" * 60)
        
        for i, result in enumerate(high_risk[:5], 1):
            print(f"\n{i}. {result.content[:60]}...")
            print(f"   风险评分: {result.risk_score}/100 ({result.risk_level})")
            print(f"   情感: {result.sentiment} ({result.sentiment_score:.3f})")
            if result.sensitive_words:
                print(f"   敏感词: {[w['word'] for w in result.sensitive_words]}")
            print(f"   风险因素: {result.risk_factors}")
    
    return results


def test_tieba_data():
    """测试贴吧数据"""
    print("\n" + "=" * 60)
    print("测试贴吧数据清洗")
    print("=" * 60)
    
    cleaner = DataCleaner()
    tieba_file = "/home/EVDP/data/tid_7892470381/posts.jsonl"
    
    comments = cleaner.clean_file(tieba_file)
    
    print(f"✓ 成功清洗 {len(comments)} 条贴吧评论")
    
    # 显示平台统计
    report = cleaner.get_report()
    print(f"平台统计: {report.platform_stats}")
    
    return comments


def main():
    """主测试函数"""
    print("\n" + "=" * 70)
    print("EVDP 数据清洗与情感分析测试")
    print("=" * 70)
    
    # 1. 测试数据清洗
    comments = test_data_cleaner()
    
    if not comments:
        print("\n没有数据,测试终止")
        return
    
    # 2. 测试情感分析
    sentiment_results = test_sentiment_analyzer(comments)
    
    # 3. 测试贴吧数据
    tieba_comments = test_tieba_data()
    
    print("\n" + "=" * 70)
    print("✓ 所有测试完成!")
    print("=" * 70)


if __name__ == "__main__":
    main()
