# -*- coding: utf-8 -*-



#导入库
import numpy as np
import pandas as pd
import time
from datetime import timedelta,date

import jqdata


#导入自定义包
from tl import IN_BACKTEST,get_volatility,get_annualized,get_divid
from pf import *
from ds import dsStk

#必须依照以下顺序导入、设置matplotlib
import matplotlib

if IN_BACKTEST:
    #策略中绘图必须使用Agg模式（即不显示图形）
    matplotlib.use('Agg') 
    print '个股框架：运行于策略'
else:
    print '个股框架：运行于研究'
    
import matplotlib.pyplot as plt


_ID='stk'
_NOTE='股票'


#判断退市、st股票
def is_st(code):
    stock_name=get_security_info(code).display_name
    return stock_name.startswith('*') or stock_name.startswith('ST') or stock_name.startswith('退')


#判断创业板股票
def is_cyb(code):
    return code.startswith('300')


#判断年报是否已出
def is_report(code,stat_year=2017):
    q=query(indicator.inc_return,).filter(indicator.code==code)
    return len(get_fundamentals(q,statDate=str(stat_year)))>0


#获取股票所属行业
def get_stock_industry(code,date=pd.datetime.today()):
    try:
        return get_industry(security=code,date=date)[code]['sw_l1']['industry_name']
    except:
        return None


#获取pe、pb、ps、自由流通市值
def get_stock_valuation(code):
    q=query(
        valuation.pe_ratio,
        valuation.pb_ratio,
        valuation.ps_ratio,
        valuation.circulating_market_cap,
    ).filter(
        valuation.code==code
    )
    df=get_fundamentals(q)   
    return (round(df['pe_ratio'].iloc[0],2),round(df['ps_ratio'].iloc[0],2),
           round(df['pb_ratio'].iloc[0],2),round(df['circulating_market_cap'].iloc[0],2))


#计算roe、毛利率、营业收入复合增长、净利润复合增长
#code：代码
#stat_year：年报截至年份，如：2017
#max_year：统计年数，如：5，即向前统计5年
#calc_year：计算年数，如：3，即向前计算3年
def get_stock_indicator(code,stat_year=2017,max_year=5,calc_year=5): 
    q = query(
        indicator.code,
        indicator.inc_revenue_year_on_year,
        indicator.inc_net_profit_year_on_year,
        indicator.gross_profit_margin,
        indicator.inc_net_profit_to_shareholders_year_on_year,
        indicator.inc_return,
    ).filter(
        indicator.code==code
    )
    df=pd.DataFrame()
    #获取近五年财务信息
    for i in range(0,max_year):
        rets=get_fundamentals(q,statDate=str(stat_year-i))
        df=pd.concat([df,rets],axis=0)  
    #print df    
    #营业收入复合增长率=近三年营业收入同比增长率之和的平均值
    inc_revenue=df['inc_revenue_year_on_year'][0:calc_year].mean()
    #净利润复合增长率=近三年净利润同比增长率之和的平均值
    net_profit=df['inc_net_profit_to_shareholders_year_on_year'][0:calc_year].mean()
    roe_mean=df['inc_return'][0:calc_year].mean()
    #毛利率（最近年报毛利率）    
    gross_profit=df['gross_profit_margin'].iloc[0]
    #roe（最近年报roe）         
    roe=df['inc_return'].iloc[0] 
    #最新年报净利润
    new_profit=df['inc_net_profit_to_shareholders_year_on_year'].iloc[0]
    return (round(roe,2),
            round(roe_mean,2),
            round(gross_profit,2),
            round(inc_revenue,2),
            round(net_profit,2),
            round(new_profit,2),
            df)

def get_stock_goodwill(code,stat_date): 
    #查询资产负债表、利润表
    q = query(
        balance.code,
        balance.good_will,#商誉
        balance.total_assets,#总资产
        balance.total_liability,#总负债
        income.net_profit#净利润
    ).filter(
        balance.code==code
    )
    df=get_fundamentals(q, statDate=stat_date)
    if len(df)>0:
        #净利润
        net_profit=float(df['net_profit'].iloc[0])
        #总资产
        total_assets=float(df['total_assets'].iloc[0])
        #总负债
        total_liability=float(df['total_liability'].iloc[0])
        #净资产
        net_assets=total_assets-total_liability
        #商誉
        good_will=float(df['good_will'].iloc[0])
        return (round(net_profit/10000000,4),round(net_assets/100000000,4),
                round(good_will/100000000,4),round(good_will/net_assets*100,4))
    else:
        return (None,None,None,None)


