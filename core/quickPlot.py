#快速绘制2d图像
import matplotlib.pyplot as plt
import numpy as np
import os
import re
def savePlot(fig,title,savePath=None,saveFormat='png'):
    """
    save the picture as .png in savePath
    """
    if not savePath:
        current_dir=os.path.dirname(os.path.abspath(__file__))
        clearTitle=re.sub(r'[\\/*?:"<>|]','_',title)
        savePath=os.path.join(current_dir,f"{clearTitle}.{saveFormat}")
        fig.savefig(savePath)

def pointLineChart(x,y,xlabel='x',ylabel='y',title='pointLineChart',color='blue',showgrid=True,save=True,saveFormat='png'):
    """
    绘制基于横坐标x,纵坐标y的折线图
    x:横坐标
    y:纵坐标
    xlabel:x轴名称
    ylabel:y轴名称
    title:标题名称
    color:颜色
    showgrid:是否展示网格
    save:是否保存图片
    saveFormat:保存格式
    """
    fig,ax=plt.subplots(figsize=(10,6))
    ax.plot(x,y)
    ax.set_xlabel(xlabel)
    ax.set_ylabel(ylabel)
    ax.set_title(title)
    ax.grid(showgrid)
    if save:
        savePlot(fig,title,None,saveFormat)
    
    plt.show()
    
def scatterChart(x,y,xlabel='x',ylabel='y',title='scatter',color='blue',showgrid=True,save=True,saveFormat='png'):
    """
    基于x,y绘制散点图
    x:横坐标
    y:纵坐标
    xlabel:x轴的名称
    ylabel:y轴的名称
    title:图像标题
    color:点的颜色
    showgrid:是否展示网格线
    save:是否保存
    saveFormat:保存的格式
    """
    fig,ax=plt.subplots(figsize=(10,6))
    ax.scatter(x,y)
    ax.set_xlabel(xlabel)
    ax.set_ylabel(ylabel)
    ax.set_title(title)
    ax.grid(showgrid)
    if save:
        savePlot(fig,title,None,saveFormat)

    plt.show()




def lineChart(xrange,expression,xlabel='x',ylabel='y',title='lineChart',color='blue',showgrid=True,save=True,saveFormat='png'):
    x=np.array(xrange)
    y=expression(x)
    picture=plt.figure(figsize=(10,6))
    plt.plot(x,y,color=color,marker='+')
    plt.xlabel(xlabel)
    plt.ylabel(ylabel)
    plt.title(title)
    if showgrid:
        plt.grid(True)
    else:
        plt.grid(False)
    plt.tight_layout()
    if save:
        savePlot(picture,title,None,saveFormat)
    plt.show()

def barChart(xrange, yvalue, xlabel='x', ylabel='y', title='barChart',
             colors=None, labels=None, showGrid=True, save=True,
             saveFormat='png', legendLoc='best'):
    """
    绘制带自动图例的柱状图
    xrange: 对应类别位置
    yvalue: 对应数值
    colors: 柱子颜色，可为单一颜色或列表
    labels: 类别标签，用于 x 轴和图例
    showGrid: 是否显示网格
    save: 是否保存图片
    saveFormat: 保存图片格式，如 'png', 'pdf'
    legendLoc: 图例位置
    """
    fig, ax = plt.subplots(figsize=(10, 6))

    # 绘制柱状图
    bars = ax.bar(xrange, yvalue, color=colors)

    # 设置坐标轴和标题
    ax.set_xlabel(xlabel)
    ax.set_ylabel(ylabel)
    ax.set_title(title)

    # 如果提供 labels，则用作 x 轴刻度和图例; 否则生成默认标签
    if labels:
        ax.set_xticks(xrange)
        ax.set_xticklabels(labels)
        legend_labels = labels
    else:
        legend_labels = [f'Bar {i+1}' for i in range(len(xrange))]

    # 在每个柱子上显示数值
    max_val = np.max(yvalue) if len(yvalue)>0 else 0
    for bar, value in zip(bars, yvalue):
        height = bar.get_height()
        ax.text(
            bar.get_x() + bar.get_width() / 2.,
            height + max_val * 0.01,
            f'{value}',
            ha='center', va='bottom', fontsize=10
        )

    # 显示网格
    if showGrid:
        ax.grid(True, axis='y', linestyle='--', alpha=0.7)

    # 添加自动生成的图例
    ax.legend(bars, legend_labels, loc=legendLoc)

    plt.tight_layout()

    # 保存图片
    if save:
        savePlot(fig, title, None, saveFormat)

    plt.show()
    return fig

def pieChart(values,labels=None,title='pieChart',colors=None,autopct='%1.1f%%',startangle=90,legendTitle=None,save=True,saveFormat='png'):
    """
    绘制带图例饼图
    values:数值列表
    labels:标签列表
    title:饼图标题
    colors:各部分颜色
    autopct:百分比格式
    startangle:起始角度
    saveFormat:保存格式
    """
    fig,ax=plt.subplots(figsize=(8,8))
    wedges,texts,autotexts=ax.pie(values,labels=None,colors=colors,autopct=autopct,startangle=startangle)
    ax.set_title(title)
    if labels:
        legend_labels = labels
    else:
        legend_labels = [f'Slice {i+1}' for i in range(len(values))]
    ax.legend(wedges, legend_labels,  loc='best',title=legendTitle)
    plt.tight_layout()
    if save:
        savePlot(fig,title,None,saveFormat)
    plt.show()

def boxPlot(data,labels=None,title='boxPlot',xlabel='x',ylabel='y',showGrid=True,save=True,saveFormat='png',legendLoc='best',legendTitle=None):
    """
    绘制箱图
    data:列表或二维数组，每一列为一组数据
    labels:每组数据对应的标签
    title:箱图标题
    xlabel,ylabel:x,y坐标标签
    showGrid:是否显示网格
    save:是否保存
    saveFormat:保存格式
    legendLoc:图例位置
    legendTitle:图例名称
    """
    fig,ax=plt.subplots(figsize=(10,6))
    box=ax.boxplot(data,labels=None,patch_artist=True)
    ax.set_title(title)
    ax.set_xlabel(xlabel)
    ax.set_ylabel(ylabel)

    colors_cycle = plt.rcParams['axes.prop_cycle'].by_key()['color']
    if isinstance(data, (list, tuple)) and box['boxes']:
        for patch, color in zip(box['boxes'], colors_cycle):
            patch.set_facecolor(color)
    if labels:
        ax.set_xticklabels(labels)
        legend_labels=labels
    else:
        legend_labels=[f'Group{i+1}' for i in range(len(data))]

    from matplotlib.lines import Line2D
    legend_handles = []
    for i, lbl in enumerate(legend_labels):
        facecolor = box['boxes'][i].get_facecolor()
        legend_handles.append(Line2D([0], [0], color=facecolor, lw=10))
    ax.legend(legend_handles, legend_labels, loc=legendLoc, title=legendTitle)
    
    if showGrid:
        ax.grid(True,axis='y',linestyle='--',alpha=0.7)
    plt.tight_layout()
    if save:
        savePlot(fig,title,None,saveFormat)
    plt.show()    

    
    
    
    