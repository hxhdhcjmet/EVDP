
from core import visualize as vs
from core.visualize import apply_global_style
from core.ui_utils import quality_report, validate_mutual_exclusive, validate_dependencies, load_file_with_timeout
from core import PreProcessing as pre
from core.predict import DataPredict as pred 
from core import quickPlot as qp
from core.MultiRegression import MultiRegressionAnalyzer as multiregress
from core.PCAAnalyzer import PCAAnalyzer
from core.FactorAnalyzer import FactorAnalyzerSimple
from core.ClusterAnalyzer import ClusterAnalyzer
import streamlit as st
from streamlit_drawable_canvas import st_canvas
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from matplotlib.figure import Figure
import logging

#--------------------------------------
#页面配置
st.set_page_config(
    page_title="数据处理与拟合工具",
    layout="wide" ,#宽布局
    page_icon="icon/home.png"
    
)
st.title("数据处理与拟合web工具")
apply_global_style()
st.markdown("点击/拖拽添加数据,自动处理、拟合与可视化")
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("evdp")
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

if "pca_analyzer" not in st.session_state:
    st.session_state.pca_analyzer = None
if "factor_analyzer" not in st.session_state:
    st.session_state.factor_analyzer = None
if "cluster_analyzer" not in st.session_state:
    st.session_state.cluster_analyzer = None




def validate_selection(regression_type: str, x_cols: list[str], y_col: str) -> list[str]:
    """CHANGED v2.1
    Validate regression type and selected columns.

    Args:
        regression_type: 回归类型
        x_cols: 自变量列
        y_col: 因变量列

    Returns:
        错误信息列表
    """
    errors = []
    if y_col in x_cols:
        errors.append("因变量不能与自变量相同！")
    if regression_type == "单元回归" and len(x_cols) != 1:
        errors.append("单元回归仅可选择一个自变量！")
    if regression_type == "多元回归" and len(x_cols) < 1:
        errors.append("多元回归需选择至少一个自变量！")
    return errors
#--------------------------------------
#1.数据收集模块
#--------------------------------------
st.subheader("步骤一：数据加载")
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
        prog = st.progress(0)
        try:
            for i in range(0, 100, 10):
                prog.progress(i)
            data = load_file_with_timeout(uploaded_file, timeout=10)
            prog.progress(100)
            if data is None or not isinstance(data, pd.DataFrame):
                raise ValueError("文件读取失败,未返回有效的数据表格")
            st.session_state.raw_data = data
            st.success("文件读取成功！")
            st.dataframe(st.session_state.raw_data.head())
        except Exception as e:
            prog.progress(0)
            st.error(f"文件读取失败或超时: {e}")
            logger.error("load_file_failed", exc_info=True)

#--------------------------------------
#2.数据清洗模块
#--------------------------------------
st.subheader("步骤二：清洗决策与质量评估")
if not st.session_state.raw_data.empty:
    open_modal = st.button("选择是否清洗数据")
    if open_modal and hasattr(st, "dialog"):
        @st.dialog("清洗选择")
        def _clean_choice_dialog():
            choice = st.radio("是否进行清洗", ["是", "否"], index=0)
            confirm = st.button("确认")
            if confirm:
                st.session_state.clean_choice = choice == "是"
                st.rerun()
    else:
        st.info("请选择是否清洗数据")
        choice = st.radio("是否进行清洗", ["是", "否"], index=1, key="clean_choice_radio")
        confirm = st.button("确认清洗选择")
        if confirm:
            st.session_state.clean_choice = choice == "是"

    target_df = st.session_state.raw_data
    if st.session_state.get("clean_choice", False):
        with st.spinner("正在清洗数据..."):
            try:
                st.session_state.cleaned_data = pre.clean_data(st.session_state.raw_data)
                target_df = st.session_state.cleaned_data
                st.success("数据清洗完成！")
            except Exception as e:
                st.error(f"清洗失败:{str(e)}")
                logger.error("clean_data_failed", exc_info=True)
    rep = quality_report(target_df)
    st.markdown("数据质量评估报告")
    st.markdown("缺失值统计")
    st.dataframe(rep["missing"], height=200)
    st.markdown("异常值检测")
    st.dataframe(rep["outliers"], height=200)


