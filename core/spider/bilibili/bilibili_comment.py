# 获取bilibili视频链接下的评论信息并保存

import requests
import re
import time
import json
from math import ceil
import os
import random
import datetime
import aiohttp
import asyncio

from core.spider.bilibili.CommentWriter import CommentWriter
from core.spider.bilibili.CommentAnalyser import CommentAnalyser
from tqdm import tqdm


HEADERS = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Accept": "application/json, text/plain, */*",
    }

TEST_LINK = r'https://www.bilibili.com/video/BV1hn6KBeEKt/?spm_id_from=333.1007.tianma.4-3-13.click&vd_source=903caa43b134dc6c594281212f0d6dee'


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
    

    def save_cookie_to_file(self,cookie_str):
        """
        保存Cookie到本地Json
        """
        cookie_dir = os.path.join(os.path.dirname(__file__),'cookies')
        os.makedirs(cookie_dir,exist_ok=True)
        path = os.path.join(cookie_dir,'bilibili_cookie.json')
        with open(path,'w',encoding = 'utf-8') as f:
            json.dump({"cookie": cookie_str,"time" : str(datetime.datetime.now())},f)

    def check_login_status(self):
        """
        检测当前是否为登录态
        """
        test_api = r'https://api.bilibili.com/x/web-interface/nav'
        # print('检测登陆状态中...')
        time.sleep(random.uniform(0.1,0.5))
        try:
            resp = requests.get(
                test_api,
                headers = self.headers,
                timeout = 10
                ).json()
            if resp.get('code') == 0 and resp.get('data',{}).get('isLogin'):
                self.uname = resp['data']['uname']
                self.is_login = True
                return True
                # print(f"登陆成功:{resp['data']['uname']}")
            # else:
            #     self.is_login = False
            #     print('当前为未登陆状态,将不保存IP属地信息')
        except Exception as e:
            self.is_login = False
            return False
            # print('登陆状态检测失败,按未登陆处理')
    


    def extract_bv_id(self):
        """
        根据链接提取bv号
        """
        # print('获取视频bv号中...')
        bv_pattern = r'BV([a-zA-Z0-9]+)'
        bv_match = re.search(bv_pattern,self.link)
        if not bv_match:
            raise ValueError(f'无效的B站视频链接{self.link},无法提取BV号')
        self.bv_id = bv_match.group(0)
        return self.bv_id
        # print('获取成功!')


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
            


    async def crawl_all_comments_async(self, writer, order='time',callback = None):
        """
        异步爬取，修复进度统计逻辑
        """
        # 1. 先获取一次元数据（总数）
        total_count, _ = self.get_total_comments_and_pages(order)
        if total_count == 0:
            print('无评论，结束')
            return

        # 2. 初始化统计器 (使用 tqdm)
        ps = 20
        stats = AsyncCrawStats(total_count, ps=ps)
        
        mode = 2 if order == 'time' else 3
        next_offset = 0
        is_end = False

        async with aiohttp.ClientSession(headers=self.headers) as session:
            while not is_end:
                params = {
                    'oid': self.video_aid,
                    'type': 1,
                    'mode': mode,
                    'next': next_offset,
                    'ps': ps
                }
                try:
                    # 随机延迟，保护 IP
                    await asyncio.sleep(random.uniform(1.0, 2.0))

                    async with session.get(self.comment_api, params=params, timeout=15) as resp:
                        res_data = await resp.json()
                        
                        if res_data.get('code') != 0:
                            # 触发验证码或频率限制
                            stats.pbar.set_description(f"中断: {res_data.get('message')}")
                            break
                        
                        data = res_data.get('data', {})
                        replies = data.get('replies', [])

                        # 情况 A：返回空列表，说明到底了
                        if not replies:
                            break
                        
                        # 写入数据
                        for reply in replies:
                            comment_item = self.build_comment_data(reply)
                            writer.write(comment_item)

                        # 更新指针
                        cursor = data.get('cursor', {})
                        next_offset = cursor.get('next')
                        is_end = cursor.get('is_end', False)

                        # 更新 tqdm 进度
                        stats.update(len(replies))

                        if callback:
                            # 计算百分比传给streamlit
                            percent = min(stats.current_step / stats.total_steps,1.0)
                            callback(percent,f"已爬取{stats.current_comment}条评论...")

                        if is_end:
                            stats.force_finish() # 强制拉满进度条
                            break

                except Exception as e:
                    stats.pbar.set_description(f"异常: {str(e)[:20]}")
                    break
                    
        stats.close()
        print('\n[完成] 数据已保存至:', writer.filepath)

                         

class AsyncCrawStats:
    """
    异步爬取统计器
    """
    def __init__(self,total_count,ps = 20):
        self.total_comments = total_count
        # 预计总页数作为tqdm的total
        self.total_steps = ceil(total_count / ps) if total_count > 0 else 1
        self.current_step = 0
        self.pbar = tqdm(total = self.total_steps,desc = "爬取进度",unit = "页")
        self.current_comments = 0

    def update(self,inc_comments):
        self.current_comments += inc_comments
        self.current_step += 1
        self.pbar.update(1)
        self.pbar.set_postfix({"已爬取条数":self.current_comments})

    def force_finish(self):
        # 接口显示返回时,强制推满进度条
        remaining = self.total_steps - self.current_step
        if remaining > 0:
            self.pbar.update(remaining)
        self.pbar.set_description("爬取完成(已过滤隐藏评论)")
        self.pbar.close()

    def close(self):
        self.pbar.close()




if __name__ == '__main__':

    extractor  = Video_Comment_Extractor(TEST_LINK)
    writer = CommentWriter('liuye')

    # print('====== 开始异步爬取 ======')
    # asyncio.run(
    #     extractor.crawl_all_comments_async(
    #         writer = writer,
    #         order = 'time',
    #         )
    #     )
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
    analyzer.plot_ip_distribution(False) 