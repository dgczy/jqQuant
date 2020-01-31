# -*- coding: utf-8 -*-


"""
investing网站历史行情数据
网站：
https://tvc-cncdn.investing.com'
网址：
https://tvc4.forexpros.com/a5cb6ed3c0b48d5dc77f0991b1717479/1531986161/6/6/28/history?symbol=29227&resolution=D&
from=1527782400&to=1528387200
返回数据格式：
{u'c': [3.6480000019073, 3.6670000553131, 3.683000087738, 3.6930000782013, 3.6930000782013], u'h': [3.6659998893738,
3.6800000667572, 3.6930000782013, 3.7000000476837, 3.7070000171661], u'l': [3.6480000019073, 3.6500000953674, 
3.6730000972748, 3.6779999732971, 3.6800000667572], u'o': [3.6659998893738, 3.6800000667572, 3.6800000667572, 
3.6979999542236, 3.6970000267029], u'vo': [u'n/a', u'n/a', u'n/a', u'n/a', u'n/a'], u's': u'ok', u't': [1527811200, 
1528070400, 1528156800, 1528243200, 1528329600], u'v': [u'n/a', u'n/a', u'n/a', u'n/a', u'n/a']}
无数据返回：
{u'nextTime': 1527724800, u's': u'no_data'}
通过判断's'状态，获悉有无数据
"""


#导入库
import pandas as pd
import numpy as np
import time
import requests
import json
from datetime import timedelta,date,datetime

#代码对照
_codes={
    'HSI':'HK50', #恒生指数
    'HSCEI':'HKHSCEI', #恒生国企指数   
    'DJI':'DJI', #道琼斯指数
    'SPX':'US500', #标普500指数
    'NDAQ':'IXIC', #纳斯达克综合指数
    'GDAXI':'DE30', #德国DAX30
    'FTSE':'UK100', #英国富时100
    'FCHI':'F40', #法国CAC40
    'SX5E':'STOXX50', #欧洲斯托克50
    'N225':'JP225', #日经225
    'C10Y':'CN10YT',#中国10年期国债
    'SPSIOP':'SPSIOPTR',#标普石油天然气指数
    'WTIUSD':'1043109',#WTI原油
    'USTEC100':'8874',#纳斯达克100指数期货
    }

#日期转换成时间戳
def date_to_timestamp(date):
    return int(time.mktime(time.strptime(date,'%Y-%m-%d')))

#时间戳转换成日期
def timestamp_to_date(timestamp):
    return time.strftime('%Y-%m-%d',time.localtime(timestamp))

class Invest(object):    
    
    #页面头
    @staticmethod
    def hist_price(code,start_date=None,end_date=None,period='D'): 
        # 代码转换
        code=_codes[code]
        
        # 参数约束
        if start_date is None:
            start_date='1900-01-01'
        if end_date is None:
            end_date=datetime.now().date().strftime('%Y-%m-%d')
        if not period in ['D','W','M']:    
            period='D'
            
        # 创建session
        session=requests.session()
        user_agent='Mozilla/5.0 (Windows NT 10.0; WOW64) AppleWebKit/537.36 \
    (KHTML, like Gecko) Chrome/45.0.2454.101 Safari/537.36'
        session.headers.update({'User-Agent':user_agent})
        session.get('https://tvc-cncdn.investing.com')
        
        # url
        url='https://tvc4.forexpros.com/a5cb6ed3c0b48d5dc77f0991b1717479/1531986161/6/6/28/history?\
    symbol=%s&resolution=%s&from=%s&to=%s'%(code,period,date_to_timestamp(start_date),date_to_timestamp(end_date))
        # 请求数据
        response=session.get(url)
        if not response.ok:
            return None
        
        # 解析数据
        data=json.loads(response.text)
        # 判断是否有数据
        if not data.get('s') =='ok':
            return None
        
        # 生成数据表
        df=pd.DataFrame(data={'close':data.get('c'),'high':data.get('h'),'low':data.get('l'),'open':data.get('o')})
        # 转换日期格式
        df.index=pd.to_datetime(map(lambda x:timestamp_to_date(x),data.get('t')),format='%Y-%m-%d')
        # 保留2位小数位
        #df=np.round(df,2)
        
        # 返回数据
        return df