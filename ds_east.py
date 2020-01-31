# -*- coding: utf-8 -*-


#获取东方财富网数据中心数据


#导入库
import numpy as np
import pandas as pd
import requests
import re
from bs4 import BeautifulSoup
from datetime import timedelta,date,time,datetime

class Ced(object):
    
    # 数据信息
    __data_type_dict={
        'CPI':{'name':'居民消费价格指数',
               'code':'consumerpriceindex',
               'format':'%Y-%m-%d',               
               'date':{'年':'-','月份':'-01'},
               'columns':['date','cpi','cpi_yoy','cpi_ring']},
        'PPI':{'name':'工业品出厂价格指数',
               'code':'productpricesindex',
               'format':'%Y-%m-%d',
               'date':{'年':'-','月份':'-01'},
               'columns':['date','ppi','ppi_yoy']},
        'PMI':{'name':'采购经理人指数',
               'code':'purchasingmanagerindex',
               'format':'%Y-%m-%d',
               'date':{'年':'-','月份':'-01'},
               'columns':['date','mfg','mfg_yoy','nmfg','nmfg_yoy']},
        'MS':{'name':'货币供应量',
              'code':'moneysupply',
              'format':'%Y-%m-%d',
              'date':{'年':'-','月份':'-01'},
              'columns':['date','m2','m2_yoy','m2_ring','m1','m1_yoy','m1_ring',
                         'm0','m0_yoy','m0_ring']},
        'NFC':{'name':'新增信贷数据',
               'code':'newfinancialcredit',
               'format':'%Y-%m-%d',
               'date':{'年':'-','月份':'-01'},
               'columns':['date','nfc','nfc_yoy','nfc_ring']},
        'GDP':{'name':'国内生产总值',
               'code':'grossdomesticproduct',
               'format':'%Y-%m-%d',
               'date':{'年':'-','第1季度':'03-01','第1-2季度':'06-01','第1-3季度':'09-01','第1-4季度':'12-01'},
               'columns':['date','gdp','gdp_yoy']},
        'SCN':{'name':'股票账户新开',
               'code':'weeklystockaccountsnew',
               'format':'%Y-%m-%d',
               'date':{},
               'columns':['date','scn']},
    }
    
    # 获取日期转换格式
    @classmethod
    def __get_format(cls,code):
        return cls.__data_type_dict[code].get('format')
    
    # 获取实际代码
    @classmethod
    def __get_code(cls,code):
        return cls.__data_type_dict[code].get('code')

    # 获取列名
    @classmethod
    def __get_columns(cls,code):
        return cls.__data_type_dict[code].get('columns')

    # 整理日期
    @classmethod
    def __get_date(cls,code,text):
        for s,r in cls.__data_type_dict[code].get('date').items():
            text=text.replace(s,r)
        return text
    
    @classmethod
    def hist_data(cls,code,start_date=None,end_date=None): 
        
        #列名、日期格式、实际代码
        columns=cls.__get_columns(code)
        date_format=cls.__get_format(code)
        real_code=cls.__get_code(code)
        
        # 今天日期
        today_str=datetime.now().date().strftime(date_format)

        # 约束开始日期
        if start_date>today_str:
            return None

        # 约束结束日期
        if end_date is None or end_date>today_str:
            # 今天日期
            end_date=today_str 
        
        # 数据生成器
        def data_list():
            
            # 页面计数
            page=1
            # 基本链接
            url_base='http://data.eastmoney.com/cjsj/%s.aspx?p='%(real_code) 
            
            # 请求数据
            content=requests.get(url_base+str(page)).text
            # 获得页数
            pages=int(re.findall("pageit\('(.*?)'\);",content,re.S)[0])+1
            
            # 退出循环标志
            exit=False
            
            #遍历页面
            for page in range(2,pages):

                # 解析页面
                soup=BeautifulSoup(content,'html.parser')

                # 遍历每行
                for item in soup.select('#tb tr[class=""]'):
                    # 行数据
                    item_list=list(item.stripped_strings)[:len(columns)]
                    # 日期
                    date_str=cls.__get_date(code,item_list[0])
                    # 判断数据是否在指定日期之内
                    if date_str<=end_date:
                        if date_str<start_date:
                            exit=True
                            # 退出行循环
                            break
                        # 每行数据
                        yield [date_str]+[text.replace('%','') for text in item_list[1:]]  
                if exit:
                    # 退出页面循环
                    break
                    
                # 获取每页内容
                content=requests.get(url_base+str(page)).text
        data=[item for item in data_list()]
        if len(data)==0:
            return None
        # 组织数据（迭代数据生成器）
        df=pd.DataFrame(data=data,columns=columns)
        # 转换为标准日期格式
        df['date']=pd.to_datetime(df['date'],format=date_format)
        # 设置索引
        df.set_index('date',inplace=True)
        df.index.name=None
        # 返回数据，转换数据格式、排序、索引频率
        return df.astype('float').sort_index()#.to_period('M')  

    
