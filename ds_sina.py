# -*- coding: utf-8 -*-

#爬取新浪实时数据

#到入库
import pandas as pd
import numpy as np
import requests
import json
import re
from datetime import timedelta,date,time,datetime

_codes_real=[
    
    #沪深指数（实时价格）
    's_sh000001',#上证指数
    's_sz399001',#深证成指
    's_sh000300',#沪深300

    #香港指数（实时价格）
    'r_HSI',  #恒生指数
    'r_HSCEI',#国企指数
    'r_HSCCI',#红筹指数
    
    #美国指数（实时价格）
    'int_dji',#道琼斯
    'int_nasdaq',#纳斯达克
    'int_sp500',#标普500

    #其它国家指数（实时价格）
    'b_DAX',#德国DAX30
    'b_UKX',#富时100指数
    'b_INDEXCF',#俄罗斯MICEX指数
    'b_CAC',#法国CAC40指数
    'b_SMI',#瑞士市场指数
    'b_FTSEMIB',#富时意大利MIB指数
    'b_MADX',#西班牙MA马德里指数
    'b_OMX',#OMX斯德哥尔摩30指数
    'b_HEX',#OMX赫尔辛基指数
    'b_OSEAX',#挪威OSE全股指数
    'b_ISEQ',#爱尔兰综合指数
    'b_AEX',#荷兰AEX指数
    'b_IBEX',#西班牙IBEX 35指数
    'b_SX5E',#道琼斯欧元区斯托克50指数
    'b_XU100',#土耳其 ISE National-100指数
    'b_NKY',#日经225指数
    'b_HSI',#香港恒生指数
    'b_TWSE',#台湾台北指数
    'b_FSSTI',#富时新加坡海峡时报指数
    'b_KOSPI',#韩国KOSPI指数
    'b_FBMKLCI',#吉隆坡综合股价指数
    'b_SET',#S泰国股票交易指数
    'b_JCI',#印尼雅加达综合指数
    'b_PCOMP',#菲律宾综合股价指数
    'b_KSE100',#巴基斯坦卡拉奇100指数
    'b_VNINDEX',#越南胡志明市股票指数
    'b_CSEALL',#斯里兰卡科伦坡指数
    'b_SASEIDX',#沙特阿拉伯TADAWUL股票综合指数
    'b_INDU',#道琼斯30种工业股票平均价格指数
    'b_CCMP',#纳斯达克综合指数
    'b_SPX',#标准普尔500指数
    'b_SPTSX',#S&P/TSX综合指数
    'b_MEXBOL',#墨西哥BOLSA指数
    'b_IBOV',#巴西BOVESPA股票指数;
    'b_MERVAL',#阿根廷MERVAL指数
    'b_NZSE50FG',#新西兰50指数
    'b_CASE',#埃及CASE 30指数
    'b_JALSH',#FTSE/JSE 南非综合指数

    #商品代码（实时价格）
    'hf_GC',#COMEX黄金
    'hf_OIL',#布伦特原油
    'hf_SI',#COMEX白银
    'hf_GC',#COMEX黄金
    'hf_CL',#NYMEX原油
    'hf_S',#CBOT黄豆
    'hf_C',#玉米
    'hf_TRB',#日本橡胶
    'hf_CAD',#LME铜
    'hf_ZSD',#LME锌
    'hf_AHD',#LME铝
    ]

#商品历史数据代码
_codes_hist={
    "GC",#comex黄金
    "SI",#comex白银
    "XAU",#伦敦金
    "XAG",#伦敦银
    "CL",#NYMEX原油
    "OIL",#布伦特原油
    }

class Sina(object):  

    #从sina获取历史
    @staticmethod
    def hist_price(item,start_date=None,end_date=None):   
        
        # 今天日期
        today_str=datetime.now().date().strftime('%Y-%m-%d')

        # 约束开始日期
        if start_date>today_str:
            return None
            
        # 约束结束日期
        if end_date is None or end_date>today_str:
        # 今天日期
            end_date=today_str
        
        #url链接
        url="http://stock2.finance.sina.com.cn/futures/api/json.php/\
GlobalFuturesService.getGlobalFuturesDailyKLine?symbol=%s"%(item)
        #网络请求数据
        ret=requests.get(url).text 
        #预处理数据
        data=ret.replace('date', '"date"').replace('open', '"open"').replace('high', '"high"')\
.replace('low', '"low"').replace('close', '"close"').replace('volume', '"volume"')  
        #整理数据
        df=pd.DataFrame(json.loads(data))
        df['date']=pd.to_datetime(df['date'],format='%Y-%m-%d')
        df.set_index('date',inplace=True)
        df.index.name=None
        
        if start_date is None:
            start_date=df.index[0].date().strftime('%Y-%m-%d')
            
        #保存到cvs文件
        return df[(df.index>=start_date) & (df.index<=end_date)].astype('float')  
    
    
    #数据实时价格
    #item_list：代码列表，可一次返回多格代码的数据
    @staticmethod
    def __real_price(item_list,position=1):  
        url_base="http://hq.sinajs.cn/list="
        #list转换为字符串
        item=str(item_list).replace("'",'').replace('[','').replace(']','').replace(' ','')
        #拼接url
        url=url_base+item
        #网络请求数据
        data=requests.get(url).text   
        #数据list
        data_list=[] 
        temp_list=[]
        #去除多余的字符
        data=re.sub(r'[a-z_=A-Z]',r'',data)
        #分行
        temp_list=data.replace('"','').replace(' ','').split(';\n')
        #遍历列表
        for data in temp_list[0:len(temp_list)-1]: 
            #取position位置的数据（指数=1，商品=0）
            data_list.append(data.split(',')[position])   
        #转换成代码/数据字典    
        return dict(zip(item_list,data_list))


    #商品实时价格
    @staticmethod
    def cmm_real_price(codes): 
        data=Sina.__real_price(codes,0)
        return data

    #指数实时价格
    @staticmethod
    def idx_real_price(codes): 
        data=Sina.__real_price(codes,1)
        return data