def get_bank_stock_indicator(code,date=2017): 
    q = query(
        bank_indicator.code,
        bank_indicator.net_interest_margin,
        bank_indicator.core_level_capital_adequacy_ratio,
        bank_indicator.Nonperforming_loan_rate,
        bank_indicator.non_performing_loan_provision_coverage,
    ).filter(
        bank_indicator.code==code
    )
    df=pd.DataFrame()
    #获取近五年财务信息
    for i in range(0,5):
        rets=get_fundamentals(q, statDate=str(date-i))
        df = pd.concat([df,rets],axis=0)    
    #净息差
    nim=df['net_interest_margin'].iloc[0]
    nim_mean=mean(df['net_interest_margin'])
    #核心一级资本充足率
    clcar=df['core_level_capital_adequacy_ratio'].iloc[0]
    clcar_mean=mean(df['core_level_capital_adequacy_ratio'])
    #不良贷款率
    nlr=df['Nonperforming_loan_rate'].iloc[0]
    #不良贷款拨备覆盖率
    nplpc=df['non_performing_loan_provision_coverage'].iloc[0]
    return (nim,clcar,nlr,nplpc)


class Fields(TField):
    label={'name':'名称','pe':'PE-TTM','pb':'PB','ps':'PS','roe':'ROE','roe_mean':'ROE均(%)','dyr':'股息率','peg':'PEG',
           'market_cap':'自由流通总市值(亿)',
           'gross_profit':'毛利率(%)','revenue_grow':'营复增(%)','profit_grow':'利复增(%)','new_profit_grow':'最新利增(%)',
           'net_profit':'净利润(千万)','net_assets':'净资产(亿)','good_will':'商誉(亿)','good_will_ratio':'商誉占比(%)',
           'industry':'所属行业','ipo_date':'IPO日期'}
    
    
                          
                         
class _Pool(TPool):
    
    def __init__(self,project):
        TPool.__init__(self,project)
    
    def create_form(self,pool,*args,**kwargs):
        """
        股票池筛选
        pool：筛选函数名
        *args,**kwargs：筛选函数参数
        """
        #调用筛选函数
        df=pool(*args,**kwargs)
        #保存股票池
        self.save(df) 
        #生成代买列表
        self.to_track(df)  
       
    def show(self,columns=None):
        """
        查看roe20股票池
        """
        #读取股票池
        df=TPool.show(self)
        #去除代码前缀
        df.index=df.index.str[0:6]
        if columns is None:
            #更改列名
            df=df.rename(columns=Fields.label)
        else:
            df.columns=columns
        return df
    
    def show(self,columns=None):
        """
        查看roe20股票池
        """
        #读取股票池
        df=TPool.show(self)
        if len(df)>0:
            #去除代码前缀
            df.index=df.index.str[0:6]
        if columns is None:
            #更改列名
            df=df.rename(columns=Fields.label)
        else:
            df.columns=columns
        return df
    
    
class _Data(Tdata):
    
    def __init__(self,project,pool):
        Tdata.__init__(self,project,pool)  
        
    def to_name(self,code):
        #代码转换
        if code.endswith('XSHG'):
            return '%s_sh_%s'%(self.project.id,code[0:6])
        elif code.endswith('XSHE'):
            return '%s_sz_%s'%(self.project.id,code[0:6])
            
    #计算PE、PB等数据   
    def get_oneday(self,code,date):   
        #获取财务信息
        q=query(valuation).filter(valuation.code==code)
        df=get_fundamentals(q,date)
        if len(df)>0:  
            #股息率、市值
            dyr,cap=get_divid(code,date)
            return (round(df.pe_ratio.iloc[-1],2),round(df.pb_ratio.iloc[-1],2), 
                    round(df.ps_ratio.iloc[-1],2),round(df.pcf_ratio.iloc[-1],2),
                    round(df.pb_ratio.iloc[-1]/df.pe_ratio.iloc[-1]*100,2),
                    round(dyr,2),round(cap,2))        
        else:
            return (float('NaN'), float('NaN'),float('NaN'),float('NaN'),
                    float('NaN'),float('NaN'),float('NaN')) 


    #计算pe、pb、roe、点位数据
    def get_data(self,code,start_date=None,end_date=None):
        #只计算2005年以来的数据
        if start_date is None:
            start_date=dsStk.info(code).start_date
            if start_date < '2005-01-04': 
                start_date = '2005-01-04'
        if end_date is None:
            end_date=pd.datetime.today()-timedelta(1)
        #获取点位
        price_df=dsStk.hist(code,start_date=start_date, end_date=end_date,
                          fields=['open','close','low','high','pre_close','volume','money'])    
        date_list=price_df.index.tolist()   
        valuation_list=[]

        for d in date_list:     
            print '\r数据更新：%s %s %s'%(code[0:6],self.pool.track[code],d.strftime('%Y年%m月%d日')),
            #获取估值数据
            data=self.get_oneday(code,d)      
            valuation_list.append(data)
        #组织数据      
        valuation_df=pd.DataFrame(data=valuation_list,index=date_list,
                                    columns=['pe','pb','ps','pcf','roe','dyr','cap'])   
        df=pd.concat([valuation_df,price_df],axis=1)
        return df
    