#--------------------------------------
#3.选择数据源(原始数据/清洗后数据)
#--------------------------------------
if st.session_state.raw_data is not None:
    st.subheader("步骤三：分析选项与数据源")
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
    available_x_cols = [col for col in cols if (y_col is None or col != y_col)] if 'cols' in locals() else []

    if y_col is None:
        st.info("请先选择因变量")
        x_cols = []
    else:
        if regression_type == "单元回归":
            if len(available_x_cols) == 0:
                st.warning("当前数据列不足，请检查数据源")
                x_cols = []
            else:
                x_cols = [st.selectbox(
                    "选择一个自变量",
                    options=available_x_cols
                )]
        else:
            x_cols = st.multiselect(
                "选择至少一个自变量",
                options=available_x_cols,
                default=[]
            )
       # x_col_index = [st.session_state.selected_data.columns.get_loc(col) for col in x_cols] #获取下标


    if regression_type is not None and y_col is not None and len(x_cols) > 0:

    # 初始化DataPredict实例
        if regression_type == "单元回归":
            if st.button("初始化插值拟合分析器"):
                if len(x_cols) != 1:
                    st.error("单元回归需且仅需选择一个自变量")
                else:
                    st.session_state.dp_instance = pred(
                        data=st.session_state.selected_data,
                        x_col=st.session_state.selected_data[x_cols[0]],
                        y_col=st.session_state.selected_data[y_col],
                        n=10
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
# 动态选项面板与互斥校验
#--------------------------------------
if st.session_state.selected_data is not None:
    st.subheader("分析选项")
    opt_cols = st.columns(3)
    with opt_cols[0]:
        opt_interp = st.checkbox("插值", value=st.session_state.get("opt_interp", False))
    with opt_cols[1]:
        opt_fit = st.checkbox("拟合", value=st.session_state.get("opt_fit", False))
    with opt_cols[2]:
        opt_pca = st.checkbox("PCA", value=st.session_state.get("opt_pca", False))
    chosen = {"插值": opt_interp, "拟合": opt_fit, "PCA": opt_pca}
    selected_opts = {k for k, v in chosen.items() if v}
    st.session_state.opt_interp = opt_interp
    st.session_state.opt_fit = opt_fit
    st.session_state.opt_pca = opt_pca
    errors = validate_mutual_exclusive(selected_opts)
    dep_errors = validate_dependencies(selected_opts, {
        "dp_ready": st.session_state.dp_instance is not None,
        "interpolated": st.session_state.get("interpolated", False)
    })
    all_err = errors + dep_errors
    if all_err:
        for e in all_err:
            st.error(e)
    else:
        st.success("选项校验通过")

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
                if "Multiple Linear Regression" in fit_methods:
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
if st.session_state.dp_instance is not None and st.session_state.get("opt_interp", False):
    st.subheader("4.数据插值")

    #选择插值方法
    interp_method=st.multiselect(
        "选择插值方法",
        options=["linear","polynomial","spline"],
        default=["linear"]
    )
    

    # 设置多项式插值阶数
    if "polynomial" in interp_method:
        poly_degree = st.slider("多项式插值阶数",1,10,2)
        st.session_state.dp_instance.degree = poly_degree
    
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
                        inter_df = pd.DataFrame({
                            "x": st.session_state.dp_instance.new_x[:10],
                            f"{method}插值y值": st.session_state.dp_instance.interpolated_results[method][:10]
                        })
                        st.subheader(f"{method}插值:")
                        st.dataframe(inter_df)
            except Exception as e:
                st.error(f"插值失败:{str(e)}")
                logger.error("interpolate_failed", exc_info=True)

#--------------------------------------
#5.数据拟合
#--------------------------------------
    if st.session_state.get("opt_fit", False) and st.session_state.dp_instance is not None and st.session_state.interpolated:
        st.subheader("5.回归拟合")

        fit_method = st.selectbox("选择拟合方法", ["polynomial", "random_forest"]) 

        fit_params = {}
        if fit_method == "polynomial":
            fit_degree = st.slider("多项式回归阶数", 1, 10, 2)
            fit_params["degree"] = fit_degree
        elif fit_method == "random_forest":
            n_estimators = st.slider("随机森林树数量", 50, 200, 100)
            max_depth = st.slider("最大深度", 1, 20, 5)
            fit_params["random_forest_params"] = {
                "n_estimators": n_estimators,
                "max_depth": max_depth,
                "random_state": 42,
            }

        if st.button("执行拟合"):
            with st.spinner(f"执行{fit_method}拟合..."):
                try:
                    result = st.session_state.dp_instance.train_model(method=fit_method, **fit_params)
                    st.session_state.fitted = True
                    st.success("拟合完成！")

                    st.markdown("### 拟合指标")
                    col1, col2, col3 = st.columns(3)
                    with col1:
                        st.metric("训练集R^2", f"{result['r2_train']:.4f}")
                        st.metric("测试集R^2", f"{result['r2_test']:.4f}")
                    with col2:
                        st.metric("训练集RMSE", f"{result['rmse_train']:.4f}")
                        st.metric("测试集RMSE", f"{result['rmse_test']:.4f}")
                    with col3:
                        st.metric("训练集MSE", f"{result['mse_train']:.4f}")
                        st.metric("测试集MSE", f"{result['mse_test']:.4f}")

                    if fit_method == "polynomial":
                        st.latex(result["regression_expression"])
                except Exception as e:
                    st.error(f"拟合失败:{str(e)}")
                    logger.error("fit_failed", exc_info=True)


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


if st.session_state.selected_data is not None and st.session_state.get("opt_pca", False):
    st.subheader("7. 高级分析")
    num_cols = st.session_state.selected_data.select_dtypes(include=["number"]).columns.tolist()
    with st.expander("PCA 主成分分析", expanded=False):
        pca_cols = st.multiselect("选择特征列", options=num_cols, default=num_cols[:2])
        scale_opt = st.checkbox("标准化", value=True)
        valid_pca = bool(pca_cols) and len(pca_cols) >= 2
        if valid_pca:
            n_comp = st.slider("成分个数", min_value=2, max_value=len(pca_cols), value=2)
        else:
            st.warning("至少选择两列数值特征")
        if st.button("执行PCA"):
            if valid_pca:
                st.session_state.pca_analyzer = PCAAnalyzer(st.session_state.selected_data, pca_cols, n_components=n_comp, scale=scale_opt)
                try:
                    st.session_state.pca_analyzer.fit()
                    st.markdown("Variance Contribution Rate")
                    st.dataframe(pd.DataFrame({"Component": [f"PC{i+1}" for i in range(n_comp)], "Explained Variance Ratio": st.session_state.pca_analyzer.explained_variance_ratio_}))
                    fig1 = st.session_state.pca_analyzer.plot_scree()
                    st.pyplot(fig1)
                    fig2 = st.session_state.pca_analyzer.plot_biplot()
                    if fig2 is not None:
                        st.pyplot(fig2)
                except Exception:
                    st.error("PCA execution failed")
                    logger.error("pca_failed", exc_info=True)
            else:
                st.warning("至少选择两列数值特征")
    with st.expander("因子分析", expanded=False):
        fa_cols = st.multiselect("选择特征列", options=num_cols, key="fa_cols", default=num_cols[:3])
        scale_f = st.checkbox("标准化", value=True, key="fa_scale")
        valid_fa = bool(fa_cols) and len(fa_cols) >= 2
        if valid_fa:
            n_f = st.slider("因子个数", min_value=2, max_value=len(fa_cols), value=2, key="fa_n")
        else:
            st.warning("至少选择两列数值特征")
        if st.button("执行因子分析"):
            if valid_fa:
                st.session_state.factor_analyzer = FactorAnalyzerSimple(st.session_state.selected_data, fa_cols, n_factors=n_f, scale=scale_f)
                try:
                    st.session_state.factor_analyzer.fit()
                    fig = st.session_state.factor_analyzer.plot_loadings_heatmap()
                    if fig is not None:
                        st.pyplot(fig)
                except Exception:
                    st.error("因子分析失败")
                    logger.error("fa_failed", exc_info=True)
            else:
                st.warning("至少选择两列数值特征")
    with st.expander("聚类分析", expanded=False):
        cl_cols = st.multiselect("选择特征列", options=num_cols, key="cl_cols", default=num_cols[:2])
        method = st.selectbox("聚类方法", options=["KMeans", "层次聚类", "DBSCAN"], index=0)
        scale_c = st.checkbox("标准化", value=True, key="cl_scale")

        # 参数控件需在按钮前定义，避免回调后取不到值
        kmeans_k = st.slider("簇数(KMeans/层次)", 2, 10, 3, key="kmeans_k")
        agg_link = st.selectbox("链接方式(层次)", options=["ward", "complete", "average", "single"], index=0, key="agg_link")
        db_eps = st.slider("eps(DBSCAN)", 0.1, 2.0, 0.5, 0.1, key="db_eps")
        db_min = st.slider("min_samples(DBSCAN)", 3, 20, 5, key="db_min")

        run_cluster = st.button("执行聚类")
        if run_cluster:
            if cl_cols and len(cl_cols) >= 2:
                st.session_state.cluster_analyzer = ClusterAnalyzer(st.session_state.selected_data, cl_cols, scale=scale_c)
                try:
                    labels = None
                    if method == "KMeans":
                        labels = st.session_state.cluster_analyzer.fit_kmeans(n_clusters=kmeans_k)
                    elif method == "层次聚类":
                        labels = st.session_state.cluster_analyzer.fit_agglomerative(n_clusters=kmeans_k, linkage=agg_link)
                    else:
                        labels = st.session_state.cluster_analyzer.fit_dbscan(eps=db_eps, min_samples=db_min)
                    st.session_state.selected_data["cluster_label"] = labels
                    st.dataframe(st.session_state.selected_data[[*cl_cols, "cluster_label"]].head())
                    fig = st.session_state.cluster_analyzer.plot_clusters()
                    if fig is not None:
                        st.pyplot(fig)
                except Exception:
                    st.error("聚类分析失败")
                    logger.error("cluster_failed", exc_info=True)
            else:
                st.warning("至少选择两列数值特征")
        

    
    
    






  








