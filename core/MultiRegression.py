# 多元回归模块
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler # 标准化x^ = (x-mu)/sigma PLS等模型需要
from sklearn.linear_model import LinearRegression, Ridge,Lasso # 多元线性回归
from sklearn.cross_decomposition import PLSRegression # 偏最小二乘回归
from sklearn.metrics import r2_score,mean_squared_error,mean_absolute_error # 评估指标

plt.rcParams["axes.unicode_minus"]=False # 负号可显示

class MultiRegressionAnalyzer:
    """多元回归分析与可视化"""
    
    def __init__(self,data,feature_cols,reaction_col,test_size=0.2,random_state=2025109):
        """
        初始化类
        data:包含特征标量和相应标量的数据集
        feature_cols:特征列名表
        reaction_col:目标变量名
        test_size:测试集比例(测试集占总数据的比例)
        random_state:随机数种子
        """

        self.data=data.copy()
        self.feature_cols=feature_cols
        self.reaction_col=reaction_col
        self.test_size=test_size

        # 获取特征变量和相应变量
        self.X=self.data[feature_cols].values
        self.y=self.data[reaction_col].values

        # 划分训练集和测试集
        self.X_train,self.X_text,self.y_train,self.y_test=train_test_split(
            self.X,self.y,test_size=test_size,random_state=random_state
        )

        # 标准化
        self.scaler=StandardScaler()
        self.X_train_scaled=self.scaler.fit_transform(self.X_train)
        self.X_test_scaled=self.scaler.transform(self.X_test)

        # 保存模型、预测结果和评价指标
        self.models = {} # 模型
        self.predictions = {} # 预测结果
        self.metrics = {} # 评估指标


    def calculate_metrics(self,model_name,y_pred):
        """
        计算R^2,MSE,MAE等指标并储存
        """    
        self.metrics[model_name]={
            "r2":r2_score(self.y_test,y_pred),
            "mse":mean_squared_error(self.y_test,y_pred),
            "mae":mean_absolute_error(self.y_test,y_pred)
        }

    def train_linear_regression(self,model_name="Multiple Linear Regression"):
        """多元线性回归模型训练"""
        model = LinearRegression
        model.fit(self.X_train_scaled,self.y_train)

        # 预测
        y_pred=model.predict(self.X_test_scaled)

        # 储存结果
        self.models[model_name] = model
        self.predictions[model_name]=y_pred
        self.calculate_metrics(model_name,y_pred)
    def train_pls_regression(self,n_compoent=2,model_name="PLS"):
        """
        偏最小二乘回归
        """
        model = PLSRegression(n_components=n_compoent,scale=False)
        model.fit(self.X_train_scaled,self.y_train)

        # 预测
        y_pred=model.predict(self.X_test_scaled).flatten()

        self.models[model_name]=model
        self.predictions[model_name]=y_pred
        self.calculate_metrics(model_name,y_pred)

    def train_ridge_regression(self,alpha=1.0,model_name="Ridge regression"):
        """
        训练岭回归模型
        """
        model = Ridge(alpha=alpha)
        model.fit(self.X_train_scaled,self.y_train)

        y_pred=model.predict(self.X_test_scaled)
        self.models[model_name]=model
        self.predictions[model_name]=y_pred
        self.calculate_metrics(model_name,y_pred)


# 回归结果可视化
    def visualize_predict_result(self,model_name,title,x_label,y_label):
        """
        可视化回归预测结果
        model_name:模型名称
        title:图标题
        x_label:x轴
        y_label:y轴
        """
        y_pred = self.predictions[model_name]
        r2=self.metrics[model_name]

        fig,ax = plt.subplots(figsize=(8,6))
        ax.scatter(self.y_test,y_pred,alpha=0.6,label="预测值")
        ax.plot([self.y.min(),self.y.max()],[self.y.min(),self.y.max()],'r--',label="对比线y=x")
        ax.set_xlabel(x_label)
        ax.set_ylabel(y_label)
        ax.set_title(f"{title}(R^2={r2:.4f})")
        ax.legend()
        return fig
    
    def plot_residuals(self,model_name,title,x_label,y_label):
        """
        绘制残差图
        model_name:模型名称
        title:标题名称
        x_label:x坐标名称
        y_label:y坐标名称
        """
        y_pred = self.predictions[model_name]
        residulals = self.y_test-y_pred

        fig,ax = plt.subplots(figsize=(8,6))
        ax.scatter(y_pred,residulals,alpha=0.6)
        ax.axhline(y=0,color="r",linestyle="--")
        ax.set_xlabel(x_label)
        ax.set_ylabel(y_label)
        ax.set_title(title)
        
        return fig
    
    def plot_feature_importance(self,model_name,title,x_label,y_label):
        """多元回归显示各分量的重要性"""
        model=self.models[model_name]
        fig,ax=plt.subplots(figsize=(8,6))

        if isinstance(model,(LinearRegression,Ridge)):
            importance = model.coef_
            var_label = y_label if y_label else "系数值"
        elif isinstance(model,PLSRegression):
            importance = model.x_weights_[:,0]
            var_label = y_label if y_label else "第一成分权重"

        sns.barplot(x=self.feature_cols,y=importance,ax=ax)
        ax.axhline(y=0,color="r",linestyle="--")
        ax.set_xlabel(x_label)
        ax.set_ylabel(var_label)
        ax.set_title(title)
        plt.xticks(rotation=45)
        return fig
    
    def plot_pls_variance(self,model_name,title,x_label,y_label):
        model = self.models[model_name]
        if not isinstance(model,PLSRegression):
            raise ValueError("仅支持PLS回归模型")
        
        explained_X = np.cumsum(model.explained_variance_ratio_X_)
        explained_y = np.cumsum(model.explained_variance_ratio_y_)
        n_components = len(explained_X)
        
        fig,ax=plt.subplots(figsize=(8,6))
        ax.plot(range(1,n_components+1),explained_X,"o-",label="X的累计解释方差")
        ax.plot(range(1,n_components+1),explained_y,"s-",label="y的累计解释方差")
        ax.set_xlabel(x_label)
        ax.set_ylabel(y_label)
        ax.set_title(title)
        ax.legend()
        ax.grid(alpha=0.3)
        return fig
    
    def get_metrics_df(self):
        """
        获取指标
        """
        return pd.DataFrame.from_dict(self.metrics,orient="index").round(4)

    




    


