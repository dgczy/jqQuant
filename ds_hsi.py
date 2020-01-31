# -*- coding: utf-8 -*-


#获取港指数据
#恒生官网

#导入库
import numpy as np
import pandas as pd
import requests,re,xlrd,json
from datetime import timedelta,date

_codes={
    'HSI':'hsi',
    'HSCEI':'hscei', #恒生国企指数       
    }

_url={
    'pe':'https://www.hsi.com.hk/static/uploads/contents/zh_cn/dl_centre/monthly/pe/%s.xls',
    'dyr':'https://www.hsi.com.hk/static/uploads/contents/zh_cn/dl_centre/reports_stat/monthly/dy/%s.xls',
}

_url_last='https://www.hsi.com.hk/static/uploads/contents/en/indexes/report/%s/idx_%s.csv'

_col={
    'pe':9,
    'dyr':8,
}

class Hsi(object):

    #pe
    #月线历史数据（恒生官网只能获取月线历史数据）
    @staticmethod
    def hist_data(code,data_tpye):  
        # 转换代码
        code=_codes[code] 
        #url
        url=(_url[data_tpye])%(code)  
        #获取历史数据（月线数据，xls文件）
        ret=requests.get(url)
        if not ret.ok:
            return None
           
        #解析xls文件
        #打开xls文件
        xlr_f=xlrd.open_workbook(file_contents=ret.content)
        #获取第一个表
        table=xlr_f.sheet_by_index(0)
        #获取日期列
        date_list=table.col_values(0)[13:]
        date_list=[xlrd.xldate.xldate_as_datetime(item,datemode=0) for item in date_list if item is not u'']
        #获取pe列
        data_list=table.col_values(1)[13:]
        data_list=[item for item in data_list if item is not u'']              
        #获取最新日线数据（经测试只能获取最近60天的日线数据，只取最近一天的数据）          
        for i in range(10):
            #日期
            day_str=(date.today()-timedelta(1)-timedelta(i)).strftime('%d%b%y')
            day_str=day_str[1:] if day_str.startswith('0') else day_str
            #日线数据url（换行处必须顶格）  
            url=(_url_last)%(code,day_str)      
            #获取数据（cvs文件）
            ret=requests.get(url)
            if not ret.ok:
                continue
            #数据进行解码再编码
            content=ret.content[2:].decode("utf16").encode('utf8')
            #取第二行、去掉双引号、按照tab符号分解
            data=content.splitlines()[2].replace('\"','').split('\t') 
            #月线最新日期与日线最新日期比较，相同，则不追加数据
            date_new=pd.Timestamp(data[0])
            if date_list[-1]==date_new:
                break
            #首列为日期
            data_list.append(float(data[_col[data_tpye]]))
            date_list.append(date_new)
            break
        df=pd.DataFrame(data_list,index=date_list,columns=[data_tpye])   
        #返回数据
        return df 

    #获取港股指数成份股数
    @staticmethod
    def stocks(code): 
        # 转换代码
        code=_codes[code] 
        #url
        url='https://www.hsi.com.hk/data/schi/rt/index-series/%s/constituents.do?3681' % (code)  
        #获取数据
        ret=requests.get(url)
        if ret.ok is True:
            content=json.loads(ret.text)
            # 成份股路径
            constituentContent=content.get('indexSeriesList')[0].get('indexList')[0].get('constituentContent')
            # 生成成份股列表
            return [item.get('constituentName') for item in constituentContent]
        else:
            return []
        
        
