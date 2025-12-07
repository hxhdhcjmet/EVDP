# 豆瓣电影top250获取,包含作品排名、名称、导演、国家、类型、年份、评分、评价人数
# 同时给出一句话形式的总结
# 目标网址：https://movie.douban.com/top250

import requests
import pandas as pd
from bs4 import BeautifulSoup
import re
import time
try:
    from .utils import save_movie_info_as_csv as save
except ImportError:
    try:
        from core.spider.utils import save_movie_info_as_csv as save
    except ImportError:
        from utils import save_movie_info_as_csv as save

URL = "https://movie.douban.com/top250"

class Movie_coll:
    def __init__(self,rank:int,name:list,year:int,country:list,director:str,mainCast:list,category:list,score:int,commentNum:int,intorduction:str):
        self.rank = rank
        self.name = name
        self.year = year
        self.country = country
        self.director = director
        self.mainCast = mainCast
        self.category = category
        self.score = score
        self.commentNum = commentNum
        self.intorduction = intorduction




def clean_movie_info(s):
    """清理爬取到的电影信息,处理多余、x0、多余空格,无用/"""
    def clean_string(s):
        if not isinstance(s,str) or s.strip() == '':
            return '' # 仅处理字符串

        # 处理\xa0,换行符,制表符
        s = s.replace('\xa0','').replace('\n','').replace('\t','').replace('...','').replace('。','.').replace('：',':')
        s = re.sub(r'\s*/\s*','/',s)
        s = s.strip().strip('/')
        s = ''.join(s.split())

        return s

    rank,title_list,info_list,rating_list = s
    clean_titles = [clean_string(item) for item in title_list]
    clean_info = [clean_string(item) for item in info_list]
    clean_rating = [clean_string(item) for item in rating_list]


    full_title = '/'.join([t for t in clean_titles if t])

    intro = clean_info[1] if len(clean_info)>1 else ''

    return {
    '排名':rank,
    '标题':full_title,
    "导演&主演&年份&地区&类型":clean_info[0],
    '简介':intro,
    '评分':clean_rating[0],
    '评价人数':clean_rating[1]
    }


def get_onePage(url,all_data): 
    headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
}
    
    respond = requests.get(url,headers=headers)
    if respond.status_code == 200:
        soup = BeautifulSoup(respond.text,'html.parser')
        #content > div > div.article > ol
        content = soup.select_one('#content div div.article ol')
        #content > div > div.article > ol > li:nth-child(1) > div > div.pic > em
        #content > div > div.article > ol > li:nth-child(1) > div > div.info
        if content is not None:
            for li,Rank in zip(content.select('li div div.info'),content.select('li div div.pic')):    
               #content > div > div.article > ol > li:nth-child(1) > div > div.info > div.hd > a > span:nth-child(1)
               rank = Rank.select_one('em').text.strip()
               #content > div > div.article > ol > li:nth-child(2) > div > div.info > div.hd > a > span.other
               title = li.select('div.hd a span')
               bg = li.select('div.bd p')
               comment = li.select('div.bd div span')

               if title and bg and comment:
                # 有多个title
                all_title = [item.text.strip() for item in title]
                # background,包括导演、主演、年份、国籍、类形
                all_bg = [back.text.strip() for back in bg if back and back.text]
                #content > div > div.article > ol > li:nth-child(2) > div > div.info > div.bd > p.quote > span
                # comment 包括评分、评价人数
                all_comment = [com.text for com in comment if com and com.text]

                if all_title and all_bg and all_comment and rank:
                    row_data=[rank,all_title,all_bg,all_comment]
                    # print(row_data)
                    cleaned_data = clean_movie_info(row_data)
                    all_data.append(cleaned_data)
                    
                else:
                    print('wrong')
                    break
            return all_data
        else:
            print('空')
    else:
        print(f'错误,状态码{respond.status_code}')
        

def crawl_top250():
    all_data = []
    start_list = [i*25 for i in range(10)]
    for i in start_list:
        url = f'https://movie.douban.com/top250?start={i}&filter='
        all_data = get_onePage(url,all_data)
    

    save(all_data,'豆瓣电影排名top250')
        

        


if __name__ == '__main__':
    crawl_top250()
