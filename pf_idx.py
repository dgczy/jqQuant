# -*- coding: utf-8 -*-

"""

指数估值、行情计算分析

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
from tl import IN_BACKTEST,data_to_period,data_del_IQR,get_volatility,get_annualized,get_divid
from pf import *
from ds import dsIdx

#必须依照以下顺序导入、设置matplotlib
import matplotlib

if IN_BACKTEST:
    #策略中绘图必须使用Agg模式（即不显示图形）
    matplotlib.use('Agg') 
    print '指数框架：运行于策略'
else:
    print '指数框架：运行于研究'
    
import matplotlib.pyplot as plt


# 标识符
_ID='idx'
_NOTE='指数'

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
    def __convert_code(self,market):
        if market in ['sh']:
            return '.SH'
        elif market in ['sz']:  
            return '.SZ'
        else:
            return ''

        
    # 生成标的
    def create(self,pool):
        # 字典转换为dt
        df=pd.DataFrame(pool,columns=['code','name','market','type','watch','fund'])        
        df.index=[df.code[i]+self.__convert_code(df.market[i]) for i in range(len(df))]
        del df['code']   
        #生成列表
        self.to_track(df)
        # 调用父类方法保存:
        TPool.save(self,df)
   

    # 构造标的字典
    def to_track(self,df):
        # 所有标的
        self.track=df.name.to_dict()
        # 主要跟踪的
        self.watch=df[df.watch].name.to_dict()
        # 估值标的
        self.value=df[df.market.isin(['sh','sz','hk'])].append(df[(df.market.isin(['us']) & df.watch)]).name.to_dict()
        # A股
        self.hs=df[df.market.isin(['sh','sz'])].name.to_dict()
        # A股全市场
        self.qsc=df[df.type.isin(['qsc']) & df.watch].name.to_dict()
        # A股宽基
        self.kj=df[df.type.isin(['kj']) & df.watch].name.to_dict()
        # A股行业、主题
        self.zj=df[df.type.isin(['zj']) & df.watch].name.to_dict()
        # 海外指数
        self.hw=df[df.market.isin(['hk','us','eu','as','qt'])].name.to_dict()
        # 港股指数
        self.hk=df[df.market.isin(['hk']) & df.watch].name.to_dict()
        # 美股指数
        self.us=df[df.market.isin(['us']) & df.watch].name.to_dict()
    


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
        if code in self.pool.hs:
            if code.endswith('SH'):
                return '%s_sh_%s'%(self.project.id,code[0:6])
            elif code.endswith('SZ'):
                return '%s_sz_%s'%(self.project.id,code[0:6])
        elif code in self.pool.hw: 
            return '%s_hw_%s'%(self.project.id,code.lower())
        elif code in [_C10Y]:
            return 'mcr_%s'%(code.lower())
        else:
            return code      
    
       
    def __get_hs_day(self,code,end_date):   
        """
        沪深指数某日估值
        code：指数代码
        end_date；截至日期        
        """
        #获取成份股
        stocks=dsIdx.stocks(code,end_date)
        #获取成份股财务信息
        q=query(
            valuation.pe_ratio,
            valuation.pb_ratio,
            valuation.ps_ratio,
            valuation.circulating_market_cap,
        ).filter(
            valuation.code.in_(stocks)
        )
        df=get_fundamentals(q,end_date)
        if len(df)==0: 
            return (None,None,None,None,None,None,None,None,None,None,None,None,None,None,None)
        #样本数
        n=len(df)
        #加权pe、pb、ps
        #所有股票流通总市值/所有股票税后利润
        #pe_ratio、pb_ratio、ps_ratio剔除零值
        cmc=df['circulating_market_cap'].sum()
        pe_w=cmc/(df['circulating_market_cap']/df['pe_ratio'][df['pe_ratio']!=0]).sum()
        pb_w=cmc/(df['circulating_market_cap']/df['pb_ratio'][df['pb_ratio']!=0]).sum()    
        ps_w=cmc/(df['circulating_market_cap']/df['ps_ratio'][df['ps_ratio']!=0]).sum() 
        #中位数pe、pb、ps
        #排序、取中值
        #pe_ratio、pb_ratio、ps_ratio负值视作零值
        pe_m=np.median(sorted([p if p>0 else 0 for p in df['pe_ratio']]))
        pb_m=np.median(sorted([p if p>0 else 0 for p in df['pb_ratio']]))
        ps_m=np.median(sorted([p if p>0 else 0 for p in df['ps_ratio']]))
        #等权pe、pb、ps
        #pe_ratio、pb_ratio、ps_ratio负值视作零值
        pe_e=n/sum([1/p if p>0 else 0 for p in df['pe_ratio']])
        pb_e=n/sum([1/p if p>0 else 0 for p in df['pb_ratio']]) 
        ps_e=n/sum([1/p if p>0 else 0 for p in df['ps_ratio']]) 
        #算数平均pe、pb、ps
        #剔除负值、剔除极值
        pe_df=data_del_IQR(df['pe_ratio'],k=0.734)
        pb_df=data_del_IQR(df['pb_ratio'],k=0.734)
        ps_df=data_del_IQR(df['ps_ratio'],k=0.734)
        pe_a=pe_df.sum()/n
        pb_a=pb_df.sum()/n
        ps_a=ps_df.sum()/n
        #roe，加权pb除以加权pe
        roe=pb_w/pe_w*100 if pe_w>0 else float(np.NaN) 
        #股息率、市值
        dyr,cap=get_divid(dsIdx.stocks(code,end_date),end_date)
        #返回数据
        return (
            round(pe_e,2),round(pb_e,2),round(ps_e,2),round(pe_w,2),round(pb_w,2),round(ps_w,2),
            round(pe_m,2),round(pb_m,2),round(ps_m,2),round(pe_a,2),round(pb_a,2),round(ps_a,2),
            round(roe,2),round(dyr,2),round(cap,2)) 


    def __get_hs(self,code,start_date=None,end_date=None):
        """
        计算沪深指数历史数据
        code：指数代码
        start_date；开始日期
        end_date；截至日期        
        """
        # 日期约束
        if start_date is None:
            start_date=dsIdx.info(code).start_date
            if start_date<'2005-01-04': 
                start_date='2005-01-04'
        if end_date is None:
            end_date=pd.datetime.today()-timedelta(1)
            
        #获取行情数据
        price_df=dsIdx.hist(code,start_date=start_date,end_date=end_date,fields=Fields.price)  
        
        #生成交易日期
        date_list=price_df.index.tolist()   
        # 获取估值数据
        valuation_list=[]
        for d in date_list:     
            print '\r数据更新：%s %s'%(self.pool.track[code],d.strftime('%Y年%m月%d日')),      
            valuation_list.append(self.__get_hs_day(code,d)  )
        print '\r',
        
        # 生成估值数据表     
        valuation_df=pd.DataFrame(data=valuation_list,index=date_list,columns=Fields.val+Fields.finance)   
        # 拼接行情和估值数据
        df=pd.concat([valuation_df,price_df],axis=1) 
        # 返回数据
        return df
        
        
    def __get_hw(self,code,start_date=None,end_date=None): 
        """
        获取海外指数历史数据
        code：指数代码
        start_date；开始日期
        end_date；截至日期        
        """
        try:
            # 获取数据
            hist_df=dsIdx.hist(code,start_date)
            if hist_df is None:
                return None
            # 组织数据
            df=pd.DataFrame(index=hist_df.index,columns=Fields.all)
            # 填充close等列
            for col in hist_df.columns:
                df[col]=hist_df[col]
            return df
        except Exception as e:
            print('%s'%e)
            print '\r数据更新：%s 失败'%self.pool.track[code],


    def get_data(self,code,start_date=None,end_date=None):
        """
        获取历史数据
        code：指数代码
        start_date；开始日期
        end_date；截至日期        
        """
        if code in self.pool.hs:
            df=self.__get_hs(code,start_date,end_date)
        elif code in self.pool.hw: 
            df=self.__get_hw(code,start_date,end_date)
        return df



class _Value(Tvalue):
    """
    估值分析
    project：项目类
    pool：标的类
    data：数据类
    """            
    def __init__(self,project,pool,data):
        # 继承Tvalue
        Tvalue.__init__(self,project,pool,data) 
  
    
    def __get_stock_count(self,code,end_date):
        """
        获取成份股数
        code：指数代码
        end_date：截至日期
        """
        return len(dsIdx.stocks(code,end_date))

    
    def standard_cols(self):
        """
        标准分析字段
        """
        return Fields.val

    
    def extend_analysis(self,code,df):
        """
        扩展分析
        """
        # 成立日期
        found=dsIdx.info(code).start_date
        # 波动率
        vlt=get_volatility(df[['close']])
        # 回报率
        roi=get_annualized(df[['close']])
        # 成份股数
        stocks=self.__get_stock_count(code,df.index[-1].date())
        return found,vlt,roi,stocks 

    
    def extend_columns(self):
        """
        扩展分析标题
        """
        return ['found','vlt','roi','stocks']
        
        

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
        

    def line_qsc(self,code1='000902.SH',item='pe',mode='e',code2='399106.SH',years=10,period='W',y10=False):
        """
        全市场走势对比图
        code：全市场指数代码
        code2：对比指数代码
        item：字段，pe、pb、ps
        mode：算法，e、w、m、a对应等权、加权、中位数、算数平均数
        years：时段，10、5、3、0对应10年、5年、3年、全部时段
        period：线型
        y10：十年期国债市盈率
        """
        #item名称
        item_name=Fields.label[item]
        #算法名称
        mode_name='' if mode=='' else Fields.label[mode]+' '
        #字段修正
        item=item if mode=='' else '%s_%s'%(item,mode)
        right='close'
        #读取数据
        df=self.data.read(code1,years=years,items=[item],period='D')  
        #对比指数点位
        r_df=self.data.read(code2,years=years,items=[right],period='D')
        df[right]=r_df[right]
        #获取数据分析表数据
        table=self.analyse.read(years)
        #当前值
        item_val=table.ix[code1,item]       
        #百分位
        item_ratio=table.ix[code1,item+'_ratio']
        #图例名称   
        item_legend=[u'%s %.2f %.2f%%'%(item_name,item_val,item_ratio)]
        #十年期国债市盈率
        if y10:
            df_10y=self.data.read(_C10Y,items=['pe'],years=years)
            df['c10y']=df_10y['pe']
            item_legend+=[u'%s %.2f'%(Fields.label[_C10Y],df['c10y'].iloc[-1])]  
        #转换数据    
        df=data_to_period(df,period)   
        #标题
        title=[(u'%s%s-%s对比')%(self.pool.track[code1],item_name,self.pool.track[code2]),(u'%s%s %s  %s')%(
            mode_name,Fields.label[years],Fields.label[period],df.index[-1].strftime('%Y年%m月%d日'))]
        #画线
        ax=df.plot(figsize=(18,8),secondary_y=[right],fontsize=12.5,linewidth=1,grid=True,mark_right=False,rot=0,
                   style=['b','orange','r'])
        #设置标题
        self.set_title(ax,title)
        #设置Y轴标题
        self.set_ylabel(ax,'%s %s'%(self.pool.track[code1],item_name))
        #设置图例 
        self.set_legend(ax,item_legend,2,8)
        #设置网格线
        self.set_grid(ax)
        #美化边框、刻度
        self.set_left(ax)
        #获取画板和r_ax
        fig=ax.get_figure()
        if right!='':
            r_ax=fig.get_axes()[1] 
            #设置Y轴标题
            self.set_ylabel(r_ax,self.pool.track[code2])
            #图例
            r_legend=[u'%s %s %.2f'%(self.pool.track[code2],Fields.label[right],df[right].iloc[-1])]            
            self.set_legend(r_ax,r_legend,1)
            #边框、刻度
            self.set_right(r_ax) 
        #返回figure对象
        return fig  


    def line_mode(self,code,item='pe',years=10,right='close',period='W'): 
        """
        估值算法对比
        code：指数代码
        item：字段，pe、pb、ps、roe、dyr
        years：时段，10、5、3、0对应10年、5年、3年、全部时段
        right：右轴对比，close、cap对应收盘点位、市值，为空时表示关闭对比
        period：线型
        """
        #item名称
        item_name=Fields.label[item]
        #字段列表
        item_list=[item+'_e',item+'_w',item+'_a',item+'_m']
        if right!='':
            item_list+=[right]
        #获取数据，并转换为周数据    
        df=self.data.read(code,years=years,items=item_list,period=period)
        #最新值
        item_e=df[item+'_e'].iloc[-1]
        item_w=df[item+'_w'].iloc[-1]
        item_m=df[item+'_m'].iloc[-1]
        item_a=df[item+'_a'].iloc[-1]
        #图表标题
        title=[(u'%s-%s算法对比')%(self.pool.track[code],item_name),
            (u'%s %s  %s')%(Fields.label[years],Fields.label[period],df.index[-1].strftime('%Y年%m月%d日'))]
        #图例列表
        item_legend=['等权平均值 %.2f'%item_e,'加权平均值 %.2f'%item_w,'算数平均值 %.2f'%item_a,'中位数%.2f'%item_m]
        #画图，收盘点位在Y轴右侧        
        ax=df.plot(figsize=(18,8),secondary_y=[right],fontsize=12.5,linewidth=1,grid=True,mark_right=False,rot=0,style=['b','m','g','c','orange'])
        #设置标题
        self.set_title(ax,title)
        #设置Y轴标题
        self.set_ylabel(ax,item_name)
        #设置图例 
        self.set_legend(ax,item_legend,2,4)
        #设置网格线
        self.set_grid(ax)
        #美化边框、刻度
        self.set_left(ax)
        #获取画板和r_ax
        fig=ax.get_figure()
        if right!='':
            r_ax=fig.get_axes()[1] 
            #y轴标题
            r_ylabel=Fields.label[right]
            #图例标题
            r_legend=[u'%s %.2f'%(r_ylabel,df[right].iloc[-1])]
            #设置Y轴标题
            self.set_ylabel(r_ax,r_ylabel)
            #设置图例 
            self.set_legend(r_ax,r_legend,1)
            #美化边框、刻度
            self.set_right(r_ax) 
        return fig    


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


        
class Index(object):
    """
    指数综合类
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
        self.value=_Value(self.project,self.pool,self.data)
        
        self.change.chart=_Chart(self.project,self.pool,self.data,self.change)
        self.value.chart=_Chart(self.project,self.pool,self.data,self.value)
        self.change.table=_Table(self.project,self.pool,self.data,self.change)
        self.value.table=_Table(self.project,self.pool,self.data,self.value)

        
    # 机会值、危险值    
    def set_chance(chance,danger):
        self.value.chance=chance
        self.value.danger=danger

        
class IdxChg(object):
    """
    指数行情类 
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
        
        self.analyse=_Change(self.project,self.pool,self.data)
        
        self.chart=_Chart(self.project,self.pool,self.data,self.analyse)
        self.table=_Table(self.project,self.pool,self.data,self.analyse)
        
        
class IdxVal(object):
    """
    指数估值类 
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
        
        self.analyse=_Value(self.project,self.project,self.pool,self.data)
        
        self.chart=_Chart(self.project,self.pool,self.data,self.analyse)
        self.table=_Table(self.project,self.pool,self.data,self.analyse)       