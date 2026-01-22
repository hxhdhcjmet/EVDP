# 获取bilibili视频链接下的评论信息并保存

import requests
import re
import time
import json
from math import ceil
import os
import random
from utils import get_data_path,default_filename
import pandas as pd
import datetime
import jieba
import matplotlib.pyplot as plt
import jieba.analyse

from collections import Counter
from snownlp import SnowNLP
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.cluster import KMeans

HEADERS = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Accept": "application/json, text/plain, */*",
    }

TEST_LINK = r'https://www.bilibili.com/video/BV1ZUkuBfEF5/?spm_id_from=333.1007.tianma.1-1-1.click&vd_source=903caa43b134dc6c594281212f0d6dee'


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


class Video_Comment_Extractor:
    def __init__(self,link):
        self.link = link
        self.view_api = r"https://api.bilibili.com/x/web-interface/view"
        self.comment_api = r"https://api.bilibili.com/x/v2/reply/main"
        self.reply_api = r'https://api.bilibili.com/x/v2/reply/reply'

    def get_cookies(self):
        curr_folder_name = os.path.dirname(__file__)
        cookie_path = os.path.join(curr_folder_name,'cookies','bilibili_cookie.json')
        print('cookie_path:',cookie_path)
        self.headers = HEADERS.copy()

        if not os.path.exists(cookie_path):
            print('未检测到Cooke文件,使用匿名模式')
            self.is_login = False
            return
        
        try:
            with open(cookie_path,'r',encoding = 'utf-8') as f:
                cookie = json.load(f)
                self.headers['Cookie'] = cookie.get('cookie','')
            print(f"成功加载Cookie:{cookie['cookie'][:10]}...")
            self.check_login_status() # 检测登陆状态
        except Exception as e:
            print(f'cookie获取失败:{str(e)}')
            self.is_login = False
    

    def check_login_status(self):
        """
        检测当前是否为登录态
        """
        test_api = r'https://api.bilibili.com/x/web-interface/nav'
        print('检测登陆状态中...')
        time.sleep(random.uniform(0.1,0.5))
        try:
            resp = requests.get(
                test_api,
                headers = self.headers,
                timeout = 10
                ).json()
            if resp.get('code') == 0 and resp.get('data',{}).get('isLogin'):
                self.is_login = True
                print(f"登陆成功:{resp['data']['uname']}")
            else:
                self.is_login = False
                print('当前为未登陆状态,将不保存IP属地信息')
        except Exception as e:
            self.is_login = False
            print('登陆状态检测失败,按未登陆处理')
    


    def extract_bv_id(self):
        """
        根据链接提取bv号
        """
        print('获取视频bv号中...')
        bv_pattern = r'BV([a-zA-Z0-9]+)'
        bv_match = re.search(bv_pattern,self.link)
        if not bv_match:
            raise ValueError(f'无效的B站视频链接{self.link},无法提取BV号')
        self.bv_id = bv_match.group(0)
        print('获取成功!')


    def get_video_aid(self,bv_id):
        """
        根据bv号查询视频的aid
        """

        print('获取视频aid中...')
        params = {'bvid':bv_id}
        # 随机停顿
        time.sleep(random.uniform(0.1,0.5))
        
        try:
            # 发送请求获取视频信息
            response= requests.get(self.view_api,params = params,headers = self.headers,timeout = 10)
            response.raise_for_status()
            video_data = response.json()

            if video_data.get('code') == 0:
                # 成功,可以提取
                aid = video_data['data']['aid']
                print(f'成功获取视频aid:{aid}')
                self.video_aid = aid
                return aid
            else:
                print(f"获取视频信息失败,错误信息:{video_data.get('message')}")
                self.video_aid = None
                return None
        except Exception as e:
            print(f'获取视频aid时发生异常:{str(e)}')
            self.video_aid = None
            return None
    
    def get_total_comments_and_pages(self,order = 'hot'):
        """
        获取评论总数
        排序依据:order:hot(最热)、time(最新)
        """
        # 先获取bv
        self.extract_bv_id()
        # 加载cookie
        self.get_cookies()
        # 再获取aid
        aid = self.get_video_aid(self.bv_id)
        if not aid:
            raise RuntimeError('aid获取失败,无法获取评论')

        params = {
            'oid':self.video_aid,
            'type':1,
            'pn':1,
            'ps':20,
            'order':order
            }
        # 随机停顿
        time.sleep(random.uniform(0.1,0.5))
        try:
            response = requests.get(self.comment_api,params = params,headers = self.headers,timeout = 10)
            response.raise_for_status()
            comment_json = response.json()
            if comment_json.get('code') != 0 or not comment_json.get('data'):
                print(f'获取评论总评论数失败:{comment_json.get('message','未知错误')}')
                return 0,0
            
            # 提取总评论数和总页数
            data = comment_json.get('data',{})
            cursor = data.get('cursor',{})
            total_count = cursor.get('all_count',0)
            page_size = params['ps']
            total_pages = ceil(total_count / page_size) if total_count else 0
            print('总评论数获取成功!')
            print(f'总页数:{total_pages}')
            print(f'总评论数:{total_count}')
            print(f'每页条数:{page_size}')

            return total_count,total_pages
        except requests.exceptions.RequestException as e:
            print(f'请求失败:{str(e)}')
            return 0,0
        except Exception as e:
            print(f'发生错误:{str(e)}')
            return 0,0
        
        
    def extract_ip(self,reply):
        """
        根据登陆状态决定是否爬ip
        """
        if not self.is_login:
            return None
        return reply.get('reply_control',{}).get('location','')

    def get_sub_replies(self,root_rpid):
        """
        根据爬取到的主评论加载子评论
        """
        sub_replies = []
        pn = 1

        while True:
            params = {
            'oid':self.video_aid,
            'type':1,
            'root':root_rpid,
            'pn':pn,
            'ps':20
            }

            time.sleep(random.uniform(0.3,0.6))

            resp = requests.get(self.reply_api,
                                params = params,
                                headers = self.headers,
                                timeout = 10).json()
            replies = resp.get('data',{}).get('replies',[])
            if not replies:
                break
            for r in replies:
                sub_replies.append({
                    'comment': r['content']['message'],
                    'like':r['like'],
                    'user':r['member']['uname'],
                    'level':r['member']['level_info']['current_level'],
                    'ip':self.extract_ip(r)
                    })
            pn += 1
        return sub_replies
    
    def build_comment_data(self,reply):
        """
        在爬取所有评论时组织爬取子回复结构
        """
        comment_data = {
        'comment': reply['content']['message'],
        'like': reply['like'],
        'reply_count': reply['rcount'],
        'ctime': reply['ctime'],
        'user': {
            'name': reply['member']['uname'],
            'level': reply['member']['level_info']['current_level'],
            'ip': self.extract_ip(reply)
        },
        'replies': []
    }

        if reply['rcount'] > 0:
            comment_data['replies'] = self.get_sub_replies(reply['rpid'])

        return comment_data
    
    def crawl_all_comments(self,order = 'time'):
        """
        爬取所有评论并保存
        order : 爬取评论时的顺序,默认按时间顺序
        """

        total_count,total_pages = self.get_total_comments_and_pages(order)

        for pn in range(1,total_pages+1):
            print(f'正在获取第{pn}/{total_pages}页...')

            time.sleep(random.uniform(0.3,0.5))# 每次爬取前随机停顿

            params = {
                'oid' : self.video_aid,
                'type' : 1,
                'pn' : pn,
                'ps' : 20,
                'order' : order                
                }

            resp = requests.get(
                self.comment_api,
                params = params,
                headers = self.headers,
                timeout = 10
                ).json()
            
            replies = resp.get('data',{}).get('replies',[])
            
            if not replies:
                continue
            
            for reply in replies:
                # 获取每一条评论信息，yield产出
                yield self.build_comment_data(reply)


class CommentWriter:
    def __init__(self,filename = default_filename()):
        # timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M")
        file_path = get_data_path(filename = filename) # 这里创建的是文件夹,需要进一步创建一个同名文件
        save_file_name = filename+'.jsonl'
        full_file_path = os.path.join(file_path,save_file_name)
        self.filepath = full_file_path
        self.fp = None

    def open_for_write(self):
        """
        仅在需要写入时调用
        """
        if not self.fp:
            # 使用a模式
            self.fp = open(self.filepath,'a',encoding = 'utf-8')


        # try:
        #     with open(full_file_path,'x',encoding = 'utf-8') as f:
        #         pass
        #     print(f'初始化成功,保存文件路径:{full_file_path},数据文件与文件夹同名,为:{save_file_name}')
        # except FileExistsError:
        #     print('保存文件已存在,将不重复创建!')
        # except Exception as e:
        #     print(f'初始化评论爬取类,创建文件时发生错误:{e}')
        # finally:
        #     self.filepath = full_file_path
        #     self.fp = open(self.filepath,'w',encoding = 'utf-8')

    def write(self,data):
        if not self.fp:
            self.open_for_write()
        self.fp.write(json.dumps(data,ensure_ascii=False)+'\n')

    def close(self):
        if self.fp:
            self.fp.close()
        

        

class CommentAnalyser:

    def __init__(self,jsonl_path:str):
        self.jsonl_path = jsonl_path
        self.df = None
        self.clustered_df = None
        # 设置中文字体（防止Streamlit或Linux下乱码，根据系统环境调整）
        plt.rcParams['axes.unicode_minus'] = False
    
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
        关键词分析:提取前n个关键词
        """
        all_text = "".join(self.df['comment'].astype(str).tolist())

        # 使用TF-IDF算法提取关键词
        keywords = jieba.analyse.extract_tags(all_text,took = top_n,withWeight = True)
        return keywords



    def analyze_sentiment(self):
        """
        情感分析
        """
        print('正在进行情感分析...')
        if self.df is None or 'comment' not in self.df.columns:
            return self

        # 计算得分
        self.df['sentiment_score'] = self.df['comment'].apply(
            lambda x: SnowNLP(str(x)).sentiments if pd.notnull(x) else 0.5
        )

        # 分类贴标签
        def classify(score):
            if score>0.6: return 'positive'
            elif score < 0.4: return 'negative'
            else: return 'neutral'
        
        self.df['sentiment_type'] = self.df['sentiment_score'].apply(classify)
        print('情感分析完成!')
        return self
    
    def plot_sentiment(self):
        """情感分布饼图"""
        counts = self.df['sentiment_type'].value_counts()
        plt.figure(figsize=(8, 6))
        plt.pie(counts, labels=counts.index, autopct='%1.1f%%', colors=['#66b3ff','#99ff99','#ff9999'])
        plt.title('Comment Sentiment Distribution')
        plt.show()

        
        


    def cluster_comments(self,k:int = 5):
        """
        聚类分析
        """
        df = self.df
        
        def cut(text):
            return ' '.join(jieba.cut(text))
        
        corpus = df['comment'].map(cut).tolist()

        vectorizer = TfidfVectorizer(max_features=3000)
        X = vectorizer.fit_transform(corpus)

        model = KMeans(n_clusters = k,random_state=42)
        df['cluster'] = model.fit_predict(X)

        self.cluster_df = df 
        return self
    
    def plot_time_density(self,freq = '1h'):
        ts = self.df.set_index('ctime').resample(freq).size()

        plt.figure(figsize = (10,5))
        ts.plot()
        plt.title("Comments Time Density")
        plt.xlabel('time')
        plt.ylabel('comment nums')
        plt.tight_layout()
        plt.show()
    
    def plot_user_level(self):
        """
        等级分析
        """
        counts = self.df['user.level'].value_counts().sort_index()

        plt.figure(figsize = (8,6))
        plt.pie(counts,labels = [f"Lv{i}" for i in counts.index],autopct='%1.1f%%')
        plt.title('User Level Distribution')
        plt.tight_layout()
        plt.show()

    


    def plot_ip_distribubtion(self,deduplicate = True):
        """
        绘制IP分布图
        """
        if 'user.ip' not in self.df.columns:
            print("无IP数据")
            return

        #  数据处理
        temp_df = self.df.copy()
        if deduplicate:
            # 假设以用户名作为唯一标识，保留该用户最后一次评论的记录
            temp_df = temp_df.drop_duplicates(subset=['user.name'], keep='last')

        #  统计并映射为英文
        # 提取 Top 10
        counts = temp_df['user.ip'].value_counts().head(10)
        
        # 将索引（中文省份）转换为英文，如果字典里没有则保留原样
        eng_indices = [PROVINCE_MAP[name] if name in PROVINCE_MAP else "Other" for name in counts.index]


        
        #  绘图
        plt.figure(figsize=(12, 7))
        # 创建柱状图
        bars = plt.bar(eng_indices, counts.values, color='steelblue', edgecolor='black', alpha=0.8)
        
        # 在柱子上方标注具体数字
        for bar in bars:
            yval = bar.get_height()
            plt.text(bar.get_x() + bar.get_width()/2, yval + 0.2, 
                    int(yval), va='bottom', ha='center', fontsize=11)

        # 设置标题和标签
        title_type = "Unique Users" if deduplicate else "Total Comments"
        plt.title(f'Top 10 IP Distribution ({title_type})', fontsize=14)
        plt.xlabel('Province / Region', fontsize=12)
        plt.ylabel('Count', fontsize=12)
        plt.xticks(rotation=45)
        plt.grid(axis='y', linestyle='--', alpha=0.6)
        
        plt.tight_layout()
        plt.show() # 弹窗显示





if __name__ == '__main__':
    extractor  = Video_Comment_Extractor(TEST_LINK)
    writer = CommentWriter('2026115bilibili')

    # for comment in extractor.crawl_all_comments(order = 'time'):
    #      writer.write(comment)
    # writer.close()
    # print('爬取完成！')

    print('开始分析数据...')
    analyzer = CommentAnalyser(writer.filepath)
    analyzer.load()
    analyzer.preprocess()
    # analyzer.plot_time_density()
    # analyzer.plot_user_level()
    analyzer.analyze_sentiment()
    analyzer.plot_sentiment()
    analyzer.plot_ip_distribubtion(False)