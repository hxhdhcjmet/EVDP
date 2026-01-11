import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import os
import seaborn as sns
from typing import Optional,List
from matplotlib import font_manager
import re
import platform


def apply_global_style(prefer: str = "auto") -> None:
    """CHANGED v2.1
    Apply unified matplotlib/seaborn styles with Chinese font support.

    Args:
        prefer: Font family preference. "auto" detects OS and picks
            SimHei on Windows, PingFang SC on macOS, DejaVu Sans on others.
    """
    system = platform.system()
    candidates = [
        "SimHei",
        "PingFang SC",
        "Noto Sans CJK SC",
        "Source Han Sans SC",
        "DejaVu Sans",
    ]
    if prefer != "auto":
        candidates = [prefer] + candidates
    # pick first available font from candidates
    available = {f.name for f in font_manager.fontManager.ttflist}
    font_family = None
    for name in candidates:
        if name in available:
            font_family = name
            break
    if font_family is None:
        font_family = "DejaVu Sans"

    plt.rcParams["font.family"] = [font_family]
    plt.rcParams["font.serif"] = [font_family]
    plt.rcParams["font.sans-serif"] = [font_family]
    plt.rcParams['axes.unicode_minus'] = False
    plt.rcParams['axes.titlesize'] = 14
    plt.rcParams['axes.labelsize'] = 12
    plt.rcParams['legend.fontsize'] = 10
    sns.set_theme(font_scale=1.0)
    sns.set_style('whitegrid')

def wrap_text(text: str, max_chars: int = 15) -> str:
    """CHANGED v2.1
    Wrap long text with newline every max_chars.

    Args:
        text: Input string
        max_chars: Maximum characters per line

    Returns:
        Wrapped string suitable for legend/tick labels.
    """
    if not isinstance(text, str):
        return str(text)
    lines = [text[i:i+max_chars] for i in range(0, len(text), max_chars)]
    return "\n".join(lines)

def apply_legend_style(ax, max_width_ratio: float = 0.4, loc: str = "best") -> None:
    """CHANGED v2.1
    Apply legend styling with elastic layout.

    Args:
        ax: Matplotlib Axes
        max_width_ratio: Maximum legend width relative to figure width
        loc: Legend location
    """
    leg = ax.legend(loc=loc, frameon=True, fancybox=True)
    if leg is not None:
        leg.set_frame_alpha(0.8)
        leg._legend_box.align = "left"
        try:
            fig = ax.figure
            bbox = leg.get_window_extent(fig.canvas.get_renderer())
            fig_w = fig.get_figwidth()
            # approximate width control by setting ncol when too wide
            if bbox.width / fig_w > max_width_ratio:
                leg._ncols = 2
        except Exception:
            pass

def responsive_tight_layout(fig) -> None:
    """CHANGED v2.1
    Ensure layout is tight and responsive across screen sizes.

    Args:
        fig: Matplotlib Figure
    """
    fig.tight_layout()

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
            plt.title(f'{col} Distribution')

        plt.tight_layout()
        save_path = f"{self.output_dir}/numerical_columns_histogram.png"
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
        plt.title('Numerical Columns Boxplot (Outlier Detection)')
        
        plt.tight_layout()
        save_path = f"{self.output_dir}/numerical_columns_boxplot.png"
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
        plt.title('Numerical Columns Correlation Heatmap')
        
        plt.tight_layout()
        save_path = f"{self.output_dir}/correlation_heatmap.png"
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
                plt.title(f'{col} Category Distribution')
                
                plt.tight_layout()
                save_path = f"{self.output_dir}/{col}_category_distribution.png"
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
        plt.title(f'{x_col} vs {y_col} Scatter Plot')
        
        plt.tight_layout()
        save_path = f"{x_col}_vs_{y_col}_scatter.png"
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




