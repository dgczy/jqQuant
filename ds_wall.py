# -*- coding: utf-8 -*-


#华尔街见闻网站行情数据

#通用模块
import numpy as np
import pandas as pd
import json
import requests
import time  
from datetime import timedelta,date,datetime
from tl import date_to_timestamp,timestamp_to_date

"""
代码对照


CHINA10YEAR 中国10年期国债
CHINA5YEAR  中国5年期国债
CHINA2YEA  中国2年期国债
US10YEAR  美国10年期国债
US5YEAR  美国5年期国债
US2YEAR  美国2年期国债

USDOLLARINDEX  美元指数
USDCNH  离岸人民币
USDCNY  在岸人民币
USDJPY  美元/日元
BTCUSD  比特币兑美元

XAUUSD  黄金
UKOIL  布伦特原油
XAGUSD 白银

HKG33INDEX  恒生指数
SPX500INDEX  标普500
US30INDEX   道琼斯
NASINDEX  纳斯达克
NAS100INDEX  纳斯达克100
GER30INDEX  德国DAX
JPN225INDEX  日经225指数
UK100INDEX  英国富时100
FRA40INDEX  法国CAC40
EUSTX50INDEX  欧洲Stoxx50
STOXX600  欧洲Stoxx600
SP500VIXINDEX  VIX波动率指数

BDIINDEX  波罗的海干散货指数
ESP35INDEX  西班牙IBEX35
AUS200INDEX  澳大利亚ASX200
KOSPIINDEX  韩国成份指数
MICEXINDEX  俄罗斯MICEX指数
BSESENSEX30INDEX  印度孟买SENSEX指数
BOVESPAINDEX  巴西BOVESPA股票指数
SPTSXCOMPOSITEINDEX  加拿大S&P/TSX综合指数
ATHENSGENERALINDEX  希腊综合股指
TADAWULALLSHAREINDEX  沙特阿拉伯综合指数
IPCINDEX  墨西哥BOLSA指数
JAKARTASTOCKEXCHANGECOMPOSITEINDEX  印尼雅加达综合指数
FTSEMALAYSIAKLCIINDEX  富时马来西亚KLCI综合指数
PSEICOMPOSITEINDEX  菲律宾PSE综合股价指数
"""

_codes={
    # 港股指数  
    'HSI':'HKG33INDEX',
    # 美股指数      
    'SPX':'SPX500INDEX',
    'DJIA':'US30INDEX',  
    'NDAQ':'NASINDEX',
    # 欧洲 指数  
    'GDAXI':'GER30INDEX', 
    'FTSE':'UK100INDEX',
    'FCHI':'FRA40INDEX',
    'SX5E':'EUSTX50INDEX',
    # 亚洲指数  
    'N225':'JPN225INDEX',
    # 指标
    'VIX':'SP500VIXINDEX',
    'BDI':'BDIINDEX',

    'UDI':u'USDOLLARINDEX',
    'VIX':u'SP500VIXINDEX',
    'BDI':u'BDIINDEX',
    'C10Y':u'CHINA10YEAR',
    'C5Y':u'CHINA5YEAR',
    'U10Y':u'US10YEAR',
    'U5Y':u'US5YEAR',
    'UCH':'USDCNH',
    'UCY':'USDCNY',
    'USCL':'USCL',#WTI原油
    'USTEC100F':'USTEC100F',#纳斯达克100指数期货
    
    }


