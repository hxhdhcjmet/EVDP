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
import matplotlib.font_manager as fm
import jieba.analyse
import threading
import aiohttp
import asyncio

from collections import Counter
from snownlp import SnowNLP
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.cluster import KMeans

from concurrent.futures import ThreadPoolExecutor, as_completed
from wordcloud import WordCloud

HEADERS = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Accept": "application/json, text/plain, */*",
    }

TEST_LINK = r'https://www.bilibili.com/video/BV1zkkEBRER5/?spm_id_from=333.1007.tianma.2-1-3.click&vd_source=903caa43b134dc6c594281212f0d6dee'

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
    font_path = os.path.join(parent2,'assets/fonts/simhei.ttf')

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

class CrawlStats:
    # 爬取统计信息类
    def __init__(self, total_pages):
        self.total_pages = total_pages
        self.finished_pages = 0
        self.failed_pages = 0
        self.total_comments = 0
        self.lock = threading.Lock()
        self.start_time = time.time()

    def page_done(self, comment_count):
        with self.lock:
            self.finished_pages += 1
            self.total_comments += comment_count

    def page_failed(self):
        with self.lock:
            self.failed_pages += 1

    def report(self):
        elapsed = time.time() - self.start_time
        speed = self.total_comments / elapsed if elapsed > 0 else 0
        print(
            f'[进度] {self.finished_pages}/{self.total_pages} 页 | '
            f'评论数: {self.total_comments} | '
            f'失败页: {self.failed_pages} | '
            f'用时: {elapsed:.1f}s | '
            f'速度: {speed:.1f} 条/s'
        )





class CrawlPointer:
    """
    爬取指针,下次爬取时从指针记录处开始爬取
    """
    def __init__(self,save_dir):
        self.path = os.path.join(save_dir,'progress.json')
        self.last_page = 0
        self.total_comments = 0
        self._load()

    def _load(self):
        if os.path.exists(self.path):
            try:
                with open(self.path,'r',encoding = 'utf-8') as f:
                    data = json.load(f)
                    self.last_page = data.get('last_page',0)
                    self.total_comments = data.get('total_commints',0)
            except Exception as e:
                    print('加载爬取指针失败:',e)

    def update(self,page,comments):
        self.last_page = page
        self.total_comments+= comments
        with open(self.path,'w',encoding = 'utf-8') as f:
            json.dump({
            'last_page' : self.last_page,
            'total_comments' : self.total_comments,
            'update_time':datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            },f,ensure_ascii = False,indent = 2)



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
        stats = CrawlStats(total_pages)
        finished_pages = 0
        next_offset = 0
        mode = 3 if order == 'time' else 2
        while True:
            params = {
                'oid':self.video_aid,
                'type': 1,
                'mode':mode,
                'next':next_offset,
                'ps':20
                }
            try:
                resp_json = requests.get(self.comment_api,params = params,headers = self.headers,timeout=10).json()
                if resp_json.get('code') != 0:
                    print('请求评论失败:',resp_json.get('message','未知错误'))
                    break
                
                data = resp_json.get('data',{})
                replies = data.get('replies',[])

                if not replies:
                    # 没有更多评论了
                    break
                for reply in replies:
                    yield self.build_comment_data(reply)

                # 更新offset指向下一页
                cursor = data.get('cursor',{})
                next_offset = cursor.get('next')
                is_end = cursor.get('is_end',False)

                if is_end:
                    # 爬取完毕
                    print('爬取完毕!')
                    break
                stats.page_done(len(replies))
                if finished_pages != stats.finished_pages:
                    finished_pages = stats.finished_pages
                    stats.report()

                    # 爬取完随机停顿
                    time.sleep(random.uniform(2,4))
            except Exception as e:
                stats.page_failed()
                print(f'发生错误:{e}')
                break

                                                  






        # for pn in range(1,total_pages+1):
        #     print(f'正在获取第{pn}/{total_pages}页...')

        #     time.sleep(random.uniform(3,5))# 每次爬取前随机停顿

        #     params = {
        #         'oid' : self.video_aid,
        #         'type' : 1,
        #         'pn' : pn,
        #         'ps' : 20,
        #         'order' : order                
        #         }

        #     resp = requests.get(
        #         self.comment_api,
        #         params = params,
        #         headers = self.headers,
        #         timeout = 10
        #         ).json()
            
        #     replies = resp.get('data',{}).get('replies',[])
            
        #     if not replies:
        #         continue
            
        #     for reply in replies:
        #         # 获取每一条评论信息，yield产出
        #         try:
        #             yield self.build_comment_data(reply)
        #         except Exception as e:
        #             stats.failed_pages()
        #             print(f'爬取发生错误:{e}')
        #             continue
        #     stats.page_done(len(replies))
        #     if finished_pages != stats.finished_pages:
        #         finished_pages = stats.finished_pages
        #         stats.report()
            
            



    





    def fetch_one_page(self, pn, order='time'):
        params = {
            'oid': self.video_aid,
            'type': 1,
            'pn': pn,
            'ps': 50,  # 增大单页数量
            'order': order
        }

        try:
            time.sleep(random.uniform(0.05, 0.2))
            resp = self.session.get(
                self.comment_api,
                params=params,
                headers=self.headers,
                timeout=10
            ).json()
            return resp.get('data', {}).get('replies', [])
        except Exception as e:
            print(f'[错误] 第 {pn} 页请求失败: {e}')
            return None

    def crawl_all_comments_threadpool(
    self,
    writer,
    order='time',
    max_workers=8,
    report_interval=5
):
        """
        线程池并发爬取
        """
        total_count, total_pages = self.get_total_comments_and_pages(order)
        if total_pages == 0:
            print('无评论，结束')
            return

        self.session = requests.Session()
        self.session.headers.update(self.headers)

        stats = CrawlStats(total_pages)
        last_report = time.time()

        print(f'开始爬取：总页数={total_pages}，线程数={max_workers}')

        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            future_map = {
                executor.submit(self.fetch_one_page, pn, order): pn
                for pn in range(1, total_pages + 1)
            }

            for future in as_completed(future_map):
                pn = future_map[future]
                try:
                    replies = future.result()
                    if replies is None:
                        stats.page_failed()
                        continue

                    for reply in replies:
                        data = self.build_comment_data(reply)
                        writer.write(data)

                    stats.page_done(len(replies))

                except Exception as e:
                    print(f'[异常] 第 {pn} 页处理失败: {e}')
                    stats.page_failed()

                # 定期输出进度
                if time.time() - last_report > report_interval:
                    stats.report()
                    last_report = time.time()

        stats.report()
        self.session.close()
        print('爬取完成')


    # 新增异步爬取

    # 单页
    async def fetch_one_page_async(self,session,sem,pn,order):
        params = {
            'oid' : self.video_aid,
            'type': 1,
            'pn' : pn,
            'ps' : 50,
            'order' : order
        }

        async with sem:
            try:
                await asyncio.sleep(random.uniform(0.05,0.2))
                async with session.get(self.comment_api,params = params, timeout = 15) as resp:
                    data = await resp.json()
                    return data.get('data',{}).get('replies',[])
            except Exception as e:
                print(f'[错误]第{pn}页请求失败:{e}')
                return None
            


    async def crawl_all_comments_async(self,writer,order = 'time',max_concurrency = 5):
        """
        异步爬取,基于cursor逻辑
        """
        total_count,total_pages = self.get_total_comments_and_pages(order)
        mode = 2 if order == 'time' else 3
        next_offset = 0
        is_end = False

        if total_pages == 0:
            print('无评论，结束')
            return
        async with aiohttp.ClientSession(headers = self.headers) as session:
            stas = AsyncCrawStats(0,total_pages)
            finished_pages = 0
            while not is_end:
                params = {
                    'oid':self.video_aid,
                    'type':1,
                    'mode':mode,
                    'next':next_offset,
                    'ps':20 
                    }
                try:
                    # 随机延迟
                    await asyncio.sleep(random.uniform(1.5,2.5))

                    async with session.get(self.comment_api,params = params,timeout = 15) as resp:
                        res_data = await resp.json()
                        if res_data.get('code') != 0:
                            print(f'解析结束或被拦截:{res_data.get('message','未知错误')}')
                            break
                        
                        data = res_data.get('data',{})
                        replies = data.get('replies',[])

                        if not replies:
                            print('无更多评论,爬取结束!')
                            break
                        
                        for reply in replies:
                            comment_item = self.build_comment_data(reply)
                            writer.write(comment_item)

                        # 更新指针
                        cursor = data.get('cursor',{})
                        next_offset = cursor.get('next')
                        is_end = cursor.get('is_end',False)

                        stas.page_done(len(replies))
                        if finished_pages != stas.finished_pages:
                            finished_pages = stas.finished_pages
                            stas.report()
                except Exception as e:
                    print(f'异步请求发生错误:{e}')
                    break
            print('异步爬取完成!')

                         






    # async def crawl_all_comments_async(self,writer,order = 'time',max_concurrency = 5):
    #     """
    #     异步爬取主函数
    #     """
    #     total_count,total_pages = self.get_total_comments_and_pages(order)


    #     if total_pages == 0:
    #         print('无评论,结束')
    #         return
        

    #     # =====断点续爬=====
        
    #     save_dir = os.path.dirname(writer.filepath)
    #     pointer = CrawlPointer(save_dir)
    #     start_page = pointer.last_page + 1

    #     if start_page > total_pages:
    #         print('评论已全部爬取完成!')
    #         return 
        
    #     print(f'从第{start_page} 页开始爬取 (总页数{total_pages})')
    #     stats = AsyncCrawStats(start_page - 1,total_pages)
    #     sem = asyncio.Semaphore(max_concurrency)
    #     connector = aiohttp.TCPConnector(limit_per_host = max_concurrency)
    #     async with aiohttp.ClientSession(headers = self.headers,connector = connector) as session:
    #         tasks = [self.fetch_one_page_async(session,sem,pn,order) for pn in range(start_page,total_pages + 1)]
    #         for pn,coro in zip(range(start_page,total_pages + 1),asyncio.as_completed(tasks)):
    #             replies = await coro

    #             # 失败页
    #             if replies is None:
    #                 stats.page_failed()
    #                 continue

    #             for reply in replies:
    #                 data = self.build_comment_data(reply)
    #                 writer.write(data)

    #             stats.page_done(len(replies))
    #             pointer.update(pn,len(replies))

    #             if stats.finished_pages % 3 == 0:
    #                 stats.report()
    #     stats.report()
    #     print('异步爬取完成!')



class AsyncCrawStats:
    """
    异步爬取统计器
    """
    def __init__(self,start_page,total_pages):
        self.start_page = start_page
        self.total_pages = total_pages
        self.finished_pages = 0
        self.failed_pages = 0
        self.total_comments = 0
        self.start_time = time.time()


    def page_done(self,count):
        self.finished_pages += 1
        self.total_comments += count

    def page_failed(self):
        self.failed_pages += 1

    def report(self):
        elapsed = time.time() - self.start_time
        speed = self.total_comments / elapsed if elapsed > 0 else 0
        print(
            f'[进度]页{self.start_page + self.finished_pages}/{self.total_pages} | '
            f'评论{self.total_comments}  | '
            f'失败页{self.failed_pages} | '
            f'{elapsed:.1f}s | {speed:.1f}条/s'
        )




class CommentWriter:
    def __init__(self,filename = default_filename()):
        # timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M")
        file_path = get_data_path(filename = filename) # 这里创建的是文件夹,需要进一步创建一个同名文件
        save_file_name = filename+'.jsonl'
        full_file_path = os.path.join(file_path,save_file_name)
        self.filepath = full_file_path
        self.fp = None
        self.lock = threading.Lock()

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
        with self.lock:
            self.fp.write(json.dumps(data,ensure_ascii=False)+'\n')

    def close(self):
        if self.fp:
            self.fp.close()
        

        

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
    
    def plot_wordcloud(self):
        """
        生成词云图
        """
        try:
            curr_file_path = os.path.abspath(__file__)
            curr_dir = os.path.dirname(curr_file_path)
            parent1 = os.path.dirname(curr_dir)
            parent2 = os.path.dirname(parent1)
            font_path = os.path.join(parent2,'assets/fonts/simhei.ttf')
        except Exception as e:
            print('词云图配置中文字体失败:{e}')
            font_path = ''

        print('正在生成词云图...')
        segmented_comments = self.df['comment'].apply(lambda x : " ".join([w for w in jieba.cut(str(x)) if len(w) >1]))
        all_text = " ".join(segmented_comments)
        wc = WordCloud(
        font_path = font_path,
        background_color = 'white',
        width = 1000,
        height = 600,
        max_words = 100, 
        stopwords = self.stopwords  
        ).generate(all_text)

        plt.figure(figsize = (12,8))
        plt.imshow(wc,interpolation='bilinear')
        plt.axis('off')
        plt.title('BiliBili 评论词云图',fontsize = 16)
        plt.show()



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

    


    def plot_ip_distribution(self,deduplicate = True):
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
        # 统计其他IP
        others = temp_df['user.ip'].value_counts().iloc[10:].sum()
        ip_names = list(counts.index)
        ip_values = list(counts.values)
        if others > 0:
            ip_names.append('Others')
            ip_values.append(others)
        
        # 将索引（中文省份）转换为英文，如果字典里没有则保留原样
        eng_indices = [PROVINCE_MAP[name] if name in PROVINCE_MAP else "Others" for name in ip_names]


        
        #  绘图
        fig,(ax1,ax2) = plt.subplots(1,2,figsize = (18,7)) # 1行2列
        title_type = 'Unique Users' if deduplicate else 'Total Comments'

        # ==========子图1==========
        # 创建柱状图
        bars = ax1.bar(eng_indices, ip_values, color='steelblue', edgecolor='black', alpha=0.8)
        # 在柱子上方标注具体数字
        for bar in bars:
            yval = bar.get_height()
            ax1.text(bar.get_x() + bar.get_width()/2, yval + 0.2, 
                    int(yval), va='bottom', ha='center', fontsize=11)

        # 设置标题和标签
        ax1.set_title(f'Top 10 and Other IP Distribution ({title_type})', fontsize=14)
        ax1.set_xlabel('Province / Region', fontsize=12)
        ax1.set_ylabel('Count', fontsize=12)
        ax1.tick_params(axis='x', rotation=45)
        ax1.grid(axis='y', linestyle='--', alpha=0.6)
        
        # ==========子图2==========
        # 饼图
        colors = plt.cm.Pastel1(range(len(ip_values)))
        wedges,texts,autotexts = ax2.pie(ip_values,labels = eng_indices,autopct = '%1.1f%%',colors = colors,
         startangle = 90,shadow = True)
        plt.setp(autotexts, size=10, weight="bold", color="black")
        plt.setp(texts, size=11)
        ax2.set_title(f'Top 10 and Other IP Distribution - Pie Chart ({title_type})', fontsize=14)

        plt.tight_layout()
        plt.show() # 弹窗显示



if __name__ == '__main__':


    init_font()
    extractor  = Video_Comment_Extractor(TEST_LINK)
    writer = CommentWriter('202625leige')

    print('====== 开始异步爬取 ======')
    asyncio.run(
        extractor.crawl_all_comments_async(
            writer = writer,
            order = 'time',
            max_concurrency = 10
            )
        )
    writer.close()

    # print('===== 开始并发爬取 =====')
    # extractor.crawl_all_comments_threadpool(
    #     writer=writer,
    #     order='time',
    #     max_workers=10,       # 建议 6~12
    #     report_interval=3    # 每 3 秒打印一次进度
    # )
    # writer.close()



    print('===== 爬取完成，开始分析 =====')
    print('开始分析数据...')
    analyzer = CommentAnalyser(writer.filepath)
    analyzer.load()
    analyzer.preprocess()
    analyzer.get_keywords()
    analyzer.plot_wordcloud()
    analyzer.plot_time_density()
    analyzer.plot_user_level()
    analyzer.analyze_sentiment()
    analyzer.plot_sentiment()
    analyzer.plot_ip_distribution(False) 