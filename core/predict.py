import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from scipy import interpolate
from sklearn.linear_model import LinearRegression
from sklearn.preprocessing import PolynomialFeatures
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
        self.model=None #储存训练好的模型
        self.data=data
        self.x_col=x_col
        self.y_col=y_col
        self.n=n #设置插值后点是原来的倍数
        self.new_x=np.array([]) #新的x坐标
        self.degree=1 #设置多项式回归时最高次数
        self.interpolated_results={}# 插值结果,字典储存,key为方法，value为插值结果
        self.prediction_results={}# 拟合预测结果

       # 设定多项式回归阶数
    def set_polynomial_degree(self)-> int :
        """
        设置多项式回归的阶数
        """
        try:
            print('Enter the polynomial regression degree(default is 1,i.e.,linear regression)')
            degree=input().strip()
            if degree=='':
                return 1
            return int(degree)
        except ValueError:
            print('valid input,use default value 1')
            return 1



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
            degree=self.set_polynomial_degree()#设置多项式次数         #min(5,len(known_x)-1) if known_x > 1 else 1
            f_poly=interpolate.interp1d(known_x,known_y,kind='quadratic' if degree >=2 else 'linear')#最高次数小于2则用线性插值
            self.interpolated_results['polynomial']=f_poly(all_indices)
        #样条插值
        if 'spline' in methods:
            if len(known_x)>=4: #样条插值至少需要4个点 
                tck=interpolate.splrep(known_x,known_y,s=0)
                self.interpolated_results['spline']=interpolate.splev(all_indices,tck,der=0)
            else:
                print('thr original data is too sparase to perform spline interpolation and this method is skipped')#数值不够提示信息
    


    def build_regression_expression(self,coefficients,intercept)-> str:
          """
         构建回归表达式字符串
         """
          if self.degree==1:
              # 线性回归
              return f"y={intercept:.4f}+{coefficients[1]:.4f}*x"
          else:
          #多项式回归
            expression=f'{intercept:.4f}'
            for i in range(1,len(coefficients)):
                power=i
                coeff=coefficients[i]
                if coeff>=0:
                    expression+f'+{coeff:.4f}*x^{power}'
                else:
                    expression+f'-{coeff:.4f}*x^{power}'
            return expression
   
 



    # 回归拟合
    def Prediction(self,degree=1):
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
        
        self.degree=degree
        # 进行回归并展示相关数据
        X_reshape=x.reshape(-1,1)
        #创建多项式回归管道
        model=Pipeline([('poly',PolynomialFeatures(degree=degree)),('linear',LinearRegression())])

        #创建并训练数据
        model.fit(X_reshape,y)
        self.model=model

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
        coefficients=model.named_steps['linear'].coef_
        intercept=model.named_steps['linear'].intercept_

        #构建回归表达式
        regression_expression=self.build_regression_expression(coefficients,intercept)
        self.prediction_results['linear']=y_pred
        
        #返回内容
        return{
            'y_pred':y_pred,
            'r2':r2,
            'mse':mse,
            'rmse':rmse,
            'SSE':SSE,
            'SSR':SSR,
            'SST':SST,
            'coefficients':coefficients,
            'intercept':intercept,
            'regression_expression':regression_expression
        }
    

    #用已经训练好的模型预测给定x的函数值
    def predict_value(self,xvalue):
        """
        计算给定xvalue处的函数回归值
        """
        if self.model==None:
            print('please perform a regression analsis first')
            return None
        
        #尝试对输入的数计算预测值
        try:
            x=float(xvalue)
        except ValueError:
            print('invalid input')
            return None
        
        #执行预测
        x_reshaped=np.array([[x]])
        y_pred=self.model.predict(x_reshaped)

        return y_pred[0]
    
    def visualize_predict_result(self,X,y,y_pred):
        """
        可视化回归预测结果
        """
        plt.figure(figsize=(12,5))

        plt.subplot(1,2,1)
        plt.scatter(X,y,color='blue',label='实际值')

        #生成平滑曲线
        X_smooth=np.linspace(min(X),max(X),100).reshape(-1,1)
        y_smooth=self.model.predict(X_smooth)
        plt.plot(X_smooth,y_smooth,color='red',linewidth=2,label='拟合结果曲线')

        plt.xlabel('X')
        plt.ylabel('y')
        plt.title(f'{self.degree}阶多项式回归拟合')
        plt.legend()
        plt.grid(True)

        #残差图
        plt.subplot(1,2,2)
        residuals=y-y_pred
        plt.scatter(y_pred,residuals,color='green')
        plt.axhline(y=0,color='red',linestyle='--')
        plt.xlabel('预测值')
        plt.ylabel('残差')
        plt.title('残差')
        plt.grid(True)

        plt.tight_layout()
        plt.show()


        








            





