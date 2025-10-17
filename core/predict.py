import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.figure import Figure
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
        self.model={} #储存训练好的模型
        self.data=data
        self.x_col=x_col
        self.y_col=y_col
        self.n=n #设置插值后点是原来的倍数
        self.new_x=np.array([]) #新的x坐标
        self.degree=1 #设置多项式回归时最高次数
        self.interpolated_results={}# 插值结果,字典储存,key为方法，value为插值结果
        self.prediction_info={}# 拟合预测信息
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
   
 
#-----------------------------------------------------------------------------------------------------------------
# 回归拟合
    def train_model(self,method='polynomial',degree=1,test_size=0.2,random_forest_params=None):
        """
        meethod:指定回归方法,默认为polynomial多项式回归
        degree:多项式回归系数,默认为1
        test_size:测试集比例
        random_forest_params:随机森林参数字典
        """
        try:
            x=np.array([float(x) for x in self.x_col])
            y=np.array([float(y) for y in self.y_col])
        except ValueError:
            print('invalid value form')

        if len(x)!=len(y):
            raise ValueError('the length of x and y is not same')
        #分割训练集和测试集
        x_train,x_test,y_train,y_test=train_test_split(x,y,test_size=test_size,random_state=42)

        if x_train.ndim !=2:
            x_train=x_train.reshape(-1,1)
        
        if x_test.ndim != 2:
            x_test=x_test.reshape(-1,1)
    
        

        result={}

        if method == 'polynomial':
            self.degree=degree
            #创建多项式回归管道
            model=Pipeline([('poly',PolynomialFeatures(degree=degree)),('linear',LinearRegression())])

            # 训练模型
            model.fit(x_train,y_train)
            self.model[method]=model

            # 预测
            y_pred_train=model.predict(x_train)
            y_pred_test=model.predict(x_test)
            y_pred=model.predict(x.reshape(-1,1))

            # 评估指标
            r2_train = r2_score(y_train, y_pred_train)
            r2_test = r2_score(y_test, y_pred_test)
            mse_train = mean_squared_error(y_train, y_pred_train)
            mse_test = mean_squared_error(y_test, y_pred_test)
            rmse_train = np.sqrt(mse_train)
            rmse_test = np.sqrt(mse_test)
            mae_train = mean_absolute_error(y_train, y_pred_train)
            mae_test = mean_absolute_error(y_test, y_pred_test)

            # 获取回归系数
            coefficients=model.named_steps['linear'].coef_
            intercept=model.named_steps['linear'].intercept_

            # 回归表达式
            regression_expression=self.build_regression_expression(coefficients,intercept)

            result = {
                'method': method,
                'y_pred_train': y_pred_train,
                'y_pred_test': y_pred_test,
                'X_train': x_train,
                'X_test': x_test,
                'y_train': y_train,
                'y_test': y_test,
                'r2_train': r2_train,
                'r2_test': r2_test,
                'mse_train': mse_train,
                'mse_test': mse_test,
                'rmse_train': rmse_train,
                'rmse_test': rmse_test,
                'mae_train': mae_train,
                'mae_test': mae_test,
                'coefficients': coefficients,
                'intercept': intercept,
                'regression_expression': regression_expression,
                'degree': degree
            }
        elif method=='random_forest':
            # 设置随机森林参数:
            if random_forest_params is None:
                random_forest_params={
                    'n_estimators':100,
                    'max_depth':None,
                    'random_state':42
                }
            
            # 创建随机森林模型
            model=RandomForestRegressor(**random_forest_params)

            # 训练模型
            model.fit(x_train,y_train)
            self.model[method]=model

            # 预测
            y_pred_train=model.predict(x_train)
            y_pred_test=model.predict(x_test)
            y_pred=model.predict(x.reshape(-1,1))

            # 计算评估指标
            r2_train = r2_score(y_train, y_pred_train)
            r2_test = r2_score(y_test, y_pred_test)
            mse_train = mean_squared_error(y_train, y_pred_train)
            mse_test = mean_squared_error(y_test, y_pred_test)
            rmse_train = np.sqrt(mse_train)
            rmse_test = np.sqrt(mse_test)
            mae_train = mean_absolute_error(y_train, y_pred_train)
            mae_test = mean_absolute_error(y_test, y_pred_test)

            result={
                'method': method,
                'y_pred_train': y_pred_train,
                'y_pred_test': y_pred_test,
                'X_train': x_train,
                'X_test': x_test,
                'y_train': y_train,
                'y_test': y_test,
                'r2_train': r2_train,
                'r2_test': r2_test,
                'mse_train': mse_train,
                'mse_test': mse_test,
                'rmse_train': rmse_train,
                'rmse_test': rmse_test,
                'mae_train': mae_train,
                'mae_test': mae_test,
                'params': random_forest_params,
                'feature_importance': model.feature_importances_
            }

        else:
            print(f'not support such method:{method}')
            return None
        self.prediction_info[method]=result
        self.prediction_results[method]=y_pred
        return result
#-----------------------------------------------------------------------------------------------------------------





    #用已经训练好的模型预测给定x的函数值
    def predict_value(self,xvalue,method):
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
        y_pred=self.model[method].predict(x_reshaped)

        return y_pred[0]
    
    def visualize_predict_result(self,X,y,y_pred,method,title,x_label,y_label,legend_actual,legend_fit):
        """
        可视化回归预测结果
        X:原自变量
        y:原因变量
        y_pred:预测得到的y值,使用self.prediction_result[method]获得
        method:使用的回归预测方法
        title:自定义标题
        x_label:x坐标名称
        y_label:y坐标名称
        legend_actual:实际值图例
        legend_fit:拟合曲线图例
        """
        
        fig=Figure(figsize=(12,5))
        ax=fig.add_subplot(121)
        ax2=fig.add_subplot(122)
        # 子图一
    
        ax.scatter(X,y,color='blue',label=legend_actual)

        #生成平滑曲线
        X_smooth=np.linspace(min(X),max(X),100).reshape(-1,1)
        y_smooth=self.model[method].predict(X_smooth)
        ax.plot(X_smooth,y_smooth,color='red',linewidth=2,label=legend_fit)# 拟合曲线

        ax.set_xlabel(x_label)
        ax.set_ylabel(y_label)
        ax.legend()
        ax.grid(True)
        ax.set_title(title)
        # if method == 'polynomial':
        #     # 当方法是多项式回归时的标题
        #     ax.set_title(f'{self.degree}阶多项式回归拟合')
        # else:
        #     ax.set_title(f'{method}回归拟合')


        
        #残差图
        
        #plt.subplot(1,2,2)
        residuals=y-y_pred
        ax2.scatter(y_pred,residuals,color='green')# 残差图
        ax2.axhline(y=0,color='red',linestyle='--')
        ax2.set_xlabel('预测值')
        ax2.set_ylabel('残差')
        ax2.set_title('残差')
        ax2.grid(True)

        fig.tight_layout()
        return fig


        








            





