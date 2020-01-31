# -*- coding:utf-8 -*-

try:
    # 策略中必须导入kuanke.user_space_api包
    from kuanke.user_space_api import *
except:
    pass


# 日期时间
from datetime import timedelta,date,datetime

# 聚宽数据
from jqdata import *

# 各类数据源
from ds_hsi import Hsi
from ds_wall import Wall
from ds_xueqiu import Xueqiu
from ds_multpl import Spx
from ds_sws import Sws
from ds_sina import Sina
from ds_east import Ced,Shibor
from ds_csindex import Plate

    
class _TInfo(object):
    """
    数据源信息
    name：中文简称，str
    start_date：成立日期，str
    """
    def __init__(self,name,start_date,data_type):
        self.name=name
        self.start_date=start_date
        self.data_type=data_type

        
class _TData(object): 
    """
    数据源基类
    """
    
    #代码
    _codes={}
    
    @classmethod
    def in_codes(cls,code):
        # 判断代码是否适配
        return code in cls._codes 


class _CMI(_TData):
    """
    A股指数数据源
    """
    
    @classmethod
    def __convert_code(cls,code):
        # 代码转换
        if code.endswith('SH'):
            return code.replace('SH','XSHG')
        if code.endswith('SZ'):
            return code.replace('SZ','XSHE')
        else:
            return code
  
    @staticmethod
    def in_codes(code):
        return code.endswith('SZ') or code.endswith('SH') or code.endswith('XSHG') or code.endswith('XSHE')
    
    @classmethod
    def hist(cls,code,start_date=None,end_date=None,fields=None,period='D'):
        # 日期检查
        if end_date is None:
            # 今天日期
            end_date=datetime.now().date().strftime('%Y-%m-%d')
        # 历史行情（聚宽数据）    
        return get_price(cls.__convert_code(code),start_date=start_date,end_date=end_date,frequency='daily',fields=fields)
        
    @classmethod
    def info(cls,code):
        # 信息（聚宽数据）
        infos=get_security_info(cls.__convert_code(code))
        return _TInfo(infos.display_name,infos.start_date.strftime('%Y-%m-%d'),infos.type)
    
    @classmethod
    def stocks(cls,code,end_date=None):
        # 成份股（聚宽数据）
        return get_index_stocks(cls.__convert_code(code),date=end_date)
   
    
class _CMS(_TData):
    """
    A股股票、场内基金数据源
    """
    
    @classmethod
    def __convert_code(cls,code):
        # 代码转换
        if code.endswith('SH'):
            return code.replace('SH','XSHG')
        if code.endswith('SZ'):
            return code.replace('SZ','XSHE')
        else:
            return code
  
    @staticmethod
    def in_codes(code):
        return code.endswith('SZ') or code.endswith('SH') or code.endswith('XSHG') or code.endswith('XSHE')
    
    @classmethod
    def hist(cls,code,start_date=None,end_date=None,fields=None,period='D'):
        # 日期检查
        if end_date is None:
            # 今天日期
            end_date=datetime.now().date().strftime('%Y-%m-%d')
        # 历史行情（聚宽数据）    
        return get_price(cls.__convert_code(code),start_date=start_date,end_date=end_date,frequency='daily',fields=fields)
        
    @classmethod
    def info(cls,code):
        # 信息（聚宽数据）
        infos=get_security_info(cls.__convert_code(code))
        return _TInfo(infos.display_name,infos.start_date.strftime('%Y-%m-%d'),infos.type)    

               
class _CMO(_TData):
    """
    A股场外基金数据源
    """
    @staticmethod
    def in_codes(code):
        return code.endswith('OF')
    
    @staticmethod
    def hist(code,start_date=None,end_date=None,fields=None,period='D'):
        # 基金净值（聚宽数据）
        df=get_extras('unit_net_value',code,start_date=start_date,end_date=end_date)  
        # 更改列名
        df.columns=['close']
        return df
        
    @classmethod
    def info(cls,code):
        # 基金信息（聚宽数据）
        infos=get_security_info(code)
        return _TInfo(infos.name,infos.start_date.strftime('%Y-%m-%d'),infos.type) 
    
        
        
class _CMU(_TData):
    """
    申万指数数据源
    """
    @staticmethod
    def in_codes(code):
        return code in Sws.sw1_codes
    
    @staticmethod
    def hist(code,start_date=None,end_date=None,fields=None,period='D'):
        # 申万行业数据（申万官网）
        return Sws.hist_data(code,start_date,end_date,period)
        
    @classmethod
    def info(cls,code):
        # 申万行业信息（聚宽）
        infos=get_industries(name='sw_l1')
        return _TInfo(infos.at[code,'name'],infos.at[code,'start_date'].strftime('%Y-%m-%d'),'industry')    
    
    @staticmethod
    def stocks(code,end_date=None):
        # 申万行业成份股（聚宽）
        return get_industry_stocks(code,date=end_date)       

    
