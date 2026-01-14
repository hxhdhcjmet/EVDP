# 获取bilibili视频链接下的评论信息并保存

import requests
import re
import time
import json
from math import ceil
import os
import random
from utils import get_data_path,default_filename

HEADERS = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Accept": "application/json, text/plain, */*",
    }

TEST_LINK = r'https://www.bilibili.com/video/BV1ggrKBKEAD/?spm_id_from=333.1007.tianma.5-3-16.click&vd_source=903caa43b134dc6c594281212f0d6dee'


class Video_Comment_Extractor:
    def __init__(self,link,filename = default_filename()):
        self.link = link
        self.view_api = r"https://api.bilibili.com/x/web-interface/view"
        self.comment_api = r"https://api.bilibili.com/x/v2/reply/main"
        self.reply_api = r'https://api.bilibili.com/x/v2/reply/reply'

        file_path = get_data_path(filename = filename) # 这里创建的是文件夹,需要进一步创建一个同名文件
        save_file_name = filename+'.json'
        full_file_path = os.path.join(file_path,save_file_name)
        try:
            with open(full_file_path,'x',encoding = 'utf-8') as f:
                pass
            print(f'初始化成功,保存文件路径:{full_file_path},数据文件与文件夹同名,为:{save_file_name}')
        except FileExistsError:
            print('保存文件已存在,将不重复创建!')
        except Exception as e:
            print(f'初始化评论爬取类,创建文件时发生错误:{e}')
        finally:
            self.filepath = full_file_path

    

    def open_writer(self):
        """
        打开文件
        """
        self.fp = open(self.filepath,'w',encoding = 'utf-8')

    def write_comment(self,data):
        """
        写入一条文件
        """
        self.fp.write(json.dumps(data,ensure_ascii=False)+'\n')
        self.fp.flush()

    def close_writer(self):
        """
        关闭文件
        """
        if hasattr(self,'fp'):
            self.fp.close()


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
            if resp.get('code' == 0) and resp.get('data',{}).get('isLogin'):
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
    
    def crawl_all_comments(self,order = 'time'):
        """
        爬取所有评论并保存
        order : 爬取评论时的顺序,默认按时间顺序
        """
        all_comments = []

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
            
            replies = resp.get('data',{}).get('replies',{})
            
            if not replies:
                continue
            
            # 边爬取边写如文件
            self.open_writer()
            
            for reply in replies:
                # 获取每一条评论信息
                comment_data = {
                    'comment' : reply['content']['message'],
                    'like' : reply['like'],
                    'reply_count' : reply['rcount'],
                    'ctime' : reply['ctime'],
                    'user':{
                        'name' : reply['member']['uname'],
                        'level' : reply['member']['level_info']['current_level'],
                        'ip' : self.extract_ip(reply)
                        },
                        'replies' : [] # 子回复      
                    }
                # 如果有子回复,再抓
                if reply['rcount'] > 0:
                    comment_data['replies'] = self.get_sub_replies(reply['rpid'])
                
                # 写入文件
                self.write_comment(comment_data)

                # 保存到所有评论列表中
                all_comments.append(comment_data)

            # 关闭写文件器
            self.close_writer()

            return all_comments


            




if __name__ == '__main__':
    comment_extract = Video_Comment_Extractor(TEST_LINK)
    comment_extract.crawl_all_comments()