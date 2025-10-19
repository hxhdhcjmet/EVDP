# 缺少数据时的一个简易爬虫，获取所需信息
from bs4 import BeautifulSoup
from parsel import Selector
from typing import List
import requests

FIRST_N_PAGE = 10
BASE_HOST = 'https://www.ptt.cc'
HEADERS= {
    "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123.0.0.0 Safari/537.36"
}



class NoteContent():
    title:str = ""
    author: str = ""
    publish_data : str = ""
    detail_link : str = ""


    def __str__(self):
        return f"""
        Title:{self.title}
        User:{self.author}
        Publish_data:{self.publish_data}
        Detail_link:{self.detail_link}
        """






class NotePushComment:
    """
    推文储存器
    """
    push_user_name:str = ""
    push_content:str = ""
    push_time:str = ""
    
    def __repr__(self):
        return f"NotePushComment(push_user_name={self.push_user_name},push_content={self.push_content},push_time={self.push_time}"




class NoteContentDetail:
    """
    帖子
    """
    title:str = ""
    author:str = ""
    publish_datetime:str = ""
    detail_link:str = ""
    push_comment:List[NotePushComment]=[]

    def __str__(self):
              return f"""
Title: {self.title}
User: {self.author}
Publish Datetime: {self.publish_datetime}
Detail Link: {self.detail_link}
Push Comments: {self.push_comment}        
"""







def parse_html_use_bs(html_content:str)-> NoteContent :
            # 初始化帖子保存器
            note_content=NoteContent()
            soup = BeautifulSoup(html_content,"lxml")
            # 标题
            note_content.title = soup.select("di.r-ent div.title a")[0].text.strip()
            # 作者
            note_content.author = soup.select("div.r-ent div.meta div.author")[0].text.strip()
            # 日期
            note_content.publish_data = soup.select("div.r-ent div.meta div.data")[0].text.strip()
            # 帖子链接
            note_content.detail_link = soup.select("div.r-ent div.title a")[0]["href"]
            return note_content


def parse_html_use_parse(html_content:str):
            "使用parsel提取帖子标题、作者、发布日期:基于xpath选择器提取"
            note_content = NoteContent()
            # 创建选择器对象
            selector = Selector(text=html_content)
            # Xpath提取标题并除去左右空格
            note_content.title = selector.xpath("//div[@class='r-ent']/div[@class='title']/a/text()").extract_first().strip()
            # xpath提取作者
            note_content.author = selector.xpath("//div[@class='r-ent']/div[@class='meta']/div[@class='data']/text()").extract_first().strip()
            # 提取帖子链接
            note_content.detail_link = selector.xpath("//div[@class='r-ent']/div[@class='title']/a/@href").extract_first()

            print("parsel"+"*"*30)
            print(note_content)
            print("parsel"+"*"*30)

def get_previous_page_number()-> int:
            """
            打开首页,提取上一页的分页Number
            """
            url_append = "/bbs/Stock/index/html"
            response = requests.get(url=BASE_HOST+url_append,headers=HEADERS)
            
            if response.status_code != 200:
                raise Exception("error status code for reason:",response.text)

            soup=BeautifulSoup(response.text,"lxml")
            css_selector="#action-bar-container > div > div.btn-group.btn-group-paging > a:nth-child(2)"
            pagination_link = soup.select(css_selector)[0]["href"].strip()

            previous_page_number = int(pagination_link.replace("/bbs/Stock/index","").replace(".html",""))# 前面/bbs/Stock/index和
            # 后面.html赋空，得到中间数字

            return previous_page_number



def fetch_bbs_note_list(previous_page_number:int)->List[NoteContent]:
        """
        获取前n页帖子列表
        """
        notes_list:List[NoteContent]= []
        start_page_num = previous_page_number+1
        end_page_num = start_page_num - FIRST_N_PAGE
        for page_num in range(start_page_num,end_page_num,-1):
            print(f"开始获取第{page_num}页的帖子列表...")

            # 根据page_num修改url
            url = f"/bbs/Stock/index{page_num}.html"
            response = requests.get(url=BASE_HOST+url,headers=HEADERS)
            if response.status_code !=200:
                print(f"第{page_num}页帖子获取异常.原因:{response.text}")
                cotinue

            # BeautifulSoup的CSS选择器解析数据
            soup = BeautifulSoup(respose.text,"lxml")
            all_note_elements = soup.select("div.r-ent")
            for note_element in all_note_elements:
                note_content : NoteContent = parse_html_use_bs(note_element.prettify())
                notes_list.append(note_content)


            print(f"结束获取第{page_num}页的帖子列表,本次获取到:{len(all_note_elements)}篇帖子...")
        return notes_list

def fetch_bbs_note_detail(note_content:NoteContent)->NoteContentDetail:
    """
    获取帖子详情页数据
    """
    print(f"开始获取帖子{note_content.detail_link}详情页......")
    note_content_detail = NoteContentDetail()

    note_content_detail.title = note_content.title
    note_content_detail.author = note_content.author
    note_content_detail.detail_link = BASE_HOST+note_content.detail_link

    response = requests.get(url=BASE_HOST + note-content.detail_link,headers=HEADERS)
    if response.status_code!=200:
        print(f"帖子:{note_content.title}获取异常,原因{response.text}")
        return note_content_detail

    soup = BeautifulSoup(response.text,"lxml")
    note_content_detail.publish_datetime = soup.select("#main-content > div:nth-child(4) > span.article-meta-value")[0].text


    # 处理推文
    note_content_detail.push_comment=[]
    all_note_elements = soup.select("#main-content > div.push")
    for push_element in all_note_elements:
        note_push = NotePushComment()
        if len(push_element.select("span"))<3:
            continue


        note_push_comment.push_user_name = push_element.select("span")[1].text.strip()
        note_push_comment.push_content = push_comment.select("span")[2].text.strip().replace(":","")
        note_push_comment.push_time = push_element.select("span")[3].text.strip()
        note_content_detail.push_comment.append(note_push_comment)


    print(note_content_detail)
    return note_content_detail







def run_crawler(save_notes:List[NoteContentDetail]):
    """
    爬虫主程序
    """

    previous_number:int = get_previous_page_number()

    note_list:List[NoteContent] = fetch_bbs_note_list(previous_number)

    for note_content in note_list:
        if not note_content.detail_link:
            continue
        note_content_detail = fetch_bbs_note_detail(note_content)
        save_notes.append(note_content_detail)

    print("任务爬取完成......")




if __name__ == "__main__":
    all_note_elements_detail:List[NoteContentDetail] = []
    run_crawler(all_note_elements_detail)


    

