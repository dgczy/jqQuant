# -*- coding: utf-8 -*-


"""
功能：
    数据读写引擎
版本：
    v 0.1
说明：
    量化研究数据的标准、通用读写
    研究、策略中通用
    分为sqlite数据库版和cvs文件版
    两个版本的读写方法及参数、返回数据完全一致
"""

import os

#环境检测包
from tl import IN_BACKTEST

# 判断运行环境
if IN_BACKTEST:
     # 策略环境
    # 策略中必须导入kuanke.user_space_api包，用于支持read_file,write_file
    from kuanke.user_space_api import read_file,write_file
    print('数据引擎：运行于策略')    
else:
    # 研究环境
    print("数据引擎：运行于研究")

    
# 基本包
import numpy as np
import pandas as pd

# 系统、数据流包
import io
import six
from six import StringIO,BytesIO

# 数据持久化包
import pickle

# 数据库包
from sqlalchemy import create_engine


    
class Sqlite(object):
    """
    功能：数据库读写（sqlite）
    name：数据库名，str，如：‘idx_db’
    path：数据库路径，str，如：'data/'、‘../data/’
    """
    def __init__(self,name,path):
        self.__in_research=not IN_BACKTEST
        self.__name=name
        self.__path=path
        self.__connect=self.__connection()
                     
    def __connection(self):
        """
        功能：连接数据库
        参数：无
        返回：数据库链接
        """
        if self.__in_research:
            # 研究中，直接连接数据库
            connect=create_engine('sqlite:///%s%s.db'%(self.__path,self.__name))
        else:
            # 策略中，生成一个副本数据库到策略的默认目录，生成副本数据库的连接
            # 数据库文件
            data_file='%s%s.db'%(self.__path,self.__name)
            # 读取数据库到内存
            data=read_file(data_file)
            # 副本文件
            temp_file='%s_temp.db'%(self.__name)
            # 写内存数据到策略默认目录中
            with open(temp_file,'wb') as f:
                f.write(data)
            # 生成数据库副本连接        
            connect=create_engine('sqlite:///%s'%temp_file)
        return connect
   
    
    def restore(self):  
        """
        功能：策略中，策略结束前恢复数据库
        参数：无
        返回：无
        """
        # 数据库文件
        data_file='%s%s.db'%(self.__path,self.__name)
        # 副本数据库文件
        temp_file='%s_temp.db'%(self.__name)
        # 读取副本数据库到内存
        with open(temp_file,'rb') as f:
            data=f.read()
        # 覆盖研究中的原数据库        
        write_file(data_file,data,append=False) 
         
            
    def read(self,name,cols=None,parse_dates=False,encoding=None):
        """
        功能：读取数据
        name：表名，str，如：‘idx_000300’
        cols：字段名，list，如：[‘close’,'open']
        parse_dates：是否解析日期，bool
        encoding：编码格式，str
        返回：数据表，dataframe
        """
        # 修正parse_dates
        parse_dates=['index'] if parse_dates else None
        # 从数据库中读取表，并重置索引
        df=pd.read_sql(name,self.__connect,columns=cols,index_col='index',parse_dates=parse_dates) 
        df.index.name=None 
        # 返回数据        
        return df   
    
    def save(self,name,df,append=True,encoding=None):
        """
        功能：保存数据到表、默认为追加模式
        name：表名，str
        df：数据表，dataframe
        append：追加、替换模式，bool
        encoding：编码格式，str
        返回：无
        """
        # 追加或替换
        exists='append' if append else 'replace'
        # code转换为表名，追加数据
        df.to_sql(name,self.__connect,if_exists=exists)       
        
        
    def append(self,name,df):
        """
        功能：追加数据到表
        name：表名，str
        df：数据表，dataframe
        """
        # 追加数据
        self.save(name,df,True)
 

    def replace(self,name,df):
        """
        功能：替换数据表
        name：表名，str
        df：数据表，dataframe
        """
        # 替换数据
        self.save(name,df,False)   
                

class _Cvs_Backtest(object):  
    """
    功能：CSV文件操作（策略环境 ） 
    说明：策略中必须用read_file、write_file读写研究文件
    path：文件路径，str
    """    
    # 构造行数
    def __init__(self,path=''):
        # 文件路径
        self.__path=path

        
    def read(self,name,cols=None,parse_dates=False,encoding=None):
        """
        功能：读取数据库表
        name：表名，str，如：‘idx_000300’
        cols：字段名，list，如：[‘close’,'open']
        parse_dates：是否解析日期，bool
        encoding：编码格式，str
        返回：数据表，dataframe
        """
        # 使用cols时，默认不包括index列，所以必须加上index列
        cols=None if cols is None else [0]+cols
        # 策略中必须使用StringIO+read_file方法
        df=pd.read_csv(StringIO(read_file('%s%s.csv'%(self.__path,name))),
                       usecols=cols,index_col=0,parse_dates=parse_dates,encoding=encoding)
        # 返回数据表
        return df   

    
    def save(self,name,df,append=True,encoding=None):  
        """
        功能：保存数据到表、默认为追加模式
        name：表名，str
        df：数据表，dataframe
        append：追加、替换模式，bool
        encoding：编码格式，str
        返回：无
        """
        # 修正追加或替换模式
        mode='a' if append else 'w'
        # 追加模式下不追加数据表头，替换模式使用数据表头
        header=False if append else True
        # 策略中必须使用write_file方法
        write_file('%s%s.csv'%(self.__path,name),
                    df.to_csv(mode=mode,header=header,encoding=encoding),append=append)  



