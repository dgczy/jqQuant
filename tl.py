
# -*- coding: utf-8 -*-

"""
判断运行环境
通过检测环境变量
"""

# 基本包

try:
    #策略中必须导入kuanke.user_space_api包
    from kuanke.user_space_api import *
except:
    pass

import numpy as np
import pandas as pd
import math
import os

# 聚源数据、交易日
from jqdata import jy

# 日期时间
import time 
from datetime import timedelta,date,datetime

IN_BACKTEST=not(os.environ.get("JUPYTERHUB_API_TOKEN") or os.environ.get("JPY_API_TOKEN"))




#检测文件      
def exists_file_in_research(file_name):
    """
    研究中检测文件，使用os.path.exists函数
    file_name：文件名、含路径，str
    """
    return os.path.exists(file_name) 


#检测文件      
def exists_file_in_backtest(file_name):
    """
    策略中检测文件，使用read_file函数
    file_name：文件名、含路径，str
    """
    try:
        # 尝试读取文件，成功则文件存在
        read_file(file_name)
        return True    
    except:
        # 出现错误，则文件不存在
        return False

    
exists_file=exists_file_in_backtest if IN_BACKTEST else exists_file_in_research
  
    
def get_volatility(df,years=None,days=30):
    """
    波动率
    df：数据表，df
    years：以年为单位的时段，int
    days：以年为单位的时段，int
    返回：波动率，float
    """
    # 按照年取数据
    if not years is None:
        start_date=df.index[-1].date()-timedelta(365*years)
        df=df[df.index>=str(start_date)]  

    # 按照天数取数据
    if not days is None:
        start_date=df.index[-1].date()-timedelta(days+1)
        df=df[df.index>=str(start_date)]  

    # 无数据返回Nan
    if len(df)==0:
        return float(np.NaN)

    #前一日收盘价
    df['pre']=df.iloc[:,0].shift(1)
    # 清除无效数据
    df=df.dropna()
    # 日收益率(当日收盘价/前一日收盘价，然后取对数)
    df['day_volatility']=np.log(df['pre']/df.iloc[:,0])
    # 波动率（年化收益率的方差*sqrt(250)）
    volatility=df['day_volatility'].std()*math.sqrt(250.0)*100

    # 返回值
    return round(volatility,2) 


def get_annualized(df,years=5): 
    """
    年化回报率
    df：数据表，df
    years：以年为单位的时段，int
    返回：回报率，float
    """
    # 按照年取数据
    if not years is None:
        start_date=df.index[-1].date()-timedelta(365*years)
        df=df[df.index>=str(start_date)]
    try:
        # 总收益率
        annualized=(df.iloc[:,0][-1]-df.iloc[:,0][0])/df.iloc[:,0][0]
        # 年化收益率
        annualized=(pow(1+annualized,250/(years*250.0))-1)*100
    except:
        annualized=float(np.NaN) 
    # 返回报率
    return round(annualized,2)        


def get_divid(code,end_date):
    """
    指定日期股息率,jy版本
    code：股票代码,list or str
    end_date：截至日期
    返回：股息率、市值
    """
    # 判断代码是str还是list
    if not type(code) is list:
        code=[code]

    #聚宽代码转换为jy内部代码    
    InnerCodes=Code.stk_to_jy(code)
    #获取所有成份股派息总额
    #数据表    
    df=pd.DataFrame()
    #因jy每次最多返回3000条数据，所以要多次查询
    #偏移值
    offset=0    
    while True:
        #查询语句
        q=query(
            #内部代码
            jy.LC_Dividend.InnerCode,
            #派息日期
            jy.LC_Dividend.ToAccountDate,
            #派息总额
            jy.LC_Dividend.TotalCashDiviComRMB,
        ).filter(
            # 已分红
            jy.LC_Dividend.IfDividend==1,
            # 获取指定日期前所有分红
            jy.LC_Dividend.ToAccountDate<=end_date,
            jy.LC_Dividend.InnerCode.in_(InnerCodes)
        #偏移         
        ).offset(offset)
        #查询    
        temp_df=jy.run_query(q)  
        if len(temp_df)==0:
            break
        #追加数据
        df=df.append(temp_df)
        #偏移值每次递增3000    
        offset+=3000

    if len(df)==0:
        div=float('NaN')
    else:
        # 生成排序字段  
        df['sort']=df['InnerCode'].astype('str')+df['ToAccountDate'].astype('str').str[0:10]
        df=df.sort('sort') 
        # 只保留最后一次派息数据
        df=df.drop_duplicates('InnerCode',take_last=True) #keep='last'
        # 返回合计的派息数
        div=df['TotalCashDiviComRMB'].sum()

    #获取指数总市值 
    q=query(
        #市值
        valuation.market_cap
    ).filter(
        valuation.code.in_(code)
    )
    #获取各成份股市值(亿元)
    df=get_fundamentals(q,end_date)
    #返回合计的成份股总市值（亿元）
    cap=df['market_cap'].sum()

    try:
        #返回股息率
        return div/cap/100000000*100.0,cap
    except:
        return float('NaN'),float('NaN')

        
