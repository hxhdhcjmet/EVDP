
from core import visualize as vs
from core import PreProcessing as pre
from core.predict import DataPredict as pred 
from core import quickPlot as plt
from core.MultiRegression import MultiRegressionAnalyzer as multiregress
import streamlit as st
from streamlit_drawable_canvas import st_canvas
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from matplotlib.figure import Figure

#--------------------------------------
#页面配置
st.set_page_config(
    page_title="数据处理与拟合工具",
    layout="wide" ,#宽布局
    page_icon="icon/home.png"
    
)
st.title("数据处理与拟合web工具")
st.markdown("点击/拖拽添加数据,自动处理、拟合与可视化")
#--------------------------------------

#--------------------------------------
# 初始化会话状态（存储临时数据）
#--------------------------------------
if "raw_data" not in st.session_state:
    st.session_state.raw_data = pd.DataFrame(columns=["x", "y"])  # 原始数据

if "cleaned_data" not in st.session_state:
    st.session_state.cleaned_data = None  # 清洗后的数据

if "selected_data" not in st.session_state:
    st.session_state.selected_data = None  # 用于插值和拟合的数据源

if "dp_instance" not in st.session_state:
    st.session_state.dp_instance = None  # 数据分析实例

if "dp.session" not in st.session_state:
    st.session_state.dp_session = None  # DataPredict实例

if "interpolated_data" not in st.session_state:
    st.session_state.interpolated_data = None  # 插值后的数据    

if "interpolated" not in st.session_state:
    st.session_state.interpolated = False  # 是否已插值

if "processed_data" not in st.session_state:
    st.session_state.processed_data = None  # 处理后的数据

if "fitted" not in st.session_state:
    st.session_state.fitted = False  # 是否已拟合

if "fit_result" not in st.session_state:
    st.session_state.fit_result = None  # 拟合结果

if "multi_regression" not in st.session_state:
    st.session_state.multi_regression = None #多元回归实例

if "multi_metrics_list" not in st.session_state:
    st.session_state.multi_metrics_list = [] # 多元回归指标




def validate_selection(regression_type,x_cols,y_col):
    """回归模型、自变量和因变量选择合理性检验"""
    errors=[]
    if y_col in x_cols:
        errors.append("因变量不能与自变量相同！")
    
    if regression_type == "单元回归" and len(x_cols)!=1:
        errors.append("单元回归仅可选择一个自变量！")
    if regression_type == "多元回归" and len(x_cols) < 1:
        errors.append("多元回归需选择至少一个自变量！")
    return errors
#--------------------------------------
#1.数据收集模块
#--------------------------------------
st.subheader("1. 数据输入")
input_col1, input_col2 = st.columns(2)

with input_col1:
    st.markdown("**方式1:鼠标在画布点击/拖拽添加数据点**")
    # 创建可交互画布（用于手动添加数据点）
    canvas_result = st_canvas(
        fill_color="rgba(255, 165, 0, 0.8)",  # 点的颜色
        stroke_width=5,
        stroke_color="rgba(0, 0, 255, 1)",
        background_color="#1E1A1A",
        height=300,
        width=500,
        drawing_mode="point",  # 支持"point"（点击）或"freedraw"（拖拽）
        key="canvas",
    )

    #画布获取点坐标
    if canvas_result.json_data is not None:
        points = pd.json_normalize(canvas_result.json_data["objects"])
        if not points.empty:
            # 获取x,y坐标
            new_data=points[["left","top"]].rename(columns={"left":"x","top":"y"})
            new_data["y"] = 300 - new_data["y"]  # 反转y轴坐标
            st.session_state.raw_data=pd.concat([st.session_state.raw_data,new_data],ignore_index=True)
with input_col2:
    st.markdown("**方式2:上传csv/Excel文件**")
    uploaded_file = st.file_uploader("选择一个文件", type=["csv", "xlsx"])
    if uploaded_file is not None:
        # 读取上传得文件
       try:
           if uploaded_file.name.endswith(".csv"):
               data=pd.read_csv(uploaded_file)
           else:
               data=pd.read_excel(uploaded_file)

          #data=pre.load_data(uploaded_file)
          # data=pre.load_data(uploaded_file)
           if data is None or not isinstance(data,pd.DataFrame):
              raise ValueError("文件读取失败,未返回有效的数据表格")
           st.session_state.raw_data=data
           st.success("文件读取成功！")
           st.dataframe(st.session_state.raw_data.head())#预览前面部分
       except Exception as e:
           st.error(f"文件读取失败: {e}")

