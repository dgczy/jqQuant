# -*- coding: utf-8 -*-

"""

宏观指标

研究、策略通用
SQLIte数据库和CVS文件通用

作者：DGC'Idea
版本：V0.31  
更新日期：2018年6月3日

"""


# 导入包、配置

#基本包
import numpy as np
import pandas as pd
import math

#时间包
import time
from datetime import timedelta,date,datetime


#导入自定义包
from tl import IN_BACKTEST
from pf import *
from ds import dsMcr

#必须依照以下顺序导入、设置matplotlib
import matplotlib

if IN_BACKTEST:
    #策略中绘图必须使用Agg模式（即不显示图形）
    matplotlib.use('Agg') 
    print '宏观框架：运行于策略'
else:
    print '宏观框架：运行于研究'
    
import matplotlib.pyplot as plt

# 标识符
_ID='mcr'
_NOTE='宏观'


class Fields(TField):
    pass
    

class _Pool(TPool):
    
    # 构造函数
    # dm：数据引擎
    def __init__(self,project):
        TPool.__init__(self,project)  

    
class _Data(Tdata):
    """
    Data类：数据获取、计算
    """
    def __init__(self,project,pool):
        Tdata.__init__(self,project,pool)      
    
    def get_data(self,code,start_date=None,end_date=None):
        df=dsMcr.hist(code,start_date)
        if code in ['C10Y']:
            #计算市盈率
            df['pe']=np.round(1/df['close']*100,2)
        return df 


class _Chart(Tchart):
    """
    图表
    """  
    def __init__(self,project,pool,data,analyse):
        Tchart.__init__(self,project,pool,data,analyse)


class Mcr(object):
    """
    宏观指标 
    name：'cvs'表示使用文件引擎，其它表示数据库文件名,使用数据库引擎
    path：数据库路径或文件路径 
    pool：指数标的名称
    analyse：分析表名称
    """
    # 构造函数
    def __init__(self,data_name,data_path,project_name=None,project_id=_ID,project_note=_NOTE):
        self.project=TProject(data_name,data_path,project_name,project_id,project_note)
        # 组合其它类  
        self.pool=_Pool(self.project)
        self.data=_Data(self.project,self.pool)
        
        self.chart=_Chart(self.project,self.pool,self.data,None)
        
        
