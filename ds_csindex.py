# -*- coding: utf-8 -*-


#获取中证指数官网数据


#导入库
import numpy as np
import pandas as pd
import requests
from bs4 import BeautifulSoup
from datetime import timedelta,date,time,datetime
from jqdata import get_trade_days


_url_base='http://www.csindex.com.cn/zh-CN/downloads/industry-price-earnings-ratio?'

_codes={'SHA':{'name':'上海A股','position':1},
        'SZA':{'name':'深圳A股','position':9},
        'HSA':{'name':'沪深A股','position':17},
        'SZB':{'name':'深市主板','position':25},
        'ZXB':{'name':'中小板','position':33},
        'CYB':{'name':'创业板','position':41},
       }

_start_date='2011-05-02'
    
class Plate(object):
    """
    获取中证官网板块市盈率数据
    数据开始日期为2011-05-02
    板块分为：上海A股、深圳A股、沪深A股、深市主板、中小板、创业板
    url，如：http://www.csindex.com.cn/zh-CN/downloads/industry-price-earnings-ratio?date=2014-01-01&type=zy2
    其中date为日期，zy2/zy3/zy4依次表示板块滚动市盈率、板块市净率、板块股息率页面
    返回的是网页源文件
    板块滚动市盈率,包括：最新滚动市盈率、股票家数、其中亏损家数、平均滚动市盈率
    板块市净率,包括：最新市净率、股票家数、其中亏损家数、平均市净率
    板块股息率,包括：最新股息率、股票家数、其中亏损家数、平均滚动股息率
    """
    @staticmethod
    def hist_data(code,start_date=None,end_date=None): 
        # 参数检查
        today_str=(datetime.now().date()-timedelta(1)).strftime('%Y-%m-%d')
        if start_date is None or start_date<_start_date:
            start_date=_start_date
        if end_date is None or end_date<_start_date or end_date>today_str:
            end_date=today_str  
        # 交易日
        trade_days=get_trade_days(start_date=start_date,end_date=end_date)
        col=_codes[code].get('position')
        name=_codes[code].get('name')
        def data_list():
            for day in trade_days:
                datas=[]
                for page in [2,3,4]:
                    #链接
                    url='%stype=zy%s&date=%s'%(_url_base,page,day) 
                    #页面请求
                    content=requests.get(url).text  
                    soup=BeautifulSoup(content,'html.parser')
                    data=soup.select('tbody[class="tc"] td')
                    if len(data)==0:
                        break
                    datas.append(data[col].get_text())
                print '\r数据更新：板块%s %s %s '%(code,name,day),  
                yield [day]+datas

        # 组织数据（迭代数据生成器）
        df=pd.DataFrame(data=[item for item in data_list()],columns=['date','pe','pb','dyr'])   
        df.set_index('date',inplace=True)
        df.index.name=None
        df.index=pd.to_datetime(df.index,format='%Y-%m-%d')   
        return  df.astype('float')