class _Value(Tvalue):
    
    def __init__(self,project,pool,data):
        Tvalue.__init__(self,project,pool,data) 
         
    def get_found_date(self,code):
        return get_security_info(code).start_date

    def standard_cols(self):
        return ['pe','pb','ps','pcf','roe','dyr']
    
    def extend_analysis(self,code,df):
#         #收盘价
#         price=df.iloc[-1].close 
#         #涨跌
#         change=round(df['close'].iloc[-1]-df['pre_close'].iloc[-1],2)
#         #涨幅
#         rise=round(change/df['pre_close'].iloc[-1]*100,2)
#         #总手
#         volume=df['volume'].iloc[-1]/100/10000.0
#         #总额
#         money=df['money'].iloc[-1]/100000000.0
        # roe、roe（均）、毛利率、营业收入复合增长率、利润复合增长率
        (roe,roe_mean,Profit_margin,income,profit,new_profit,tdf)=get_stock_indicator(code)
        # 流通市值、股息、股息（均）
        cap=round(df.iloc[-1].cap/profit,2)
        #dyr=round(df.iloc[-1].dyr/profit,2)
        # peg
        peg=round(df.iloc[-1].pe/profit,2)
        # 股票所属行业
        industry=get_stock_industry(code) 
        return cap,roe,roe_mean,Profit_margin,income,profit,peg,industry
#         return price,rise,change,volume,money,markt,roe,roe_mean,Profit_margin,income,profit,divid,divid_mean,peg,industry

    def extend_columns(self):
        return [
            #'price','rise','change','volume','money',
            'cap',
             'roe','roe_mean','Profit_margin', 'income','profit',
            #'dyr',
            #'divid_mean',
            'peg',
            'industry']
        

class _Change(Tchange):
    """
    行情分析
    """   
    def __init__(self,project,pool,data):
        Tchange.__init__(self,project,pool,data) 
        
        
    def get_found_date(self,code):
        """
        IPO日期    
        code：代码
        """
        return dsStk.info(code).start_date   
                
        
class _Chart(Tchart):   
    
    def __init__(self,project,pool,data,analyse):
        Tchart.__init__(self,project,pool,data,analyse)

    def pe(self,code,years=5,right='close',period='W',quantile=True):  
        self.line_merit(code,item='pe',mode='',years=years,right=right,period=period,quantile=quantile)
             
    def pb(self,code,years=5,right='close',period='W',quantile=True):  
        self.line_merit(code,item='pb',mode='',years=years,right=right,period=period,quantile=quantile)
    
    def ps(self,code,years=5,right='close',period='W',quantile=True):  
        self.line_merit(code,item='ps',mode='',years=years,right=right,period=period,quantile=quantile)    
    
    def roe(self,code,years=5,right='close',period='W',quantile=True):  
        self.line_merit(code,item='roe',mode='',years=years,right=right,period=period,quantile=quantile)
        
    
    def dyr(self,code,years=5,right='close',period='W',quantile=True):  
        self.line_merit(code,item='dyr',mode='',years=years,right=right,period=period,quantile=quantile)

        
class _Table(Ttable):
    
    def __init__(self,project,pool,data,analyse):
        Ttable.__init__(self,project,pool,data,analyse)


    def finance_columns(self):
        return {'name':'名称',
                  'Profit_margin':'毛利率','roe':'ROE','roe_mean':'ROE均','income':'营复增',
                  'profit':'利复增','dyr':'股息率',
                    #'divid_mean':'股息率均%',
                  'peg':'PEG','cap':'市值(亿)','industry':'所属行业','found':'IPO日期'}

    
    def finance_cols(self):
        return ['name','Profit_margin','roe','roe_mean','income','profit','dyr',
                # 'divid_mean',
                 'peg','cap','industry','found']

        
    def integrate_columns(self,mode):
        return {'name':'名称',
            'pe':'PE','pe_ratio':'PE高度','pb':'PB','pb_ratio':'PB高度',
            'Profit_margin':'毛利率','roe':'ROE','roe_mean':'ROE均',
            'income':'营复增','profit':'利复增','dyr':'股息率',
                              #'divid_mean':'股息率均%',
                              'peg':'PEG',
            'industry':'所属行业'}
    
    
    def integrate_cols(self,mode):
        return ['name','pe','pe_ratio','pb','pb_ratio',
                'Profit_margin','roe','roe_mean','income','profit','dyr',
                                    # 'divid_mean',
                                     'peg','industry']
    


class Stk(object):
 
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