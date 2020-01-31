# -*- coding: utf-8 -*-

#雪球网站历史行情数据

#返回数据格式

"""

{"stock":{"symbol":"HKHSI"},"success":"true","chartlist":[{"volume":0,"open":28617.0,"high":28617.0,"close":28545.57,"low":27990.45,"chg":-409.54,"percent":-1.41,"turnrate":0.0,"ma5":28647.132,"ma10":28999.612,"ma20":29972.953,"ma30":30201.684,"dif":-573.56,"dea":-414.77,"macd":-317.59,"lot_volume":0,"timestamp":1530547200000,"time":"Tue Jul 03 00:00:00 +0800 2018"},{"volume":0,"open":28546.32,"high":28642.34,"close":28241.67,"low":28141.28,"chg":-303.9,"percent":-1.06,"turnrate":0.0,"ma5":28519.186,"ma10":28876.964,"ma20":29835.138,"ma30":30108.142,"dif":-608.15,"dea":-453.42,"macd":-309.46,"lot_volume":0,"timestamp":1530633600000,"time":"Wed Jul 04 00:00:00 +0800 2018"},{"volume":0,"open":28101.85,"high":28320.9,"close":28182.09,"low":27830.75,"chg":-59.58,"percent":-0.21,"turnrate":0.0,"ma5":28484.352,"ma10":28725.556,"ma20":29689.57,"ma30":30006.4,"dif":-632.93,"dea":-489.12,"macd":-287.61,"lot_volume":0,"timestamp":1530720000000,"time":"Thu Jul 05 00:00:00 +0800 2018"},{"volume":0,"open":28254.37,"high":28554.21,"close":28315.62,"low":27925.33,"chg":133.53,"percent":0.47,"turnrate":0.0,"ma5":28448.012,"ma10":28627.513,"ma20":29542.396,"ma30":29928.066,"dif":-633.86,"dea":-517.11,"macd":-233.49,"lot_volume":0,"timestamp":1530806400000,"time":"Fri Jul 06 00:00:00 +0800 2018"}]}

"""



#导入库
from datetime import timedelta,date,datetime
import pandas as pd
import requests,json,os,re,time

#代码对照
_codes={
    'HSI':'HKHSI', #恒生指数
    'HSCEI':'HKHSCEI', #恒生国企指数   
    'DJI':'.DJI', #恒生国企指数   
    'SPX':'SP500', #标普500
    'NDAQ':'QQQ', #纳斯达克
    }

#日期转换成时间戳
def date_to_timestamp(date):
    return int(time.mktime(time.strptime(date,'%Y-%m-%d')))

#时间戳转换成日期
def timestamp_to_date(timestamp):
    return time.strftime('%Y-%m-%d',time.localtime(timestamp))

class Xueqiu(object):    
    
    #页面头
    @staticmethod
    def __init_xq():
        xueqiu_s=requests.session()
        user_agent='Mozilla/5.0 (Windows NT 10.0; WOW64) AppleWebKit/537.36 \
(KHTML, like Gecko) Chrome/45.0.2454.101 Safari/537.36'
        xueqiu_s.headers.update({'User-Agent':user_agent})
        xueqiu_s.headers.update({'X-Requested-With':'XMLHttpRequest'})
        xueqiu_s.get('https://xueqiu.com/')
        return xueqiu_s
    
    @staticmethod
    def hist_price(code,start_date=None,end_date=None,period='D'):    
        
        """
        获取历史行情数据，限制开始、结束时间版本
        code：代码，str
        start_date：开始日期，str，如：'2018-07-01'
        end_date：结束日期，str，如：'2018-07-31'
        period：暂不支持
        """
        # 今天日期
        today=datetime.now().date()
        today_str=today.strftime('%Y-%m-%d')
        
        # 约束开始日期
        if start_date>today_str:
            return None
        
        # 初始化
        xueqiu_s=Xueqiu.__init_xq()
        
        # 代码转换
        code=_codes[code]
    
        # 约束结束日期
        if end_date is None or end_date>=today_str:
            # 今天日期减一天（与其他数据源保持一致）
            end_date=(today-timedelta(1)).strftime('%Y-%m-%d')

        # url，拼接代码、日期（转换为时间戳，并*1000，以符合雪球时间戳标准）、当前时间
        url='https://xueqiu.com/stock/forchartk/stocklist.json?symbol=%s&period=1day&type=normal'%(code)
        if not start_date is None:
            url='%s&begin=%d'%(url,date_to_timestamp(start_date)*1000)
        if not end_date is None:
            url='%s&end=%s'%(url,date_to_timestamp(end_date)*1000)
        url='%s&_=%d'%(url,int(time.time()*1000))
        
        #获取数据
        response=xueqiu_s.get(url,timeout=5)
        # 判断返回标志
        if not response.ok:
            return None
        # 解析数据
        ret_data=response.json()['chartlist']
        # 无数据返回空列表
        if len(ret_data)==0:
            return None
        # 生成数据表
        df=pd.DataFrame(data=ret_data)[['timestamp','open','close','high','low']] 
        # 转换时间戳为标准日期格式
        df['timestamp']=df['timestamp'].apply(lambda x:timestamp_to_date(x/1000))
        # 重置索引
        df=df.set_index('timestamp')
        df.index.name=None
        # 转换格式
        df.index=pd.to_datetime(df.index)
        
        # 返回数据表
        return df
    
    
        
    #行情
    #code:sh000300
    #begin/end: 2016-09-01
    #days:指定最近天数
    @staticmethod
    def price(code,begin='',end='',days=0,timeout=5):        
        xueqiu_s=Xueqiu.__init_xq()

        code=_codes[code]
        begin=begin.replace('-','')
        end=end.replace('-','')
        if len(begin) > 0 and days > 0: #!!!不能同时指定begin和days!!!
            log.error('begin: %s, days: %d', begin, days)
            return None

        #url
        url='https://xueqiu.com/stock/forchartk/stocklist.json?symbol=%s&period=1day&type=normal'%(code)
        if len(begin) > 0:
            url='%s&begin=%d'%(url,int(time.mktime(datetime.strptime(begin,'%Y%m%d').timetuple())*1000))
        if len(end) > 0:
            url='%s&end=%s'%(url,int(time.mktime(datetime.strptime(end,'%Y%m%d').timetuple())*1000))
        if days > 0:
            url='%s&begin=%d'%(url,int(time.mktime((datetime.today()-timedelta(days)).timetuple())*1000))
        url='%s&_=%d'%(url,int(time.time()*1000))
        #获取网站数据
        r=xueqiu_s.get(url,timeout=timeout)
        if r.ok is False:
            return None
        #解析数据
        ret_data=r.json()
        #有效数据
        stock_data=ret_data['chartlist']
        #数据列表
        data_list=[]
        #日期列表
        day_list=[]
        for item in stock_data:
            #日期格式转换
            try:
                date=datetime.strptime(item['time'],"%a %b %d %H:%M:%S +0800 %Y")
            except:
                date=datetime.strptime(item['time'],"%a %b %d %H:%M:%S +0900 %Y")
            data_list.append([item['open'],item['close'],item['high'],item['low']])
            day_list.append(date)
        df=pd.DataFrame(data=data_list,index=day_list,columns=['open','close','high','low'])   
        return df