#--------------------------------------
#2.数据清洗模块
#--------------------------------------
st.subheader("2. 数据清洗")
if not st.session_state.raw_data.empty:
    if st.button("清洗数据",type="primary"):
        with st.spinner("正在清洗数据..."):
            try:
                st.session_state.cleaned_data=pre.clean_data(st.session_state.raw_data)#使用PreProcressing模块清洗数据
                st.success(
                    f"数据清洗完成！\n"
                    f"原始数据:{len(st.session_state.raw_data)}行"
                    f"清洗后数据:{len(st.session_state.cleaned_data)}行"
                )
            except Exception as e:
                st.error(f"清洗失败:{str(e)}")
            
    
    #显示清洗后的数据
    if st.session_state.cleaned_data is not None:
        st.markdown("**清洗后的数据预览**")
        st.dataframe(st.session_state.cleaned_data,height=200)
    else:
        st.warning("请先上传或添加数据，并点击'清洗数据'按钮")


#--------------------------------------
#3.选择数据源(原始数据/清洗后数据)
#--------------------------------------
if st.session_state.raw_data is not None:
    st.subheader("3. 选择数据源")
    data_options=["原始数据"]
    if st.session_state.cleaned_data is not None:
        data_options.append("清洗后的数据")#确定可用数据源有没有清洗后数据
    
    selected_source=st.radio("选择用于插值和拟合的数据源",data_options)

    # 确认选出的数据源
    if selected_source == "原始数据":
        st.session_state.selected_data=st.session_state.raw_data
        st.markdown("**选中原始数据**")
        st.dataframe(st.session_state.selected_data.head())
    else:
        st.session_state.selected_data=st.session_state.cleaned_data
        st.markdown("**选中清洗后数据**")
        st.dataframe(st.session_state.selected_data.head())

    # 选择回归类型
    if selected_source is not None:
        regression_type = st.radio(
            "选则回归类型",
            options=["单元回归","多元回归"],
            index=None,
            help="单元回归:1个自变量->1个因变量;多元回归:多个自变量->1个因变量"
        )
     

    # 选择自变量数据和因变量数据
    if st.session_state.selected_data is not None:
        cols=st.session_state.selected_data.columns.tolist()
        col1,=st.columns(1)
        with col1:
            y_col=st.selectbox(
                "选择因变量(响应变量y)",
                options=cols,
                index=None
            ) 
           # y_col_index=st.session_state.selected_data.columns.get_loc(y_col)#获取下标
    
    st.subheader("选择自变量(特征变量x)")
    available_x_cols =[col for col in cols if col != y_col]

    if regression_type == "单元回归":
        # 单元回归，仅可选择1个自变量
        x_cols = [st.selectbox(
            "选择一个自变量",
            options=available_x_cols,
            index=None
        )]
    else:
        x_cols=st.multiselect(
            "选择至少一个自变量",
            options=available_x_cols,
            default=[]#默认第一个
        )
       # x_col_index = [st.session_state.selected_data.columns.get_loc(col) for col in x_cols] #获取下标


    if regression_type is not None:

    # 初始化DataPredict实例
        if regression_type == "单元回归":
            if st.button("初始化插值拟合分析器"):
                st.session_state.dp_instance=pred(
                    data=st.session_state.selected_data,
                    x_col=st.session_state.selected_data[x_cols],
                    y_col=st.session_state.selected_data[y_col],
                    n=10#插值倍数
         )
                st.success("分析器初始化成功！")
     # 多元回归初始化       
        elif regression_type == "多元回归":
            if st.button("初始化多元回归器"):
                st.session_state.multi_regression=multiregress(
                    data=st.session_state.selected_data,
                    feature_cols=x_cols,
                    reaction_col=y_col,
                )

                st.success("多元回归器初始化成功！")

