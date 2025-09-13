import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from scipy import interpolate
from sklearn.linear_model import LinearRegression
from sklearn.ensemble import RandomForestRegressor
from sklearn.model_selection import train_test_split
from sklearn.metrics import mean_absolute_error,r2_score,mean_squared_error
from sklearn.pipeline import Pipeline
import warnings

warnings.filterwarnings('ignore')
# 字体设置
plt.rcParams['font.family']=['SimHei']
plt.rcParams['axes.unicode_minus']=False


class DataPredict:
    def __init__(self,data=None,x_col=None,y_col=None,n=10):
        """
        数据预测类
        data:原始数据
        x_col:自变量
        y_col:因变量
        """
        self.data=data
        self.x_col=x_col
        self.y_col=y_col
        self.n=n #设置插值后点是原来的倍数
        self.new_x=np.array([]) #新的x坐标
        self.interpolated_results={}# 插值结果,字典储存,key为方法，value为插值结果
        self.prediction_results={}# 拟合预测结果

    # 插值
    def dataInterpolate(self,methods=['linear','polynomial','spline']):
        """
        数据插值
        method:插值方法,linear:线性插值,polynomial:多项式插值，spline:样条插值
        """
        # 没有数据，抛出错误
        if self.data is None:
            raise ValueError('no original data')
        
        # 确保数据按时间排序
        known_x=np.asarray(self.x_col)
        known_y=np.asarray(self.y_col)
        x_col_min=self.x_col.min()
        x_col_max=self.x_col.max()
        all_indices=np.linspace(start=x_col_min,stop=x_col_max,num=self.n*len(self.x_col),endpoint=True)
        for value in all_indices:
            self.new_x=np.append(self.new_x,value)
      

        # 线性插值
        if 'linear' in methods:
            f_linear=interpolate.interp1d(known_x,known_y,kind='linear')#创建线性插值函数
            self.interpolated_results['linear']=f_linear(all_indices)
        # 多项式插值    
        if 'polynomial' in methods:
            #选取多项式次数,避免过度拟合
            degree=min(5,len(known_x)-1) if known_x > 1 else 1
            f_poly=interpolate.interp1d(known_x,known_y,kind='quadratic' if degree >=2 else 'linear')#最高次数小于2则用线性插值
            self.interpolated_results['polynomial']=f_poly(all_indices)
        #样条插值
        if 'spline' in methods:
            if len(known_x)>=4: #样条插值至少需要4个点 
                tck=interpolate.splrep(known_x,known_y,s=0)
                self.interpolated_results['spline']=interpolate.splev(all_indices,tck,der=0)
            else:
                print('thr original data is too sparase to perform spline interpolation and this method is skipped')#数值不够提示信息
    
    # 设定多项式回归阶数
    def set_polynomial_degree(self):
        """
        设置多项式回归的阶数
        """
        try:
            print:('Enter the polynomial regression degree(default is 1,i.e.,linear regression)')
            degree=input().strip()
            if degree=='':
                return 1

    # 回归拟合
    def Prediction(self,methods=['linear_regression','random_forest']):
        """
        回归拟合
        methods:指定方法,linear_regression:线性回归  random_forest:随机森林
        """
        try:
            x=np.array([float(x) for x in self.x_col])
            y=np.array([float(y) for y in self.y_col])
        except ValueError:
            print('invalid value form')

        if len(x)!=len(y):
            raise ValueError('the length of x and y is not same')
        
        # 进行回归并展示相关数据
        X_reshape=x.reshape(-1,1)

        #创建并训练数据
        model=LinearRegression()
        model.fit(X_reshape,y)

        y_pred=model.predict(X_reshape)

        #计算评估指标
        r2=r2_score(y,y_pred)
        mse=mean_squared_error(y,y_pred)
        rmse=np.sqrt(mse)

        #计算SSE,SSR,SST
        SSE=np.sum((y-y_pred)**2)
        SSR=np.sum((y_pred-np.mean(y))**2)
        SST=np.sum((y-np.mean((y)))**2)

        #获取回归系数
        coeff=model.named_steps['linear'].coef_
        intercept=model.named_steps['linear'].intercept_

        #构建回归表达式
        regression_expression=build_regre




            





