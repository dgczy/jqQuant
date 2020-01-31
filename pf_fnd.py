# -*- coding: utf-8 -*-

"""

基金行情计算分析

研究、策略通用
SQLIte数据库和CVS文件通用

作者：DGC'Idea
版本：V0.31  
更新日期：2018年6月3日

"""


# 基本包
import numpy as np
import pandas as pd
import math

# 日期时间
import time 
from datetime import timedelta,date,datetime

# 自定义包
from tl import IN_BACKTEST,data_to_period
from pf import *
from ds import dsFnd,dsIdx

#必须依照以下顺序导入、设置matplotlib
import matplotlib

if IN_BACKTEST:
    #策略中绘图必须使用Agg模式（即不显示图形）
    matplotlib.use('Agg') 
    print '基金框架：运行于策略'
else:
    print '基金框架：运行于研究'
    
import matplotlib.pyplot as plt


# 标识符
_ID='fnd'
_NOTE='基金'

_C10Y='C10Y'  
            

class Fields(TField):
    """
    Fields类，字段、名称对照
    """
    
    #价格字段
    price=['open','close','low','high','pre_close','volume','money']
    
    #估值字段
    val=['pe_e','pb_e','ps_e','pe_w','pb_w','ps_w','pe_m','pb_m','ps_m','pe_a','pb_a','ps_a','roe','dyr']
    
    #财务指标字段
    finance=['cap']
    
    #所有字段
    all=val+finance+price

    
#-------------------------------------------------------------------------------------- 
# Codes类，指数标的

class _Pool(TPool):
    """
    指数标的
    project：项目
    """
    def __init__(self,project):
        TPool.__init__(self,project)  

        
    # 代码转换
    def __convert_code(self,code): 
        # 代码转换
        if code.endswith('XSHG'):
            return code.replace('XSHG','SH')
        if code.endswith('XSHE'):
            return code.replace('XSHE','SZ')
        if code.upper().endswith('OF'):
            return code.upper()

        
    # 生成标的
    def create(self,pool):
        data_list=[] 
        code_list=[]
        for fund_code,index_code in pool.items():
            code_fund=self.__convert_code(fund_code)
            code_index=self.__convert_code(index_code)
            fund=get_security_info(fund_code)
            index=get_security_info(index_code)
            data_list.append([fund.display_name,fund.type,fund.start_date,
                             code_index,index.display_name])
            code_list.append(code_fund)  
        df=pd.DataFrame(index=code_list,data=data_list,columns=['name','type','start_date ','index_code','index_name'])  
        
        #生成列表
        self.to_track(df)
        # 调用父类方法保存:
        TPool.save(self,df)
   

    # 构造标的字典
    def to_track(self,df):
        # 所有标的
        self.track=df.name.to_dict()
        # ETF
        self.etf=df[df.type=='etf'].name.to_dict()
        # LOF
        self.lof=df[df.type=='lof'].name.to_dict()
        # OF
        self.open=df[df.type=='open_fund'].name.to_dict()
        # mixture_fund
        self.mixture=df[df.type=='mixture_fund'].name.to_dict()    
        # money_market_fund
        self.money=df[df.type=='money_market_fund'].name.to_dict()
        # QDII_fund
        self.qdii=df[df.type=='QDII_fund'].name.to_dict()
        # QDII_fund
        self.stock=df[df.type=='stock_fund'].name.to_dict()
        # QDII_fund
        self.bond=df[df.type=='bond_fund'].name.to_dict()


class _Data(Tdata):
    """
    数据类：指数数据获取、计算
    project：项目类
    pool：标的类
    """
    def __init__(self,project,pool):
        Tdata.__init__(self,project,pool)  
       
                
    # 代码转换为存储名
    def to_name(self,code):
        if code.endswith('SH'):
            return '%s_sh_%s'%(self.project.id,code[0:6])
        elif code.endswith('SZ'):
            return '%s_sz_%s'%(self.project.id,code[0:6])


    def get_data(self,code,start_date=None,end_date=None):
        """
        获取历史数据
        code：指数代码
        start_date；开始日期
        end_date；截至日期        
        """
        pass
        
        

class _Change(Tchange):
    """
    行情分析类
    project：项目类
    pool：标的类
    data：数据类
    """ 
    def __init__(self,project,pool,data):
        # 继承Tchange
        Tchange.__init__(self,project,pool,data) 
        
        

class _Chart(Tchart):
    """
    图表类
    pool：标的类
    data：数据类
    analyse：分析类
    """  
    def __init__(self,project,pool,data,analyse):
        # 继承Tchart
        Tchart.__init__(self,project,pool,data,analyse) 
        

    def line_10y(self,fig,start_date,style=['r--']):
        """
        在已有画板上添加10年期国债市盈率
        fig：原图画板对象
        start_date:原图数据起始日期
        style：线型
        """
        #创建右侧Y轴
        ax=fig.get_axes()[0]
        r_ax=ax.twinx()
        #获取十年期国债数据
        df=self.data.read(_C10Y,items=['pe'],start_date=start_date)
        #国债市盈率折线图
        df.plot(ax=r_ax,grid=True,linewidth=3.0,rot=0,style=style)
        #设置网格
        r_ax.grid(False)
        #获取原图的左侧Y轴ticks，设置新图右侧Y轴刻度
        ticks=ax.get_yticks()
        r_ax.set_yticks(ticks)
        #Y轴标题
        r_ylabel=Fields.label[_C10Y]
        #设置Y轴标题
        self.set_ylabel(r_ax,r_ylabel)
        #设置图例 
        self.set_legend(r_ax,[r_ylabel],1)
        #美化边框、刻度
        self.set_right(r_ax) 

        
class _Table(Ttable):
    """
    数据表类
    pool：标的类
    data：数据类
    analyse：分析类
    """           
    def __init__(self,project,pool,data,analyse):
        Ttable.__init__(self,project,pool,data,analyse)


        
class Fund(object):
    """
    基金
    data_name：'cvs'表示使用文件引擎，其它表示数据库文件名,使用数据库引擎
    data_path：文件路径或数据库路径
    project_name：项目名称
    project_id：项目ID
    project_note：项目说明
    """
    # 构造函数
    def __init__(self,data_name,data_path,project_name=None,project_id=_ID,project_note=_NOTE):
        self.project=TProject(data_name,data_path,project_name,project_id,project_note)
        # 组合其它类  
        self.pool=_Pool(self.project)
        self.data=_Data(self.project,self.pool)
        
        self.change=_Change(self.project,self.pool,self.data)
        
#         self.change.chart=_Chart(self.project,self.pool,self.data,self.change)
#         self.value.chart=_Chart(self.project,self.pool,self.data,self.value)
#         self.change.table=_Table(self.project,self.pool,self.data,self.change)
#         self.value.table=_Table(self.project,self.pool,self.data,self.value)

        
      