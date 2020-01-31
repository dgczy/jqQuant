# -*- coding: utf-8 -*-



#导入库
import numpy as np
import pandas as pd
import time
import jqdata

from datetime import timedelta,date


#导入自定义包
from tl import IN_BACKTEST,get_volatility,get_annualized
from pf import *
from ds import dsCmm

#必须依照以下顺序导入、设置matplotlib
import matplotlib

if IN_BACKTEST:
    #策略中绘图必须使用Agg模式（即不显示图形）
    matplotlib.use('Agg') 
    print '商品框架：运行于策略'
else:
    print '商品框架：运行于研究'
    
import matplotlib.pyplot as plt

    
_ID='cmm'
_NOTE='商品'


class Fields(TField):
    pass


class _Pool(TPool):
    
    def __init__(self,project):
        TPool.__init__(self,project)  

    
class _Data(Tdata):
    """
    获取商品价格数据
    """
    def __init__(self,project,pool):
        Tdata.__init__(self,project,pool)  
       
    # 重载父类方法    
    def get_data(self,code,start_date=None,end_date=None):
        return dsCmm.hist(code=code,start_date=start_date,end_date=end_date)   
    
    # 获取比值
    def __get_ratio(self):   
        gsr_df=pd.DataFrame()
        gor_df=pd.DataFrame()
        #读取数据
        g_df=self.read('XAU').close
        s_df=self.read('XAG').close
        o_df=self.read('OIL').close
        #计算比值
        gsr_df['gsr']=np.round(g_df/s_df,2)
        gor_df['gor']=np.round(g_df/o_df,2)
        #保存
        self.save('gsr',gsr_df.dropna(),False)
        self.save('gor',gor_df.dropna(),False)

    # 重载父类方法
    def update(self,codes):
        # 执行父类方法
        Tdata.update(self,codes)
        # 获取比值
        self.__get_ratio()
    
      
class _Value(Tvalue): 
    """
    分析数据
    """
    def __init__(self,project,pool,data):
        Tvalue.__init__(self,project,pool,data) 
     
    def standard_cols(self):
        return ['close']
 
    
    def extend_analysis(self,code,df):
        """
        扩展分析
        """
        # 波动率
        vlt=get_volatility(df[['close']])
        # 回报率
        roi=get_annualized(df[['close']])
        return vlt,roi

    
    def extend_columns(self):
        """
        扩展分析标题
        """
        return ['vlt','roi']  
    
    

class _Change(Tchange):
    """
    行情分析
    """   
    def __init__(self,project,pool,data):   
        Tchange.__init__(self,project,pool,data)  
        
    
class _Chart(Tchart):  
    """
    生成图表
    """
    
    def __init__(self,project,pool,data,analyse):
        Tchart.__init__(self,project,pool,data,analyse)

        
    #对比图
    def compar(self,codes,title=None,years=10,period='D'):
        df=pd.DataFrame() 
        #加载数据
        for code in codes:
            df[code]=self.data.read(code,years=years,period=period).close
           
        #生成金、银价格对比图
        ax=df.plot(figsize=(18,8),secondary_y=[codes[1]],mark_right=False,linewidth=0.8,rot=0,
            style=['orange','gray'],grid=True)
        #设置画板
        self.set_title(ax,['%s-走势对比'%(title),
            '%s %s  %s'%(Fields.name(years),Fields.name(period),df.index[-1].date().strftime('%Y-%m-%d'))])
       
        self.set_legend(ax,['%s %.2f'%(self.pool.name(codes[0]),df[codes[0]].iloc[-1])],loc=2)
        self.set_ylabel(ax,self.pool.name(codes[0]))
        self.set_grid(ax)
        self.set_left(ax)
        rax=ax.get_figure().get_axes()[1]
        self.set_legend(rax,['%s %.2f'%(self.pool.name(codes[1]),df[codes[1]].iloc[-1])],loc=1)
        self.set_ylabel(rax,self.pool.name(codes[1]))
        self.set_right(rax)

        
    #金银比
    def gsr(self,years=10,period='D'):
        #读取数据
        df=self.data.read('gsr',years=years,period=period)
        #辅助线
        val=df['gsr'].iloc[-1]
        df['per']=val
        df['80']=80
        df['70']=70   
        df['55']=55
        df['45']=45
        #生成金银比走势图
        ax=df.plot(figsize=(18,8),linewidth=0.8,rot=0,
            style=['c', 'c', 'g-.','g', 'r', 'r-.'],grid=True)
        #设置画板
        legend=['金银比','当前值：%.2f'%val,'80','高于70 银价低估','低于55 金价低估','45']
        self.set_title(ax,['金、银价格比-走势',
            '%s %s  %s'%(Fields.name(years),Fields.name(period),df.index[-1].date().strftime('%Y-%m-%d'))])
        self.set_legend(ax,legend,loc='best')
        self.set_grid(ax)
        self.set_left(ax)        

        
    #金油比
    def gor(self,years=10,period='D'):
        #读取数据
        df=self.data.read('gor',years=years,period=period)
        #辅助线
        val=df['gor'].iloc[-1]
        val_median=round(df['gor'].median(),2)
        df['val']=val
        df['median']=val_median
        df['30']=30
        #生成金银比走势图
        ax=df.plot(figsize=(18,8),linewidth=0.8,rot=0,
            style=['c', 'c-.', 'k','r', 'r', 'r-.'],grid=True)
        #设置画板
        legend=['金油比','当前值：%.2f'%val,'中位值：%.2f'%val_median,'危险值：%.2f'%30]
        self.set_title(ax,['金、油价格比-走势',
            '%s %s  %s'%(Fields.name(years),Fields.name(period),df.index[-1].date().strftime('%Y-%m-%d'))])
        self.set_legend(ax,legend,loc='best')
        self.set_grid(ax)
        self.set_left(ax)
        
        
    #价格走势图
    def line(self,codes,years=10,period='D'):
        for code,name in codes.items():
            item='close'
            #读取数据
            df=self.data.read(code,years=years,period=period)[[item]]
            table=self.analyse.read(years)
            #辅助线
            val=df.iloc[-1].close   
            val_q20=table.ix[code,item+'_q20']  
            val_q50=table.ix[code,item+'_q50'] 
            val_q80=table.ix[code,item+'_q80']
            df['current']=val
            df['q20']=val_q20    
            df['q50']=val_q50
            df['q80']=val_q80
            #画图
            ax=df.plot(figsize=(18,8),linewidth=0.5,style=['b','b:','r','k','g'],grid=True,rot=0)
            #设置画板
            legend=[name,'当前 %0.2f'%(val),'%s%% %0.2f'%(20,val_q20),
                '%s%% %0.2f'%(50,val_q50),'%s%% %0.2f'%(80,val_q80)]
            self.set_legend(ax,legend,loc='best')
            self.set_title(ax,[name,'%s %s  %s'%(Fields.name(years),Fields.name(period),
                df.index[-1].date().strftime('%Y-%m-%d'))])
            self.set_grid(ax)
            self.set_left(ax)



class _Table(Ttable):
    """
    生成分析表
    """
    
    def __init__(self,project,pool,data,analyse):
        Ttable.__init__(self,project,pool,data,analyse)
        
    def show(self,sort='ratio',asc=True,years=10):
        return self.value(self.pool.track,'close','',sort,asc,years)
         
        
class Cmm(object):

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
        
        