class _Cvs_Research(object):  
    """
    功能：CSV文件读写（研究环境 ）  
    path：文件路径，str
    """       
    # 构造行数
    def __init__(self,path=''):
        # 文件路径
        self.__path=path
   

    def read(self,name,cols=None,parse_dates=False,encoding=None):
        """
        功能：从csv文件读取数据
        name：表名，str，如：‘idx_000300’
        cols：字段名，list，如：[‘close’,'open']
        parse_dates：是否解析日期，bool
        encoding：编码格式，str
        返回：数据表，dataframe
        """
        # 使用cols时，默认不包括index列，所以必须加上index列
        cols=None if cols is None else [0]+cols
        # 读取cvs文件
        df=pd.read_csv('%s%s.csv'%(self.__path,name),
                       usecols=cols,index_col=0,parse_dates=parse_dates,encoding=encoding)
        # 返回数据表
        return df   

    
    def save(self,name,df,append=True,encoding=None):  
        """
        功能：保存数据到csv文件
        name：表名，str
        df：数据表，dataframe
        append：追加、替换模式，bool
        encoding：编码格式，str
        返回：无
        """
        # 修正追加或替换模式
        mode='a' if append else 'w'
        # 追加模式下不追加数据表头，替换模式使用数据表头
        header=False if append else True
        # 保存结果
        df.to_csv('%s%s.csv'%(self.__path,name),mode=mode,header=header,encoding=encoding) 

    
    
class _Pickle_Backtest(object):  
    """
    功能：Pickle读写（策略环境 ）  
    说明：策略中必须用read_file、write_file读写研究文件
    path：文件路径，str
    """       
    # 构造行数
    def __init__(self,path=''):
        self.__path=path

        
    def read(self,name):
        """
        功能：读取pickle
        name：文件名，str
        返回：数据
        """
        data=pickle.load(StringIO(read_file('%s%s.pkl'%(self.__path,name))))
        return data 

    
    def save(self,name,data):
        """
        功能：写入pickle
        name：文件名，str
        data：数据
        返回：无
        """
        write_file('%s%s.pkl'%(self.__path,name),pickle.dumps(data),append=False)
     
         
class _Pickle_Research(object):  
    """
    功能：Pickle读写（研究环境 ）  
    path：文件路径，str
    """     
    # 构造行数
    def __init__(self,path=''):
        # 文件路径
        self.__path=path

        
    def read(self,name):
        """
        功能：读取pickle
        name：文件名，str
        返回：数据
        """
        with open('%s%s.pkl'%(self.__path,name),'r') as pick_file:
            data=pickle.load(pick_file)
        return data 

    
    def save(self,name,data):
        """
        功能：写入pickle
        name：文件名，str
        data：数据
        返回：无
        """
        with open('%s%s.pkl'%(self.__path,name),'w') as pick_file:
            # 第三个参数必须为0
            pickle.dump(data,pick_file,0)

            
class Image_Research(object): 
    """
    功能：图表保存为图像（研究环境 ）  
    path：文件路径，str
    """   
    def __init__(self,path=''):
        # 文件路径
        self.__path=path
        
    def save(self,fig,file_name,file_type='png'): 
        """
        功能：图表保存为图像
        fig：图表画板对象
        file_name：文件名，str
        file_type：图像类型，即扩展名
        返回：无
        """  
        # 文件全名
        file_name=self.__path+file_name+'.'+file_type
        # 使用画板对象的savefig方法生成图表为图像
        # 参数bbox_inches='tight'、,pad_inches=0必须，否则生成的图像有边框
        fig.savefig(file_name,dpi=fig.dpi,bbox_inches='tight',pad_inches=0) 

        
class Image_Backtest(object): 
    """
    功能：图表保存为图像（策略环境 ）  
    path：文件路径，str
    """  
    def __init__(self,path=''):
        # 文件路径
        self.__path=path
        
    def save(self,fig,file_name,file_type='png'):   
        """
        功能：图表保存为图像
        fig：图表画板对象
        file_name：文件名，str
        file_type：图像类型，即扩展名
        返回：无
        """  
        # 文件名
        file_name=file_name+'.'+file_type
        # 先保存到策略目录下，作为临时文件
        fig.savefig(file_name,dpi=fig.dpi,bbox_inches='tight',pad_inches=0) 
        # 读取临时文件
        with open(file_name,'rb') as fp:
            data=fp.read()
        # 保存到研究中
        write_file(self.__path+file_name,data,append=False) 
        # 删除临时文件
        os.remove(file_name)


        
# 根据运行环境初始化Cvs、Pickle、Image            
Csv=_Cvs_Backtest if IN_BACKTEST else _Cvs_Research
Pickle=_Pickle_Backtest if IN_BACKTEST else _Pickle_Research        
Image=Image_Backtest if IN_BACKTEST else Image_Research  