#--------------------------------------
#4多元回归
#--------------------------------------
if st.session_state.multi_regression is not None:
    st.subheader("4.多元回归")

    fit_methods=st.multiselect(
        "选择多元回归方法",
        options=["Multiple Linear Regression","PLS","Ridge"],
        default=["Multiple Linear Regression"]
    )
    if st.button("开始执行多元拟合回归"):
        with st.spinner("正在执行拟合回归......"):

            if "Multiple Linear Regression" in fit_methods:
                st.session_state.multi_regression.train_linear_regression()
                st.session_state.multi_metrics_list.append(st.session_state.multi_regression.metrics["Multiple Linear Regression"])
            if "PLS" in fit_methods:
                st.session_state.multi_regression.train_pls_regression()
                st.session_state.multi_metrics_list.append(st.session_state.multi_regression.metrics["PLS"])
            if "Ridge" in fit_methods:
                st.session_state.multi_regression.train_ridge_regression()
                st.session_state.multi_metrics_list.append(st.session_state.multi_regression.metrics["Ridge regression"])

            st.success("拟合成功！")
            st.markdown("### 拟合指标")
            if not st.session_state.multi_metrics_list:
                st.info("无回归模型数据,请先执行回归分析！")
            else:
        # 转换为DataFrame
                col1,col2,col3=st.columns(3)
                if "Multiple Linear Regresion" in fit_methods:
                    mlr_metrics=st.session_state.multi_regression.metrics["Multiple Linear Regression"]
                    with col1:
                        st.subheader("多元线性回归")
                        st.metric(label="R^2",value=round(mlr_metrics["r2"],4))# 保留四位小数
                        st.metric(label="MSE",value=round(mlr_metrics["mse"],4))# 保留四位小数
                        st.metric(label="MAE",value=round(mlr_metrics["mae"],4))# 保留四位小数
                if "PLS" in fit_methods:
                    pls_metrics=st.session_state.multi_regression.metrics["PLS"]
                    with col2:
                        st.subheader("PLS回归")
                        st.metric(label="R^2",value=round(pls_metrics["r2"],4))
                        st.metric(label="MSE",value=round(pls_metrics["mse"],4))
                        st.metric(label="MAE",value=round(pls_metrics["mae"],4))
                if "Ridge" in fit_methods:
                    ridge_metrics=st.session_state.multi_regression.metrics["Ridge regression"]
                    with col3:
                        st.subheader("岭回归")
                        st.metric(label="R^2",value=round(ridge_metrics["r2"],4))
                        st.metric(label="MSE",value=round(ridge_metrics["mse"],4))
                        st.metric(label="MAE",value=round(ridge_metrics["mae"],4))
    





#--------------------------------------
#4插值处理
#--------------------------------------
if st.session_state.dp_instance is not None:
    st.subheader("4.数据插值")

    #选择插值方法
    interp_method=st.multiselect(
        "选择插值方法",
        options=["linear","polynomial","spline"],
        default=["linear"]
    )
    

    # 设置多项式插值阶数
    poly_degreee=1
    if "polynomial" in interp_method:
        poly_degree=st.slider("多项式插值阶数",1,10,2)
        st.session_state.dp_instance.degree=poly_degree#重置阶数
    
    if st.button("开始插值"):
        with st.spinner("正在插值..."):
            try:
                st.session_state.dp_instance.dataInterpolate(methods=interp_method)
                st.session_state.interpolated=True
                st.success(f"插值完成!,插值方法为:{interp_method}")

                # 展示插值结果
                st.markdown("**插值结果预览**")
                for method in interp_method:
                    if method in st.session_state.dp_instance.interpolated_results:
                        inter_df=pd.DataFrame({
                            "x":st.session_state.dp_instance.new_x[:10],
                            f"{method}插值y值":st.session_state.dp_instance.interpolated_results[method][:10]
                        })
                        st.subheader(f"{method}插值:")
                        st.dataframe(inter_df)
            except Exception as e:
                st.error(f"插值失败:{str(e)}")

