# 评论分析

import pandas as pd
import os
import json
import jieba
from jieba import analyse
import matplotlib.pyplot as plt
import matplotlib.font_manager as fm
from wordcloud import WordCloud

# 配置中文字体
def init_font():
    """
    配置中文字体
    """
    # 目标字体目录
    curr_file_path = os.path.abspath(__file__)
    curr_dir = os.path.dirname(curr_file_path)

    parent1 = os.path.dirname(curr_dir)
    parent2 = os.path.dirname(parent1)
    parent3 = os.path.dirname(parent2)
    font_path = os.path.join(parent3,'assets/fonts/simhei.ttf')

    if os.path.exists(font_path):
        # 注册字体到字体管理器
        fm.fontManager.addfont(font_path)
        prop = fm.FontProperties(fname=font_path)
        
        # 设置全局默认字体为该文件的名称
        plt.rcParams['font.sans-serif'] = [prop.get_name()]
        plt.rcParams['font.family'] = 'sans-serif'
        plt.rcParams['axes.unicode_minus'] = False
        print(f'字体加载成功: {prop.get_name()}')
    else:
        # 如果没找到，尝试使用系统黑体垫底
        print('警告: 未找到字体文件')


# 省份中英文/拼音转换字典
PROVINCE_MAP = {
    '北京': 'Beijing', '上海': 'Shanghai', '天津': 'Tianjin', '重庆': 'Chongqing',
    '河北': 'Hebei', '山西': 'Shanxi', '辽宁': 'Liaoning', '吉林': 'Jilin',
    '黑龙江': 'Heilongjiang', '江苏': 'Jiangsu', '浙江': 'Zhejiang', '安徽': 'Anhui',
    '福建': 'Fujian', '江西': 'Jiangxi', '山东': 'Shandong', '河南': 'Henan',
    '湖北': 'Hubei', '湖南': 'Hunan', '广东': 'Guangdong', '海南': 'Hainan',
    '四川': 'Sichuan', '贵州': 'Guizhou', '云南': 'Yunnan', '陕西': 'Shaanxi',
    '甘肃': 'Gansu', '青海': 'Qinghai', '中国台湾': 'China Taiwan', '内蒙古': 'Inner Mongolia',
    '广西': 'Guangxi', '西藏': 'Tibet', '宁夏': 'Ningxia', '新疆': 'Xinjiang',
    '中国香港': 'China Hong Kong', '中国澳门': 'China Macao', '未知': 'Unknown', '海外': 'Overseas'
}