class Shibor(object):
    
  
    @classmethod
    def get_data(cls,code,url_d,url_type,columns,start_date=None,end_date=None): 
 
        # 数据生成器
        def data_list():
            
            # 页面计数
            page=1
            # 基本链接2
            url_base='http://data.eastmoney.com/shibor/shibor.aspx?\
m=sh&t=99&d=%s&cu=cny&type=%s&p='%(url_d,url_type) 
            
            # 请求数据
            content=requests.get(url_base+str(page)).text
            # 解析页面
            soup=BeautifulSoup(content,'html.parser')
            # 获得页数
            pages=int(soup.select('#PageCont a[class="next"]')[0].get_text().replace('...',''))+1
            
            # 退出循环标志
            exit=False

            #遍历页面
            for page in range(2,pages):

                # 遍历每行
                for item in soup.select('#tb tr'):
                    # 行数据
                    item_list=list(item.stripped_strings)[:2]
                    # 日期
                    date_str=item_list[0]
                    # 判断数据是否在指定日期之内
                    if date_str<=end_date:
                        if date_str<start_date:
                            exit=True
                            # 退出行循环
                            break
                        # 每行数据
                        yield [text for text in item_list]  
                if exit:
                    # 退出页面循环
                    break
                    
                # 获取每页内容
                content=requests.get(url_base+str(page)).text
                # 解析页面
                soup=BeautifulSoup(content,'html.parser')
                
                
        # 组织数据（迭代数据生成器）
        df=pd.DataFrame(data=[item for item in data_list()],columns=['date',columns])
        # 转换为标准日期格式
        df['date']=pd.to_datetime(df['date'],format='%Y-%m-%d')
        # 设置索引
        df.set_index('date',inplace=True)
        df.index.name=None
        # 返回数据，转换数据格式、排序、索引频率
        return df
              
    @classmethod
    def hist_data(cls,start_date=None,end_date=None):  
                      
        # 今天日期
        today_str=datetime.now().date().strftime('%Y-%m-%d')

        # 约束开始日期
        if start_date>today_str:
            return None

        # 约束结束日期
        if end_date is None or end_date>today_str:
            # 今天日期
            end_date=today_str
            
        df=pd.DataFrame()
        
        # 参数
        code_list=zip(['ON','1W','2W','1M','3M','6M','9M','1Y'],
                      ['99221','99222','99223','99224','99225','99226','99227','99228'],
                     ['009016','009017','009018','009019','009020','009021','009022','009023'])

        # 遍历所有code
        for code,url_d,url_type in code_list:
            temp_df=cls.get_data(code,url_d,url_type,code.lower(),start_date,end_date)
            # 拼接数据
            df=pd.concat([df,temp_df],axis=1)
        if len(df)==0:
            return None
        else:
            # 转换为浮点格式、排序    
            return df.astype('float').sort_index() 

        