class _HMI(_TData):
    """
    港股指数数据源
    """
    _codes={
        'HSI':{'name':u'恒生指数','start_date':'1964-07-31','stock_count':500,},
        'HSCEI':{'name':'恒生国企','start_date':'2000-01-03','stock_count':500,}, 
        }
    
    @staticmethod
    def hist(code,start_date=None,end_date=None,fields=None,period='D'):
        # 雪球官网数据
        df=Xueqiu.hist_price(code,start_date) 
        if df is None :
            return None
        # 恒生官网数据
        pe_df=Hsi.hist_data(code,'pe')  
        dyr_df=Hsi.hist_data(code,'dyr')
        if not pe_df is None:
            df['pe_e']=pe_df.resample('D',fill_method='ffill')
        if not dyr_df is None:
            df['dyr']=dyr_df.resample('D',fill_method='ffill')
        return df.fillna(method='bfill').fillna(method='ffill')
        
    @classmethod
    def info(cls,code):
        return _TInfo(cls._codes[code].get('name'),cls._codes[code].get('start_date'),'index') 
    
    @staticmethod
    def stocks(code,end_date=None):
        # 恒生官网数据
        return Hsi.stocks(code)


class _SPX(_TData):
    """
    标普500数据源
    """
    _codes={
        # 美股指数      
        'SPX':{'name':u'标普500','start_date':'1871-01-01','stock_count':500,},
        }
    
    @staticmethod
    def hist(code,start_date=None,end_date=None,fields=None,period='D'):
        # price（雪球官网数据）
        df=Xueqiu.hist_price(code,start_date) 
        if df is None :
            return None
        # pe（multpl网站月线数据）
        pe_df=Spx.hist_data('pe',start_date) 
        # dyr（multpl网站月线数据）
        dyr_df=Spx.hist_data('dyr',start_date)
        if not pe_df is None:
            # pe按照日线重新采样，合并到price
            df['pe_e']=pe_df.resample('D',fill_method='ffill')
        if not dyr_df is None:
            # dyr按照日线重新采样，合并到price
            df['dyr']=dyr_df.resample('D',fill_method='ffill')
        # 缺失值，按照bfill填充
        return df.fillna(method='bfill').fillna(method='ffill')
   
    @classmethod
    def info(cls,code):
        return _TInfo(cls._codes[code].get('name'),cls._codes[code].get('start_date'),'index')    
 
    @classmethod
    def stocks(cls,code,end_date=None):
        return [None for i in range(cls._codes[code].get('stock_count'))]   
    
    
class _OMI(_TData):
    """
    海外指数数据源
    """
    _codes={
        # 美股指数  
        'DJIA':{'name':u'道琼斯','start_date':'1998-01-20','stock_count':30,},
        'NDAQ':{'name':u'纳斯达克','start_date':'2005-02-09','stock_count':3258,},
        # 欧洲 
        'GDAXI':{'name':u'德国DAX','start_date':'1871-01-01','stock_count':30,},
        'FTSE':{'name':u'英国富时100','start_date':'1871-01-01','stock_count':100,},
        'FCHI':{'name':u'法国CAC40','start_date':'1871-01-01','stock_count':40,},
        'SX5E':{'name':u'欧洲斯托克50','start_date':'1871-01-01','stock_count':50,},
        # 亚洲
        'N225':{'name':u'日经225','start_date':'1871-01-01','stock_count':225,},
        }
    
    @staticmethod
    def hist(code,start_date=None,end_date=None,fields=None,period='D'):
        # 华尔街见闻网站数据
        try:
            return Wall.hist_price(code,start_date,end_date)   
        except Exception as e:
            print '%s：%s'%("华尔街见闻网站数据",e)
            return None
        
    @classmethod
    def info(cls,code):
        return _TInfo(cls._codes[code].get('name'),cls._codes[code].get('start_date'),'index')    
 
    @classmethod
    def stocks(cls,code,end_date=None):
        return [None for i in range(cls._codes[code].get('stock_count'))]  

    
class _MCD(_TData):
    """
    中国经济指标数据源
    """
    _codes={
        'CPI':'居民消费价格指数',
        'PPI':'工业品出厂价格指数',
        'PMI':'采购经理人指数',
        'MS':'货币供应量',
        'NFC':'新增信贷数据',
        'GDP':'国内生产总值',
        'SCN':'股票账户新开',
        }
    
    @staticmethod
    def hist(code,start_date=None,end_date=None,fields=None,period='D'):
        # 东方财富网数据
        return Ced.hist_data(code,start_date,end_date)  
        
    @classmethod
    def info(cls,code):
        return _TInfo(cls._codes[code],None,'macro') 

    
class _MCR(_TData):
    """
    宏观指标数据源
    """
    _codes={
        'UDI':u'美元指数',
        'VIX':u'VIX波动率',
        'BDI':u'波罗的海干散货指数',
        'C10Y':u'中国十年期国债',
        'C5Y':u'中国五年期国债',
        'U10Y':u'美国十年期国债',
        'U5Y':u'美国五年期国债',
        'UCH':'离岸人民币',
        'UCY':'在岸人民币',
        }
    
    @staticmethod
    def hist(code,start_date=None,end_date=None,fields=None,period='D'):
        # 华尔街见闻网站数据
        try: 
            return Wall.hist_price(code,start_date,end_date)  
        except Exception as e:
            print '%s：%s'%("华尔街见闻网站数据",e)
            return None
            
    @classmethod
    def info(cls,code):
        return _TInfo(cls._codes[code],None,'macro') 

    
    
