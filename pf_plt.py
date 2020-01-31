# -*- coding: utf-8 -*-

"""

板块

研究、策略通用
SQLIte数据库和CVS文件通用

作者：DGC'Idea
版本：V0.31  
更新日期：2018年6月3日

"""


#--------------------------------------------------------------------------------------   
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
from ds import dsPlt

#必须依照以下顺序导入、设置matplotlib
import matplotlib

if IN_BACKTEST:
    #策略中绘图必须使用Agg模式（即不显示图形）
    matplotlib.use('Agg') 
    print '板块框架：运行于策略'
else:
    print '板块框架：运行于研究'
    
import matplotlib.pyplot as plt

# 标识符
_ID='plt'
_NOTE='板块'
  
            

class Fields(TField):
    """
    Fields类，字段、名称对照
    """
    value=['pe','pb','dyr']

    
    
class _Pool(TPool):
    """
    标的
    """
    
    # 构造函数
    # dm：数据引擎
    def __init__(self,project):
        TPool.__init__(self,project)  
         


class _Data(Tdata):
    """
    Data类：指数数据获取、计算
    沪深指数：聚宽数据，日线数据，包括行情、估值；
    港指：恒生官网数据，月线数据，包括行情、pe、股息率
    美指：标普500，http://www.multpl.com网站数据，月线数据
    """
    def __init__(self,project,pool):
        Tdata.__init__(self,project,pool)  
   
    def get_data(self,code,start_date=None,end_date=None):
        return dsPlt.hist(code=code,start_date=start_date,end_date=end_date)
    


class _Value(Tvalue):
    """
    估值分析：PE-TTM（滚动市盈率）、PB（平均市净率）；
    财务指标分析：ROE（年报、扣非后净资产收益率）、波动率、回报率、股息率。
    """   
        
    def __init__(self,project,pool,data):
        Tvalue.__init__(self,project,pool,data) 

    
    def standard_cols(self):
        """
        标准分析字段
        """
        return Fields.value
    

    
class _Change(Tchange):
    """
    行情分析
    """   
    def __init__(self,project,pool,data):
        Tchange.__init__(self,project,pool,data) 
        
        

class _Chart(Tchart):
    """
    Chart类，生成图表
    """

    def __init__(self,project,pool,data,analyse):
        Tchart.__init__(self,project,pool,data,analyse)

    def pe(self,years=10,period='W',quantile=True):
        for code in self.pool.track:
            fig=self.line_one(code,'pe','',years,'',period,quantile)

    def pb(self,years=10,period='W',quantile=True):
        for code in self.pool.track:
            fig=self.line_one(code,'pb','',years,'',period,quantile)
            

    def dyr(self,years=10,period='W',quantile=True):
        for code in self.pool.track:
            fig=self.line_one(code,'dyr','',years,'',period,quantile)
            
            

class _Table(Ttable):
    """
    Table类，查询估值表
    """
    def __init__(self,project,pool,data,analyse):
        Ttable.__init__(self,project,pool,data,analyse)
           
    # 对外接口
    def pe(self,sort='ratio',asc=True,years=10):
        return self.value(self.pool.track,'pe','',sort,asc,years)
    
    def pb(self,sort='ratio',asc=True,years=10):
        return self.value(self.pool.track,'pb','',sort,asc,years)
    
    def dyr(self,sort='ratio',asc=True,years=10):
        return self.value(self.pool.track,'dyr','',sort,asc,years)
    

    
class Plt(object):
    """
    指数估值计算、分析 
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
        
        self.change=_Change(self.project,self.pool,self.data)
        self.value=_Value(self.project,self.pool,self.data)
        
        self.change.chart=_Chart(self.project,self.pool,self.data,self.change)
        self.value.chart=_Chart(self.project,self.pool,self.data,self.value)
        self.change.table=_Table(self.project,self.pool,self.data,self.change)
        self.value.table=_Table(self.project,self.pool,self.data,self.value)
        
        
