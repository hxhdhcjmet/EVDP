# 对画出的图添加水印
from PIL import Image,ImageDraw,ImageFont
import os

def add_text_watermark(input_path,ouput_path,watermark_text,position=(0,0),fontsize=48,transpranency=128):
    """
    添加文字水印
    input_path:图片路径
    ouput_path:保存路径
    watermark_text:文字水印内容
    position:水印位置,默认左上角
    fontsize:文字大小
    transpranency
    """
    image=Image.open(input_path).convert('RGBA')
    #创建透明图层
    watermark_layer=Image.new("RGBA",image.size,(0,0,0,0))
    draw=ImageDraw.Draw(watermark_layer)

    #设置字体
    font=ImageFont.truetype('arial.ttf',fontsize)

    #绘制水印文字
    text_color=(255,255,255,transpranency)
    draw.text(position,watermark_text,font=font,fill=text_color)

    #图层合并
    watermarkered_image=Image.alpha_composite(image,watermark_layer)

    #合并
    watermarkered_image.save(ouput_path+'.png')



def add_image_watermarke(input_path,watermark_path,ouput_path,position=(0,0),transparency=128):
    """
    添加图片水印
    input_path:待添加水印图片文件路径
    watermark_path:水印图片路径
    output_path:保存添加了水印的文件的路径
    """
    image=Image.open(input_path).convert("RGBA")
    watermark_image=Image.open(watermark_path)

    #调整水印透明度
    watermark_image.putalpha(transparency)
    
    #粘贴水印图片并保存
    image.paste(watermark_image,position,watermark_image)
    image.save(ouput_path)


def batch_add_watertext(directory,watermark_text,fontsize=48,transparency=128):
    for filename in os.listdir(directory):
        if filename.lower().endswith(('.png','.jpg','.jpeg')):
            input_path=os.path.join(directory,filename)
            ouput_path=os.path.join(directory,f"watermarked_{filename}")
            add_text_watermark(input_path,ouput_path,watermark_text,fontsize=fontsize,transpranency=transparency)
            print(f"processed:{ouput_path}")



if __name__ == '__main__':
  directory="D:/DeskTop/test"
  watertext='Hxhdhcjmet'
  batch_add_watertext(directory,watertext)


