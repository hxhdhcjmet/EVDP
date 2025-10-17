# 为可视化后的图片添加文字水印再下载
import matplotlib.pyplot as plt
from PIL import Image
import numpy as np
from io import BytesIO

def add_watermark(fig,text="sample watermark",alpha=0.2,fontsize=40,position="center"):
    """
    fig:待添加水印的图片
    text:水印信息
    alpha:水印透明度
    fontsize:字体大小
    position:水印位置
    """

    bbox=dict(boxstyle="round,pad=0.3",fc="none",ec="none",alpha=alpha)

    if position == "center":
        # 中间
        x,y = 0.5,0.5
        ha,va = "center","center"
    elif position == "bottom-right":
        # 右下角
        x,y = 0.95,0.05
        ha,va ="right","bottom"
    elif position == "top-left":
        x,y = 0.05,0.95
        ha,va = "left","top"
    else:
        x,y = 0.5,0.5
        ha,va = "center","center"

    # 添加文字到图窗
    fig.text(x,y,text,fontsize=fontsize,
             color="gray",
             alpha=alpha,
             ha=ha,va=va,
             rotation=30,
             transform=fig.transFigure)
    return fig

def add_image_watermark(fig,image_file,alpha=0.3,position="bottom-right",scale=0.2,margin=0.02):
    """
    fig:待添加水印的图片
    image_file:streamlit 上传文件对象 UploadedFile
    alpha:透明度(0~1)
    position:水印位置
    scale:缩放比例
    margin:边缘间距
    """
    logo=Image.open(image_file).convert("RGBA")

    width,height=logo.size
    fig_w,fig_h=fig.get_size_inches()

    width_frac=float(scale)

    height_frac=width_frac*(fig_w/fig_h)*(height/width)

    # 根据位置计算坐标
    if position == "bottom-right":
        left = 1-width_frac -margin
        bottom=margin
    elif position == "top-left":
        left = margin
        bottom = 1-height_frac- margin
    elif position == "center":
        left = (1-width_frac)/2
        bottom = (1-height_frac)/2
    else:
        # 默认放右下角
        left = 1-width_frac-margin
        bottom=margin

    wm_ax=fig.add_axes([left,bottom,width_frac,height_frac],zorder=100)
    wm_ax.imshow(np.array(logo),aspect="auto",alpha=alpha)
    wm_ax.axis("off")
    return fig

    
    