class _SHI(_TData):
    """
    上海银行同行业拆借利率
    """
    _codes={
        'SHIBOR':u'上海银行同行业拆借利率',
        }
    
    @staticmethod
    def hist(code,start_date=None,end_date=None,fields=None,period='D'):
        # 东方财富网数据
        return Shibor.hist_data(start_date,end_date)  
        
    @classmethod
    def info(cls,code):
        return _TInfo(cls._codes[code],None,'macro') 
    
    
class _CMM(_TData):
    """
    大宗商品数据源
    """   
    _codes={
        'GC':u'comex黄金',
        'SI':u'comex白银',
        'XAU':u'伦敦金',
        'XAG':u'伦敦银',
        'CL':u'NYMEX原油',
        'OIL':u'布伦特原油'
        }
    
    @staticmethod
    def hist(code,start_date=None,end_date=None,fields=None,period='D'):  
        # 新浪网财经数据
        return Sina.hist_price(code,start_date,end_date)   
    
    @classmethod
    def info(cls,code):
        return _TInfo(cls._codes[code],None,'commodity')  
    
    
    
class _CBK(_TData):
    """
    中证官网板块数据源
    """   
    _codes={
        'SHA':'上海A股',
        'SZA':'深圳A股',
        'HSA':'沪深A股',
        'SZB':'深市主板',
        'ZXB':'中小板',
        'CYB':'创业板',
       }
    
    @staticmethod
    def hist(code,start_date=None,end_date=None,fields=None,period='D'):  
    # 中证官网数据
        return Plate.hist_data(code,start_date,end_date)   
    
    @classmethod
    def info(cls,code):
        return _TInfo(cls._codes[code],None,'plate')    

    
    
#########################################################################################################
# 数据分类接口
#########################################################################################################    
 
    
# 指数    
class dsIdx(object): 
    """
    指数数据源
    """
    @staticmethod
    def hist(code,start_date=None,end_date=None,fields=None,period='D'):
        for data in [_CMI,_HMI,_SPX,_OMI]:
            if data.in_codes(code):
                return data.hist(code,start_date,end_date,fields) 
        
    @staticmethod
    def info(code): 
        for data in [_CMI,_CMS,_HMI,_SPX,_OMI]:
            if data.in_codes(code):
                return data.info(code) 

    @staticmethod
    def stocks(code,end_date=None): 
        for data in [_CMI,_CMS,_HMI,_SPX,_OMI]:
            if data.in_codes(code):
                return data.stocks(code,end_date)
             

# 宏观指标
class dsMcr(object): 
    """
    宏观经济指标数据源
    """  
    @staticmethod
    def hist(code,start_date=None,end_date=None,fields=None,period='D'):
        for data in [_MCR,_MCD,_SHI]:
            if data.in_codes(code):
                return data.hist(code,start_date,end_date,fields) 
        
    @staticmethod
    def info(code): 
        for data in [_MCR,_MCD,_SHI]:
            if data.in_codes(code):
                return data.info(code) 

            
# 基金（场内基金、场外基金）
class dsFnd(object): 
    """
    基金数据源（含场内、场外）
    """  
    @staticmethod
    def hist(code,start_date=None,end_date=None,fields=None,period='D'):
        for data in [_CMS,_CMO]:
            if data.in_codes(code):
                return data.hist(code,start_date,end_date,fields) 
        
    @staticmethod
    def info(code): 
        for data in [_CMS,_CMO]:
            if data.in_codes(code):
                return data.info(code) 
            
# 商品            
dsCmm=_CMM  

# 板块
dsPlt=_CBK 

# 行业
dsIdu=_CMU

# 股票
dsStk=_CMS
   
    
#########################################################################################################
# 数据通用接口
#########################################################################################################    
 

class dsData(object): 
    """
    数据源通用数据接口
    """
            
    @staticmethod
    def hist(code,start_date=None,end_date=None,fields=None,period='D'):
        """
        历史行情
        """
        for data in [_CMI,_CMS,_CMO,_HMI,_SPX,_OMI,_CMM,_CMU,_CMO,_MCR,_MCD,_SHI,_CBK]:
            if data.in_codes(code):
                return data.hist(code,start_date,end_date,fields) 
        
    @staticmethod
    def info(code): 
        """
        信息
        """
        for data in [_CMI,_CMS,_CMO,_HMI,_SPX,_OMI,_CMM,_CMU,_CMO,_MCR,_MCD,_SHI,_CBK]:
            if data.in_codes(code):
                return data.info(code) 

    @staticmethod
    def stocks(code,end_date=None): 
        """
        成份股
        """
        for data in [_CMI,_CMS,_CMO,_HMI,_SPX,_OMI,_CMM,_CMU,_CMO,_MCR,_MCD,_SHI,_CBK]:
            if data.in_codes(code):
                return data.stocks(code,end_date)
            
            