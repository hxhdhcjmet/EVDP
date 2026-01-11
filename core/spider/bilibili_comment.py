# 获取bilibili视频链接下的评论信息并保存

import requests
import re
import time
import json
from math import ceil

HEADERS = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Accept": "application/json, text/plain, */*",
    }

TEST_LINK = r'https://www.bilibili.com/video/BV1xErKBfETy'


class Video_Comment_Extractor:
    def __init__(self,link):
        self.link = link
        self.view_api = r"https://api.bilibili.com/x/web-interface/view"
        self.comment_api = r"https://api.bilibili.com/x/v2/reply/main"

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
        
        try:
            # 发送请求获取视频信息
            response= requests.get(self.view_api,params = params,headers = HEADERS,timeout = 10)
            response.raise_for_status()
            video_data = response.json()

            if video_data.get('code') == 0:
                # 成功,可以提取
                aid = video_data['data']['aid']
                print(f'成功获取视频aid:{aid}')
                self.video_aid = aid
                return aid
            else:
                print(f'获取视频信息失败,错误信息:{video_data.get('message')}')
                self.video_aid = None
                return None
        except Exception as e:
            print(f'获取视频aid时发生异常:{str(e)}')
            self.video_aid = None
            return None
    
    def get_total_comments_and_pages(self,order = 'hot'):
        """
        获取评论总数
        排序依据:order:hot(最热)、time(最新)、reply(最多回复)
        """
        # 先获取bv
        self.extract_bv_id()
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
        try:
            response = requests.get(self.comment_api,params = params,headers = HEADERS,timeout = 10)
            response.raise_for_status()
            comment_json = response.json()
            if comment_json.get('code') != 0 or not comment_json.get('data'):
                print(f'获取评论总评论数失败:{comment_json.get('message','未知错误')}')
                return 0,0
            
            # 提取总评论数和总页数
            page_data = comment_json['data'].get('page',{})
            total_count = page_data.get('count',0) # 总评论数
            page_size = page_data.get('ps',20) # 每页条数
            total_pages = ceil(total_count / page_size) if total_count > 0 else 0 # 总页数
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




if __name__ == '__main__':
    comment_extract = Video_Comment_Extractor(TEST_LINK)
    comment_extract.get_total_comments_and_pages()