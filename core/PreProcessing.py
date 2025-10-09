import pandas as pd
import numpy as np
import os

def load_data(file):
    """
    导入数据,支持CSV,Excel等
    file:传入的文件
    返回导入的数据内容
    """
    if isinstance(file,str):
        # if not os.path.exist(file):
        #     raise FileExistsError(f"文件路径不存在：{file}")
        # elif not os.path.isfile(file):
        #     raise ValueError(f"指定路径不是文件：{file}")
        
        if file.name.endswith(".csv"):
            file_type="csv"
        elif file.name.endwith('.xlsx'):
            file_type="xlsx"
        else:
            raise ValueError("仅支持CSV,EXCEL文件")
        if file_type == "csv":
            return pd.read_csv(file)
        elif file_type == "xlsx":
            return pd.read_excel(file)
        else:
            raise ValueError("文件读取失败")




def clean_data(dataContent):
    """
    数据清洗，返回清洗后的数据
    
    """
    # 空输入报错并返回
    if dataContent is None:
        print('Error,empty data content')
        return None
    cloned=dataContent.copy()

    same_count=cloned.duplicated().sum()
    
    if same_count > 0:
        cloned=cloned.drop_duplicates()
        print(f'the number of  repeated and dropped value is:{same_count}')

    for col in cloned.columns:
        #转换字符串为日期
        if cloned[col].dtype=='object':
            try:
                cloned[col]=pd.to_datetime(cloned[col])
                print(f'column {col} has been converted into data type')
            except:
                continue
        # 打印缺失信息
        missing=cloned.isnull().sum()
        missing=missing[missing>0]
        if not missing.empty:
            print('\n missing data:')
            print(missing)

        # 分离出数值数据信息和非数值信息
        num_data=cloned.select_dtypes(include=['number']).columns
        not_num_data=cloned.select_dtypes(exclude=['number']).columns

        # 数值信息用均值填充
        for col in num_data:
            if cloned[col].isnull().sum()>0:
                cloned[col]=cloned[col].fillna(cloned[col].mean())
                print(f'column {col} has been filled with average value')
        
        # 非数值信息用众数填充
        for col in not_num_data:
            if cloned[col].isnull().sum()>0:
                mode_val=cloned[col].mode()[0]
                cloned[col]=cloned[col].fillna(mode_val)
                print(f'column {col} has been filled with mode')

        # 去除无用列（全空、全单一值）
        drop_col=[]
        for col in cloned.columns:
            if cloned[col].isnull().all():
                drop_col.append(col)
                print(f'column {col} is Nan,which will be dropped')
            elif cloned[col].nunique()==1:
                drop_col.append(col)
                print(f'column {col} is single-value column,which will be dropped')
            
        if drop_col:
            cloned=cloned.drop(columns=drop_col)
            print(f'totally remove useless columns:{drop_col}')
        
        print('\n data wash finish')
        return cloned





if __name__=='main':
    pass








    



        


