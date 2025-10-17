import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import os
import seaborn as sns
from typing import Optional,List
from matplotlib import font_manager
import re


# 设置中文


plt.rcParams["font.family"] = ["SimHei"]
plt.rcParams["font.serif"] = ["SimHei"]
plt.rcParams["font.sans-serif"] = ["SimHei"]
plt.rcParams['axes.unicode_minus'] = False
sns.set_theme(font_scale=1.2)
sns.set_style('whitegrid')

class DataVisualizer:
    """
    可视化类
    """
    def __init__(self,output_dir:dir='plots'):
        self.output_dir=output_dir
        os.makedirs(self.output_dir,exist_ok=True)
        self.num_cols=[]# 数值型列
        self.notNum_cols=[]# 非数值型列

    def save_path_check(self,path:str)->str:
        return re.sub(r'[\/:*?"<>|]','_',path)   #把path中可能造成路径问题的部分给替换成_



    def prepare_columns(self,dataContent:pd.DataFrame):
        """
        准备数据,替换num_cols和notNum_cols
        """
        self.num_cols=dataContent.select_dtypes(include=['number']).columns.tolist()
        self.notNum_cols=dataContent.select_dtypes(include=['object','category','datetime64']).columns.tolist()
        

    def plot_histogram(self,dataContent:pd.DataFrame,columns:Optional[List[str]]=None):
        """
        绘制直方图
        """
        if not columns:
            columns=self.num_cols
        # 没有数据后尝试将自身的数据列给到columns,此时如果仍没有数据，说明无法画成图  
        if not columns:
            print('no available columns to plot into histogram')
            return 
        
        plt.figure(figsize=(15,10))
        for i, col in enumerate(columns, 1):
            plt.subplot(len(columns)//2 + 1, 2, i)
            sns.histplot(data=dataContent, x=col, kde=True)
            plt.title(f'{col}的分布')

        plt.tight_layout()
        save_path = f"{self.output_dir}/数值列分布直方图.png"
        plt.savefig(save_path, dpi=300)
        plt.close()
        print(f"have been saved to {save_path}")
    
    def plot_boxgram(self,dataContent:pd.DataFrame,columns:Optional[list[str]]=None):
        """
        绘制箱线图
        """
        if not columns:
            columns=self.num_cols

        if not columns:
            print('no available columns to plot into box figure')
            return
        
        plt.figure(figsize=(12, 6))
        sns.boxplot(data=dataContent[columns])
        plt.xticks(rotation=45)
        plt.title('数值列箱线图（异常值检测）')
        
        plt.tight_layout()
        save_path = f"{self.output_dir}/数值列箱线图.png"
        plt.savefig(save_path, dpi=300)
        plt.close()
        print(f"have been saved to  {save_path}")

    def plot_correlation_heatmap(self,dataContent:pd.DataFrame,columns:Optional[list[str]]=None):
        """
        绘制相关性热图
        """
        if not columns:
            columns=self.num_cols
        
        if len(columns)<2:#至少两列才能画成相关性热图
            print('Error,only no less than two columns of data can be ploted into correlation_heatmap')
            return
        
        plt.figure(figsize=(10, 8))
        corr = dataContent[columns].corr()
        sns.heatmap(corr, annot=True, cmap='coolwarm', fmt='.2f', linewidths=0.5)
        plt.title('数值列相关性热图')
        
        plt.tight_layout()
        save_path = f"{self.output_dir}/相关性热图.png"
        plt.savefig(save_path, dpi=300)
        plt.close()
        print(f"have been saved to {save_path}")


    
    def plot_category_distributions(self, dataContent: pd.DataFrame, max_categories: int = 10):
        """
        绘制类别分布柱状图
        """
        if not self.notNum_cols:
            print("no available columns")
            return
        
        for col in self.cat_cols:
            # 只绘制类别数量较少的列
            if dataContent[col].nunique() <= max_categories:
                plt.figure(figsize=(8, 5))
                sns.countplot(data=dataContent, x=col)
                plt.xticks(rotation=45)
                plt.title(f'{col}的类别分布')
                
                plt.tight_layout()
                save_path = f"{self.output_dir}/{col}_类别分布.png"
                plt.savefig(save_path, dpi=300)
                plt.close()
                print(f"the {col} category figurehave been saved to {save_path}")

    
    def plot_scatter(self, df: pd.DataFrame, x_col: str = None, y_col: str = None):
        """
        绘制散点图
        """
        if len(self.num_cols) < 2:
            print("Error,only no less than two columns of data can be ploted ito scatter figure")
            return
        
        # 默认使用前两列
        if not x_col:
            x_col = self.num_cols[0]
        if not y_col:
            y_col = self.num_cols[1]
        
        plt.figure(figsize=(8, 6))
        sns.scatterplot(data=df, x=x_col, y=y_col, alpha=0.7)
        plt.title(f'{x_col}与{y_col}的散点图')
        
        plt.tight_layout()
        save_path = f"{x_col}_vs_{y_col}_散点图.png"
        save_path=self.save_path_check(save_path)
        save_path=self.output_dir+'/'+save_path
        plt.savefig(save_path, dpi=300)
        plt.close()
        print(f"have been saved to  {save_path}")
    

    def generate_all_figures(self,dataContent:pd.DataFrame):
        """
        绘制所有图片
        """
        self.prepare_columns(dataContent)
        self.plot_histogram(dataContent)
        self.plot_boxgram(dataContent)
        self.plot_correlation_heatmap(dataContent)
        self.plot_category_distributions(dataContent)
        self.plot_scatter(dataContent)




