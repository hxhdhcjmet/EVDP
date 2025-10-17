# 使用OCR将图片、pdf格式的文件读取到excel中，便于后续处理
import pandas as pd
import os
from paddleocr import PaddleOCR

def extract_texts_and_scores(result:dict):
    """
    将ocr读取结果读取文本内容和置信度
    result:ocr读取的结果
    """
    result_data={'texts':[],'scores':[]}

    if isinstance(result,list) and len(result)>0:
        # 当result为list且不为空
        result_dict=result[0]
    else:
        print('wrang!the input is not a list or empty')
        return result_data
    
    if 'rec_texts' in result_dict:#读取rec_text
        result_data['texts']=[text.strip() for text in result_dict['rec_texts'] if text.strip()]
    else:
        print('no key named "rec_text" ')

    if 'rec_scores' in result_dict:#读取rec_scores
        result_data['scores']=result_dict['rec_scores']
    else:
        print('no key named "rec_scores" ')
    
    if len(result_data['texts']) != len(result_data['scores']):#文本内容和置信度长度不一致提示
        print('attention, the length of texts and scores are not same')

    return  result_data

def save_to_excel(texts,scores,output_path):
    """
    将ocr结果保存到excel文件中
    texts:文本内容
    scores:置信度
    output_path:保存路径
    """
    try:
        if not texts:
            print('warn,empty text,can not generate Excel file')
            return False
        valid_scores=[s for s in scores if isinstance(s,(int,float))]
        #计算平均置信度
        ave_score=sum(valid_scores)/len(valid_scores) if valid_scores else 0.0

        data={
            "序号":range(1,len(texts)+1),
            "识别文本":[text.strip() for text in texts],
            "单条置信度":[f'{s:.4f}' if isinstance(s,(int,float)) else "无" for s in scores[:len(texts)]]
        }
        df=pd.DataFrame(data)

        df.loc[len(df)]={
            "序号":"平均置信度",
            "识别文本":"",
            "单条置信度":f"{ave_score:.4f}"
        }

        #保存到Excel
        output_dir=os.path.dirname(output_path)
        if output_dir and not os.path.exists(output_dir):
            os.makedirs(output_dir,exist_ok=True)

        # 保存文件
        df.to_excel(output_path,index=False,engine='openpyxl')
        print(f'\nExcel save succeed')
        print(f'totally average score:{ave_score:.4f}')
        return True
    except Exception as e:
        print(f"fail to save excel:{str(e)}")
        return False

    





ocr=PaddleOCR(lang='ch')

image=r'D:/DeskTop/test.png'

result=extract_texts_and_scores(ocr.predict(image))
save_to_excel(result['texts'],result['scores'],r'D:/DeskTop/test.xlsx')