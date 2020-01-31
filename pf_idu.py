# -*- coding: utf-8 -*-

"""

指数估值计算、分析

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

import requests

#聚源包（获取派息数据）
from jqdata import get_industries

#导入自定义包
# 工具
from tl import IN_BACKTEST,get_volatility,get_annualized
# 框架
from pf import *
# 数据源
from ds import dsIdu

#必须依照以下顺序导入、设置matplotlib
import matplotlib

if IN_BACKTEST:
    #策略中绘图必须使用Agg模式（即不显示图形）
    matplotlib.use('Agg') 
    print '行业框架：运行于策略'
else:
    print '行业框架：运行于研究'
    
import matplotlib.pyplot as plt

# 标识符
_ID='idu'
_NOTE='行业'
  
            
            
#--------------------------------------------------------------------------------------   
# Fields类，字段、名称对照

class Fields(TField):
    pass
    
    
#-------------------------------------------------------------------------------------- 
# Codes类，指数标的

class _Pool(TPool):
    
    # 构造函数
    # dm：数据引擎
    def __init__(self,project):
        TPool.__init__(self,project)  
    
 
    # 生成标的
    def create(self):
        df=get_industries(name='%s_l%s'%(self.project.name[:2],self.project.name[-1])) 
        #生成列表
        self.to_track(df)
        # 调用父类方法保存:
        TPool.save(self,df)
        
    def show(self):
        df=TPool.show(self)
        df=df.rename(columns={'name':'行业名称','start_date':'成立日期'})
        return df


#-------------------------------------------------------------------------------------- 
# Data类：指数数据获取、计算
       
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
        return dsIdu.hist(code=code,start_date=start_date,end_date=end_date)
    
    def to_name(self,code):  
        """
        获得文件名或数据库表名，子类可重新实现
        code：代码，str
        """
        return '%s_%s'%(self.project.id,code) if self.project.name is None else '%s_%s_%s'%(self.project.id,self.project.name,code) 


    
# --------------------------------------------------------------------------------------
# Analyse类，估值分析

class _Value(Tvalue):
    """
    估值分析：PE-TTM（滚动市盈率）、PB（平均市净率）；
    财务指标分析：ROE（年报、扣非后净资产收益率）、波动率、回报率、股息率。
    """   
        
    def __init__(self,project,pool,data):
        Tvalue.__init__(self,project,pool,data) 

        
    def get_found_date(self,code):
        """
        获取指数发布日期    
        code：指数代码
        """
        return dsIdu.info(code).start_date   
    
    
    def __get_stock_count(self,code,end_date):
        """
        获取成份股数
        code：指数代码
        end_date：截至日期
        """
        return len(dsIdu.stocks(code))
  
    
    def standard_cols(self):
        """
        标准分析字段
        """
        return ['pe','pb','dyr','roe']
    
    def extend_analysis(self,code,df):
        """
        扩展分析
        """
        #波动率
        vlt=get_volatility(df[['close']])
        # 回报率
        roi=get_annualized(df[['close']])
        #成份股数
        stocks=self.__get_stock_count(code,df.index[-1].date())
        return vlt,roi,stocks 

    def extend_columns(self):
        """
        扩展分析标题
        """
        return ['vlt','roi','stocks']
        
        
# --------------------------------------------------------------------------------------
# Change类，行情分析

class _Change(Tchange):
    """
    行情分析
    """   
    def __init__(self,project,pool,data):
        Tchange.__init__(self,project,pool,data) 
        
        
    def get_found_date(self,code):
        """
        获取指数发布日期    
        code：指数代码
        """
        return dsIdu.info(code).start_date
        
 
    
    
#--------------------------------------------------------------------------------------
# Chart类，生成图表

class _Chart(Tchart):

    def __init__(self,project,pool,data,analyse):
        Tchart.__init__(self,project,pool,data,analyse)

  
    
#--------------------------------------------------------------------------------------
# Table类，查询估值表
class _Table(Ttable):

        
    def __init__(self,project,pool,data,analyse):
        Ttable.__init__(self,project,pool,data,analyse)
 
    def integrate_columns(self,mode):
        return {
            'name':'名称',
            'pe'+mode:'PE','pe'+mode+'_ratio':'高度(%)','pe'+mode+'_state':'区间',
            'pb'+mode:'PB','pb'+mode+'_ratio':'高度(%)','pb'+mode+'_state':'区间',
            'roe':'ROE','dyr':'股息率(%)','vlt':'波动率','roi':'收益率(%)',
            'start':'数据起点','sample':'样本数','stocks':'成份股数'}
    
    
    def integrate_cols(self,mode):
        return [
            'name',
            'pe'+mode,'pe'+mode+'_ratio','pe'+mode+'_state',
            'pb'+mode,'pb'+mode+'_ratio','pb'+mode+'_state',
            'roe','dyr','vlt','roi',
            'start','sample','stocks'
            ]   

    

class Industry(object):
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
        
        
    def set_chance(chance,danger):
        self.value.chance=chance
        self.value.danger=danger

        
