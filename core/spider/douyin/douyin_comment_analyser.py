import os
import json
import jieba
import pandas as pd
import matplotlib
# 必须在导入 pyplot 之前设置后端为 Agg，防止在 Linux 服务器报错
matplotlib.use('Agg') 
import matplotlib.pyplot as plt
import matplotlib.font_manager as fm
import seaborn as sns
import math
from wordcloud import WordCloud
from collections import Counter
from snownlp import SnowNLP

class CommentVisualizer:
    def __init__(self, data_path):
        self.data_path = data_path
        # 路径计算逻辑
        current_file_dir = os.path.dirname(os.path.abspath(__file__))
        base_dir = os.path.dirname(os.path.dirname(os.path.dirname(current_file_dir)))
        self.assets_dir = os.path.join(base_dir, "assets")
        self.font_dir = os.path.join(self.assets_dir, "fonts")
        self.stop_file = os.path.join(self.assets_dir, "stopwords","douyin_stopwords.txt")
        
        # 1. 核心修复：注册中文字体到 Matplotlib
        self.custom_font_path = self._setup_matplotlib_fonts()
        
        # 2. 加载数据
        self.df = self._load_and_preprocess()
        print(f"数据文件夹{self.data_path}\n字体文件夹{self.font_dir}")

    def _setup_matplotlib_fonts(self):
        """将 assets 中的字体注册到系统，解决坐标轴乱码"""
        font_path = None
        if os.path.exists(self.font_dir):
            for file in os.listdir(self.font_dir):
                if file.lower().endswith(('.ttf', '.otf')):
                    font_path = os.path.join(self.font_dir, file)
                    break
        
        if font_path:
            # 动态注册字体
            fe = fm.FontEntry(fname=font_path, name='CustomFont')
            fm.fontManager.ttflist.insert(0, fe)
            # 设置全局默认字体
            plt.rcParams['font.sans-serif'] = ['CustomFont']
            plt.rcParams['axes.unicode_minus'] = False
            return font_path
        else:
            print(f"警告：{self.font_dir}目录下未找到字体文件，坐标轴将显示乱码。")
            return None

    def _load_and_preprocess(self):
        """读取 JSONL 文件"""
        data = []
        with open(self.data_path, 'r', encoding='utf-8') as f:
            for line in f:
                if line.strip():
                    try:
                        data.append(json.loads(line))
                    except: continue
        
        df = pd.DataFrame(data)
        if not df.empty:
            df['dt'] = pd.to_datetime(df['create_time'], unit='s')
            df['digg_count'] = pd.to_numeric(df['digg_count'], errors='coerce').fillna(0)
        return df

    def _get_stopwords(self):
        stops = {"的", "了", "在", "是", "我", "你", "他", "也", "就", "和", "回复", "评论", "视频", "看到"}
        if os.path.exists(self.stop_file):
            with open(self.stop_file, 'r', encoding='utf-8') as f:
                stops.update({line.strip() for line in f if line.strip()})
        return stops

    def plot_wordcloud(self):
        """绘制关键词云"""
        stops = self._get_stopwords()
        word_weights = Counter()
        for _, row in self.df.iterrows():
            words = jieba.cut(str(row['text']))
            valid_words = [w for w in words if len(w) > 1 and w not in stops and not w.isdigit()]
            for w in valid_words:
                word_weights[w] += 1 + math.log1p(row['digg_count'])

        if not word_weights or not self.custom_font_path:
            fig, ax = plt.subplots()
            ax.text(0.5, 0.5, "数据不足或缺少字体", ha='center')
            return fig

        wc = WordCloud(
            font_path=self.custom_font_path, # 使用 assets 里的字体
            background_color='white',
            width=1000, height=600,
            max_words=100
        ).generate_from_frequencies(word_weights)

        fig, ax = plt.subplots(figsize=(10, 6))
        ax.imshow(wc, interpolation='bilinear')
        ax.axis('off')
        ax.set_title("评论关键词云 (基于点赞权重)")
        return fig

    def plot_time_density(self):
        """绘制时间密度"""
        time_series = self.df.set_index('dt').resample('H').size().reset_index(name='count')
        fig, ax = plt.subplots(figsize=(10, 5))
        sns.lineplot(data=time_series, x='dt', y='count', ax=ax, color='#ff4b4b')
        ax.set_title("评论发布时间密度分布")
        plt.xticks(rotation=45)
        plt.tight_layout()
        return fig

    def plot_ip_distribution(self):
        """绘制 IP 分布"""
        ip_counts = self.df['ip_label'].value_counts()
        top_10 = ip_counts.head(10)
        others = pd.Series({"其他": ip_counts.iloc[10:].sum()})
        plot_data = pd.concat([top_10, others]) if others.values[0] > 0 else top_10

        fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(14, 6))
        sns.barplot(x=plot_data.index, y=plot_data.values, ax=ax1, palette="magma")
        ax1.set_title("IP 归属地 Top 10")
        ax1.tick_params(axis='x', rotation=45)
        
        ax2.pie(plot_data.values, labels=plot_data.index, autopct='%1.1f%%', startangle=140)
        ax2.set_title("IP 分布比例")
        plt.tight_layout()
        return fig

    def plot_sentiment_analysis(self):
        """情感分析图"""
        # 过滤掉空字符串或只有空格的评论，SnowNLP 处理空字符串会报错 ZeroDivisionError
        texts = self.df['text'].dropna().astype(str).str.strip()
        texts = texts[texts != ""]
        
        if texts.empty:
            fig, ax = plt.subplots(figsize=(10, 5))
            ax.text(0.5, 0.5, "数据不足，无法进行情感分析", ha='center', va='center')
            ax.set_title("评论情感倾向分布")
            return fig

        def safe_sentiment(text):
            try:
                return SnowNLP(text).sentiments
            except:
                return 0.5  # 出错时返回中性

        sent_scores = texts.apply(safe_sentiment)
        fig, ax = plt.subplots(figsize=(10, 5))
        sns.histplot(sent_scores, bins=25, kde=True, ax=ax, color='#2ecc71')
        ax.axvline(x=0.5, color='red', linestyle='--')
        ax.set_title("评论情感倾向分布 (0负面 <--> 1正面)")
        return fig