#对源数据按照周、月、年筛选 
#period：D、W、M分别为日线、周线、月线
def data_to_period(df,period='W'):
    df['date']=df.index
    df=df.resample(period,how='last')
    df.index=df['date']
    del df['date']
    df=df.dropna()
    df.index.name=None
    return df    


#四分位去除负值、极值
def data_del_IQR(p,k=0.5):
    #去除负值
    x=np.array(p[p>0])
    #排序
    x=np.sort(x)
    #取中值
    m=np.median(x)
    #按照m分为两个数据表
    #取小于m的数据表中值
    q1=np.median(x[x<=m])
    #取大于m的数据表中值
    q3=np.median(x[x>m])
    #计算上下临界值
    d=q1-k*(q3-q1)
    u=q3+k*(q3-q1) 
    #取大于d小于u且大于0的数据，并去除空值
    return p[(p>d)&(p<u)&(p>0)].dropna()


#四分位填充极值
def data_fill_IQR(p,k=0.734):
    x=np.array(p)
    x=np.sort(x)
    m=np.median(x)
    q1=np.median(x[x<=m])
    q3=np.median(x[x>m])
    d=q1-k*(q3-q1)
    u=q3+k*(q3-q1)
    p[p<=d]=d
    p[p>=u]=u
    return p




# 日期转换成时间戳
def date_to_timestamp(date):
    return int(time.mktime(time.strptime(date,'%Y-%m-%d')))


# 时间戳转换成日期
def timestamp_to_date(timestamp):
    return time.strftime('%Y-%m-%d',time.localtime(timestamp))



class Code(object):
    
    @classmethod
    def __secu_to_jq(cls,code):
        if code.endswith('SH'):
            return code.replace('SH','XSHG')
        if code.endswith('SZ'):
            return code.replace('SZ','XSHE')
        
    @classmethod
    def __jq_to_secu(cls,code):
        if code.endswith('XSHG'):
            return code.replace('XSHG','SH')
        if code.endswith('XSHE'):
            return code.replace('XSHE','SZ')
        
    @classmethod
    def secu_to_jq(cls,code):
        if type(code) is str:
            return cls.__secu_to_jq(code)
        elif type(code) is list:
            return [cls.__secu_to_jq(item) for item in code]
        
    @classmethod
    def jq_to_secu(cls,code):
        if type(code) is str:
            return cls.__jq_to_secu(code)
        elif type(code) is list:
            return [cls.__jq_to_secu(item) for item in code]

    @classmethod        
    def __secu_to_jy(cls,codes,category=1):      
        df=pd.DataFrame()
        #因jy每次最多返回3000条数据，所以要多次查询
        #偏移值
        offset=0    
        while True:
            q=query(
                #内部代码
                jy.SecuMain.InnerCode,
            ).filter(
                #去除聚宽代码后缀
                jy.SecuMain.SecuCode.in_(codes),
                #限定查询股票
                jy.SecuMain.SecuCategory==category
                #偏移         
            ).offset(offset)
            #查询    
            temp_df=jy.run_query(q)  
            #无数据时退出
            if len(temp_df)==0:
                break
            #追加数据
            df=df.append(temp_df)
            #偏移值每次递增3000    
            offset+=3000    
        #返回代码list
        return df.InnerCode.tolist()    
    
    @classmethod        
    def idx_to_jy(cls,code):
        if type(code) is str:
            return cls.__secu_to_jy([code[0:6]],category=4)[0]
        elif type(code) is list:
            return cls.__secu_to_jy([item[0:6] for item in code],category=4)
        
    @classmethod        
    def stk_to_jy(cls,code):
        if type(code) is str:
            return cls.__secu_to_jy([code[0:6]],category=1)[0]
        elif type(code) is list:
            return cls.__secu_to_jy([item[0:6] for item in code],category=1)
                