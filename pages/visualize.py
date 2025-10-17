import streamlit as st
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from io import BytesIO,StringIO
from PIL import Image
from core.predict import DataPredict as pred
from core import watermark_utils as wm



st.set_page_config(
    page_title="拟合数据可视化与图片下载",
    page_icon="icon/visualize.png",
    layout="wide"
)
st.title("拟合数据可视化与图片下载")
plt.rcParams['font.family']=['SimHei']
plt.rcParams['axes.unicode_minus']=False

def save_fig(fig,format='png',dpi=300):
    """
    下载绘制好的图片
    """
    buf=BytesIO()
    fig.savefig(buf,format=format,dpi=dpi,bbox_inches="tight")
    buf.seek(0)
    return buf
    
# 确保可视化数据存在
if "dp_instance" not in st.session_state and st.session_state.dp_instance is None and st.session_state.multi_regression is None:
    st.error("请先执行拟合！")
elif st.session_state.dp_instance is not None:
    dp_instance = st.session_state.dp_instance
    fit_methods = list(dp_instance.prediction_info.keys())
    if not fit_methods:
        # 拟合方法为空
        st.error("未找到单元拟合结果,请先执行拟合")
    else:
        # 选择拟合方法
        fit_method=st.selectbox("选择拟合方法",fit_methods)
elif st.session_state.multi_regression is not None:
    multi_regression = st.session_state.multi_regression
    fit_methods = list(multi_regression.models.keys())
    if not fit_methods:
        st.error("未找到多元拟合结果，请先执行拟合")
    else:
        fit_method = st.selectbox("选择拟合方法",fit_methods)






    #--------------------------------------
#自定义图片内容
#--------------------------------------
    st.subheader("自定义图片内容")
    with st.expander("点击展开自定义内容(或者不设置,使用默认值)",expanded=True):
        col1,col2,col3=st.columns(3)
        with col1:
            plot_title=st.text_input("标题",value=f"{fit_method}拟合结果可视化")
            x_label=st.text_input("x坐标名称",value='X')
            y_label=st.text_input("y坐标名称",value='Y')
        with col2:
            # 图例
            legend_actual=st.text_input("实际值图例",value="实际数据点")
            legend_fit=st.text_input("拟合曲线图例",value="拟合曲线")
            # 图片格式与DPI:
            img_format=st.selectbox("保存格式",["png","pdf","svg"],index=0)
            img_dpi=st.slider("图片清晰度",100,600,300)
        
        with col3:
            add_wm=st.checkbox("是否添加水印?",value=False)
            if add_wm:
                col31,col32=st.columns(2)
                with col31:
                    watermark_text=st.text_input("水印文字","CONFIDENTIAL")
                    position=st.selectbox("水印位置",["center","bottom-right","top-left"])
                with col32:
                    upload_logo=st.file_uploader("上传一张jpg/png水印图片(也可不上传,仅使用文字水印)",type=["png","jpg","jepg"])
                    position_logo=st.selectbox("水印图片位置",["center","bottom-right","top-left"])
                    alpha=st.slider("水印图片透明度",0.0,1.0,0.3,0.05)
                    scale=st.slider("水印图片大小",0.05,0.5,0.2,0.05)

        

#--------------------------------------
#保存图片(用户选择是否下载)
#--------------------------------------
    if st.button("生成可视化图片"):
        if st.session_state.dp_instance is not None:
            fig=st.session_state.dp_instance.visualize_predict_result(
                st.session_state.dp_instance.x_col,
                st.session_state.dp_instance.y_col,
                st.session_state.dp_instance.prediction_results[fit_method],
                fit_method,
                plot_title,
                x_label,
                y_label,
                legend_actual,
                legend_fit
        )
        elif st.session_state.multi_regression is not None:
            fig=st.session_state.multi_regression.visualize_predict_result(
                fit_method,
                plot_title,
                x_label,
                y_label,
                legend_actual,
                legend_fit
            )

        if add_wm:
            fig=wm.add_watermark(fig,watermark_text,position=position)
            if upload_logo is not None:
                fig=wm.add_image_watermark(fig,upload_logo,alpha=alpha,position=position_logo,scale=scale)

        st.pyplot(fig) # 显示图片

        st.subheader("保存图片")

        # 保存图片
        img_bytes=save_fig(fig,format=img_format,dpi=img_dpi)

        st.download_button(
            label=f"下载图片({img_format}格式)",
            data=img_bytes,
            file_name=f"拟合可视化_{fit_method}.{img_format}",
            mime=f"image/{img_format}" if img_format != "pdf" else "application/pdf"
        )



    
    


    