#--------------------------------------
#5.数据拟合
#--------------------------------------
if st.session_state.dp_instance is not None and st.session_state.interpolated: 
    st.subheader("5.回归拟合") 

    # 选择拟合方法
    fit_method=st.selectbox("选择拟合方法",["polynomial","random_forest"])

    # 设置多项式回归的拟合参数
    fit_params={}
    if fit_method=="polynomial":
        fit_degree=st.slider("多项式回归阶数",1,10,2)
        fit_params["degree"]=fit_degree
    elif fit_method=="random_forest":
        n_estimators=st.slider("随机森林树数量",50,200,100)
        max_depth=st.slider("最大深度",1,20,5)
        fit_params["random_forest_params"]={

            "n_estimators":n_estimators,
            "max_depth":max_depth,
            "random_state":42
        }
    
    # 执行拟合
    if st.button("执行拟合"):
        with st.spinner(f"执行{fit_method}拟合..."):
            try:
                result=st.session_state.dp_instance.train_model(
                    method=fit_method,
                    **fit_params
                )
                st.session_state.fitted=True
                st.success("拟合完成！")

                #展示拟合指标
                st.markdown("### 拟合指标")
                col1,col2,col3=st.columns(3)
                with col1:
                    st.metric("训练集R^2",f"{result['r2_train']:.4f}")
                    st.metric("测试集R^2",f"{result['r2_test']:.4f}")
                with col2:
                    st.metric("训练集RMSE",f"{result['rmse_train']:.4f}")
                    st.metric("测试集RMSE",f"{result['rmse_test']:.4f}")
                with col3:
                    st.metric("训练集MSE",f"{result['mse_train']:.4f}")
                    st.metric("测试集MSE",f"{result['mse_test']:.4f}")

                # 多项式拟合表达式
                if fit_method == "polynomial":
                    st.latex(result["regression_expression"])
                    
            except Exception as e:
                st.error(f"拟合失败:{str(e)}")


#--------------------------------------
#6.结果可视化
#--------------------------------------

if st.session_state.fitted:
    st.subheader("6.结果可视化(配置图片信息或下载图片请使用visualize页面功能)")
    
    # # 可视化
    # fitted_method = st.selectbox("选择可视化方法",st.session_state.dp_instance.prediction_info.keys())
    # if st.button("生成可视化图表"):
    #     fig=st.session_state.dp_instance.visualize_predict_result(st.session_state.dp_instance.x_col,
    #                                                           st.session_state.dp_instance.y_col
    #                                                           ,st.session_state.dp_instance.prediction_results[fit_method]
    #                                                           ,fit_method)
    #     st.pyplot(fig)
        



        # def get_fig(method):
        #     fig = Figure(figsize=(12,5))
        #     ax1 = fig.add_subplot(121)
        #     ax2 = fig.add_subplot(122)

        #     X = np.array(st.session_state.dp_instance.x_col)
        #     y = np.array(st.session_state.dp_instance.y_col)
        #     y_pred = st.session_state.dp_instance.prediction_results[method]

        #     # 拟合曲线
        #     ax1.scatter(X,y,c='blue',label='实际值')
        #     X_smooth=np.linspace(min(X),max(X),100).reshape(-1,1)
        #     y_smooth=st.session_state.dp_instance.model[method].predict(X_smooth)
        #     ax1.plot(X_smooth,y_smooth,'r-',linewidth=2,label='拟合曲线')
        #     ax1.set_xlabel('X')
        #     ax1.set_ylabel('Y')
        #     ax1.legend()
        #     ax1.set_title(f"{method}拟合" if method != "polynomial" else f'{fit_degree}阶多项式拟合')

        #     #残差图
        #     residuals=y-y_pred
        #     ax2.scatter(y_pred,residuals,c="green")
        #     ax2.axhline(y=0,c="red",linestyle='--')
        #     ax2.set_xlabel('预测值')
        #     ax2.set_ylabel('残差')
        #     ax2.set_title('残差分布')
        #     return fig
        
        # st.pyplot(get_fig(fit_method))
    

   

    # 预测新值
    st.markdown("### 预测新值")
    x_input=st.number_input("输入x的值",value=0.0)
    if st.button ("预测y值"):
        y_pred = st.session_state.dp_instance.predict_value(x_input,fit_method)
        st.success(f"x={x_input}时,预测y值为:{y_pred:.4f}")


    








  