class Wall(object):
    """
    获取华尔街见闻网站历史行情日线数据

    url格式：
    https://forexdata.wallstreetcn.com/kline?prod_code=CHINA10YEAR&candle_period=8&data_count=1&end_time=1522252800&
       fields=time_stamp,open_px,close_px,high_px,low_px
    返回的数据格式：
    {"code":200,"data":{"candle":{"CHINA10YEAR":[[1522191600,3.773,3.758,3.773,3.747]],
        "fields":["time_stamp","open_px","close_px","high_px","low_px"]}}}

    返回的数据不含当天的数据
    prod_code：代码
    candle_period：数据级别，8代表日线数据
    data_count：每次返回的数据量，网站限制每次最多返回1000条数据
    end_time：截至时间，网站返回的日期格式为时间戳，如1522191600
    """
    
    @staticmethod
    def hist_price(code,start_date=None,end_date=None,period='D'):  
        """
        获取历史行情数据，限制开始、结束时间版本
        code：代码，str
        start_date：开始日期，str，如：2018-07-01
        end_date：结束日期，str，如：2018-07-31
        period：数据线级别，str，分别为：'D'、'W'、'M'（日、周、月）
        """
                
        #今日日期
        today=datetime.now().date()
        today_str=today.strftime('%Y-%m-%d')
        
        # 约束开始日期
        if start_date>today_str:
            return None
        
        # 转换代码
        code=_codes[code]  
        
        # 约束开始日期
        if not start_date is None:
            # 转换日期为timestamp
            start_date=date_to_timestamp(start_date)
            
        # 结束日期
        if end_date is None:
            # 今日日期
            end_date=today_str
        else:
            # 日期+1天(否则取不到end_date当天的值)
            end_date=(datetime.strptime(end_date,'%Y-%m-%d')+timedelta(1)).strftime('%Y-%m-%d')         
        # 转换日期为timestamp
        end_date=date_to_timestamp(end_date)    
        
        # 每次取数据时的日期值
        end_time=end_date          
        # 转换数据线级别（# '1m':1,'5m':2,'15m':3,'30m':4,'1h':5,'4h':7,）
        period={'D':8,'W':10,'M':11}[period]
        # 默认每次获取的数据量（不能超过1000）
        data_count=1000

        df=pd.DataFrame()
        data_list=[]
        
        while True:

            # 生成url 
            url='https://forexdata.wallstreetcn.com/kline?prod_code={prod_code}\
&candle_period={candle_period}&data_count={data_count}&end_time={end_time}\
&fields=time_stamp%2Copen_px%2Cclose_px%2Chigh_px%2Clow_px'.format(prod_code=code,
                   candle_period=period,data_count=data_count,end_time=end_time)

            # 请求数据
            response=requests.get(url).text
            
            # 获取数据列表
            data=json.loads(response).get("data").get("candle").get(code)
           
            # 无数据退出
            if len(data)==0:
                break
                
            # 反转数据    
            data.reverse()

            # 查找指定日期范围内的数据
            b=False
            for item in data:
                if item[0]<=end_date:
                    if item[0]<start_date:
                        b=True
                        break
                    data_list.append(item)
            # 找到指定日期范围内的所有数据，退出        
            if b:
                break

            # 取得下一次的时间戳
            end_time=data[-1][0]

            # 延时
            time.sleep(0.0)
        

        # 无数据
        if len(data_list)==0:
            return None
        
        #组织数据
        df=pd.DataFrame(data_list,columns=['date','open','close','high','low'])
        
        # 时间戳转换为日期    
        df['date']=df['date'].apply(lambda x:timestamp_to_date(x))
        
        #去除重复数据（不知为何返回的数据有重复,必须按照日期删除重复）
        df=df.drop_duplicates(['date'])  
        
        # 重置索引
        df=df.set_index('date')
        df.index.name=None

        # 转换索引为日期格式
        df.index=pd.to_datetime(df.index,format='%Y-%m-%d')
        
        # 保留2位小数位
        # df=np.round(df,2)
        
        #返回数据（升序）
        return df.sort_index()   
     

    @staticmethod
    def real_price(code):  
        #url
        url='https://forexdata.wallstreetcn.com/real?en_prod_code={en_prod_code}&\
fields=last_px'.format(en_prod_code=code )

        #请求数据
        response=requests.get(url)
        #json解析 
        json_data=json.loads(response.text).get("data").get("snapshot")
        #转换为字典
        return {key:value[0] for key,value in json_data.items()}