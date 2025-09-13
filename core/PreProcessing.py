import pandas as pd
import numpy as np


def load_data(file_path,file_format=None):
    """
    导入数据,支持CSV,Excel等
    file_path:文件路径
    file_format:文件格式,默认空
    返回导入的数据内容
    """
    try:
        if file_format is None:
            if file_path.endswith('.csv'):
                file_format='csv'
            elif file_path.endswith(('.xlsx','.xls')):
                file_format='excel'
            else:
                raise ValueError('can not recognize file format,please check your file')
            
            # 根据格式读取
            if file_format=='csv':
                dataContent=pd.read_csv(file_path)
            elif file_format=='excel':
                dataContent=pd.read_excel(file_path)
            else:
                raise('do not support file format:{file_format}')
  
            print(f'succeed load data,totally {dataContent.shape[0]} rows,{dataContent.shape[1]} columns')
            return dataContent
    except FileNotFoundError:
        print(f'Can not find file:{file_path}')
        return None
    except Exception as e:
        print(f'error happened when loading data:{str(e)}')
        return None


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








    



        