class CommentAnalyser:

    def __init__(self,jsonl_path:str):
        init_font()
        self.jsonl_path = jsonl_path
        self.df = None
        self.clustered_df = None
        self.stopwords = set(['的','了','是','我','你','他','吧','啊','呢','这','那','就'])
    
    def load(self):
        """
        数据获取
        """
        rows = []
        try:
            with open(self.jsonl_path,encoding = 'utf-8') as f:
                for line in f:
                    rows.append(json.loads(line))
            self.df = pd.json_normalize(rows)
            print('评论文件读取成功!')
            return self
        except Exception as e:
            print(f'读取文件发生错误:{e}')
            


    def preprocess(self):
        """
        数据清洗
        """
        print('开始清洗数据...')
        # 时间戳转datetime:
        self.df['ctime'] = pd.to_datetime(self.df['ctime'],unit = 's')
        
        # ip清洗('ip属地:xx'->'xx')
        if 'user.ip' in self.df.columns:
            self.df['user.ip'] = self.df['user.ip'].fillna('未知')
            self.df['user.ip'] = self.df['user.ip'].str.replace('IP属地：','',regex=False)
        print('数据清洗完成！')
        
    def analyze_basic(self):
        """
        基础统计
        """
        return {
            'total_comments':len(self.df),
            'avg_like' : self.df['like'].mean(),
            'avg_reply':self.df['reply_count'].mean()
        }
    

    def get_keywords(self,top_n = 10):
        """
        提取关键此并生成词云
        """
        all_text = "".join(self.df['comment'].astype(str).tolist())

        # 使用TF-IDF算法提取关键词
        keywords = jieba.analyse.extract_tags(all_text,topK = top_n,withWeight = True)
        # 打印词云
        
        print("\n --- Top 关键词 ---")
        for word,weight in keywords:
            print(f"{word}: {weight:.4f}")
        return keywords
    
    def plot_wordcloud(self, return_fig=False):
            """生成词云图"""
            try:
                curr_dir = os.path.dirname(os.path.abspath(__file__))
                # 简化路径逻辑：向上退两级到根目录
                root_dir = os.path.abspath(os.path.join(curr_dir, "../.."))
                font_path = os.path.join(root_dir, 'assets/fonts/simhei.ttf')
                if not os.path.exists(font_path): font_path = None
            except:
                font_path = None

            print('正在生成词云图...')
            segmented_comments = self.df['comment'].apply(lambda x: " ".join([w for w in jieba.cut(str(x)) if len(w) > 1]))
            all_text = " ".join(segmented_comments)
            
            wc = WordCloud(
                font_path=font_path,
                background_color='white',
                width=1000, height=600,
                max_words=100, 
                stopwords=self.stopwords  
            ).generate(all_text)

            fig, ax = plt.subplots(figsize=(12, 8))
            ax.imshow(wc, interpolation='bilinear')
            ax.axis('off')
            # --- 修正点：使用 set_title ---
            ax.set_title('BiliBili 评论词云图', fontsize=16) 
            
            if return_fig:
                return fig
            plt.show()
            plt.close(fig)

    def plot_time_density(self, freq='1h', return_fig=False):
        """
        时间密度分析 - 增强版（解决 DatetimeIndex 报错）
        """
        # 1. 基础检查：确保 df 存在且不为空
        if self.df is None or self.df.empty:
            print("警告：数据为空，无法生成时间密度图")
            return None

        # 2. 核心修复：确保 ctime 是 datetime 格式
        # 即使 preprocess 跑过了，这里再检查一遍更稳健
        try:
            if not pd.api.types.is_datetime64_any_dtype(self.df['ctime']):
                # 如果是整数时间戳，转换为 datetime
                self.df['ctime'] = pd.to_datetime(self.df['ctime'], unit='s', errors='coerce')
            
            # 剔除转换失败的行（如果有的话）
            temp_df = self.df.dropna(subset=['ctime']).copy()
            
            if temp_df.empty:
                print("警告：没有有效的时间数据")
                return None

            # 3. 核心修复：显式将 ctime 设为索引并排序
            temp_df = temp_df.set_index('ctime').sort_index()

        except Exception as e:
            print(f"处理时间序列索引时发生错误: {e}")
            return None

        # 4. 执行重采样
        try:
            # size() 统计每个频率区间内的评论数量
            ts = temp_df.resample(freq).size()
            
            # 如果重采样后数据太少（比如只有1个点），plot 会报错或很难看
            if len(ts) < 1:
                return None

            # 5. 绘图
            # 注意：这里要用 plt.subplots() 确保 fig 和 ax 的正确对应
            fig, ax = plt.subplots(figsize=(12, 6))
            
            # ts 是 Series，可以直接调用 plot
            ts.plot(ax=ax, color='#1f77b4', marker='.', markersize=4, linewidth=1)
            
            ax.set_title("Comments Time Density Distribution", fontsize=14, pad=20)
            ax.set_xlabel('Time (Interval: {})'.format(freq), fontsize=12)
            ax.set_ylabel('Comment Count', fontsize=12)
            
            # 优化视觉效果
            ax.grid(True, linestyle='--', alpha=0.6)
            plt.xticks(rotation=45)
            fig.tight_layout()

            if return_fig:
                return fig
            plt.show()
            plt.close(fig)
            
        except Exception as e:
            # 这里捕获的就是你遇到的 "Only valid with DatetimeIndex" 错误
            print(f"重采样分析失败: {e}")
            return None

    def plot_user_level(self, return_fig=False):
        """等级分析"""
        counts = self.df['user.level'].value_counts().sort_index()

        fig, ax = plt.subplots(figsize=(8, 6))
        # 修正点：增加 label 对应
        ax.pie(counts, labels=[f"Lv{i}" for i in counts.index], autopct='%1.1f%%', startangle=140)
        ax.set_title('User Level Distribution')
        
        if return_fig:
            return fig
        plt.show()
        plt.close(fig)

    def plot_ip_distribution(self, deduplicate=True, return_fig=False):
        """绘制IP分布图"""
        if 'user.ip' not in self.df.columns or self.df['user.ip'].empty:
            print("无IP数据或数据为空")
            return None

        temp_df = self.df.copy()
        if deduplicate:
            temp_df = temp_df.drop_duplicates(subset=['user.name'], keep='last')

        counts_all = temp_df['user.ip'].value_counts()
        counts = counts_all.head(10)
        others = counts_all.iloc[10:].sum()
        
        ip_names = list(counts.index)
        ip_values = list(counts.values)
        if others > 0:
            ip_names.append('Others')
            ip_values.append(others)
        
        # 假设 PROVINCE_MAP 已在外部定义
        eng_indices = [PROVINCE_MAP.get(name, "Others") for name in ip_names]

        fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(18, 7))
        title_type = 'Unique Users' if deduplicate else 'Total Comments'

        # 子图1：柱状图
        bars = ax1.bar(eng_indices, ip_values, color='steelblue', edgecolor='black', alpha=0.8)
        for bar in bars:
            yval = bar.get_height()
            ax1.text(bar.get_x() + bar.get_width()/2, yval + 0.1, int(yval), va='bottom', ha='center')

        ax1.set_title(f'Top 10 IP Distribution ({title_type})', fontsize=14)
        ax1.tick_params(axis='x', rotation=45)

        # 子图2：饼图
        ax2.pie(ip_values, labels=eng_indices, autopct='%1.1f%%', startangle=90, shadow=False)
        ax2.set_title(f'IP Percentage ({title_type})', fontsize=14)

        fig.tight_layout()
        if return_fig:
            return fig
        plt.show()
        plt.close(fig)
