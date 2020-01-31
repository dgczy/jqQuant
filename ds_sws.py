# -*- coding: utf-8 -*-

#获取申万官网申万行业数据

#导入库
import numpy as np
import pandas as pd
import requests
import json
from datetime import timedelta,date


class Sws(object):

    #申万1级行业代码列表
    sw1_codes=[
        '801010','801020','801030','801040','801050','801080','801110','801120','801130','801140','801150','801160','801170','801180',
        '801200','801210','801230','801710','801720','801730','801740','801750','801760','801770','801780','801790','801880','801890'
        ] 
    #申万2级行业代码列表
    sw2_codes=[
        '801011','801012','801013','801014','801015','801016','801017','801018','801021','801022','801023','801024','801032','801033',
        '801034','801035','801036','801037','801041','801051','801053','801054','801055','801072','801073','801074','801075','801076',
        '801081','801082','801083','801084','801085','801092','801093','801094','801101','801102','801111','801112','801123','801131',
        '801132','801141','801142','801143','801144','801151','801152','801153','801154','801155','801156','801161','801162','801163',
        '801164','801171','801172','801173','801174','801175','801176','801177','801178','801181','801182','801191','801192','801193',
        '801194','801202','801203','801204','801205','801211','801212','801213','801214','801215','801222','801223','801231','801711',
        '801712','801713','801721','801722','801723','801724','801725','801731','801732','801733','801734','801741','801742','801743',
        '801744','801751','801752','801761','801881'
        ]
    

    @staticmethod
    def get_sw_idu(code=None,start_date=None,end_date=None,period='D',fields=None): 
        """
        获取申万官网申万行业数据
        code：行业代码
        period：D、W、M
        start_date：None(表示最早日期)
        end_date：None(表示今天日期)
        fields：None(表示所有字段)
        """

        #headers
        header={
            'HOST':'www.swsindex.com',
            'Referer':'http://www.swsindex.com/idx0200.aspx?columnid=8838&type=Day',
            'User-Agent':'Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) \
Chrome/53.0.2785.104 Safari/537.36 Core/1.53.4482.400 QQBrowser/9.7.13001.400'
            }

        #传入参数
        param={
            'tablename':'V_Report',
            'key':'id',
            #页面序号，每页返回20条数据
            'p':'1',
            #查询语句，查询的代码、日期、数据类型
            "where":"swindexcode in ('801020') and   BargainDate>='2018-04-02' and  BargainDate<='2018-04-24' and type='Day'",
            #排序(swindexcode asc表示按照代码升序，BargainDate_1表示按照日期降序，_2表示按照升序)
            'orderby':'swindexcode asc,BargainDate_2',
            #返回的字段
            'fieldlist':'SwIndexCode,SwIndexName,BargainDate,OpenIndex,CloseIndex,MaxIndex,MinIndex,BargainAmount,BargainSum,Markup,TurnoverRate,\
PE,PB,MeanPrice,BargainSumRate,NegotiablesShareSum,NegotiablesShareSum2,DP',
            'pagecount':'1',
            'timed':'1524497094532',
            }

        #通用数据表头
        simple_columns_list=['code','name','date','open','close','high','low',
            'volume','money','change','pe','pb','cap','dyr']
        #数据表表头
        real_columns_list=['SwIndexCode','SwIndexName','BargainDate','OpenIndex','CloseIndex','MaxIndex','MinIndex',
            'BargainAmount','BargainSum','Markup','PE','PB','NegotiablesShareSum','DP']

        #数据类型（日、周、月）
        frequency_dict={'D':'day','W':'week','M':'month'}

        #行业类别
        level_list=['sw1','sw2']

        #配置代码
        code_str=','.join(Sws.sw1_codes)
        if not(code is None):   
            #如果代码为列表，判断代码列表是否在申万代码列表中
            if (type(code)==list):
                if set(code).issubset(set(Sws.sw1_codes)) or set(code).issubset(set(Sws.sw2_codes)) :
                    code_str=','.join(code)
            #如果代码为字符串，判断代码是否在申万代码列表中
            if (type(code)==str):
                if (code in Sws.sw1_codes) or (code in Sws.sw2_codes) : 
                    code_str=code

        #配置日期
        today_str=pd.datetime.today().strftime('%Y-%m-%d')
        if (start_date is None) or (start_date<'1999-12-30'): #or (start_date>today_str)
            start_date='1999-12-30'
        if (end_date is None) or (end_date>today_str) or (end_date<'1999-12-30'):
            end_date=today_str
        
        # 配置数据周期
        if not(period in frequency_dict):  
            period='D'

        # 查询语句    
        where="swindexcode in (%s) and BargainDate>='%s' and BargainDate<='%s' and type='%s'"%(code_str,
            start_date,end_date,frequency_dict[period]) 

        # 检查字段
        simple_columns=simple_columns_list 
        if not(fields is None):
            if(set(fields).issubset(set(simple_columns_list))):  
                if not (['code','name','date'] in fields):
                    simple_columns=['code','name','date']+fields

        # 转换为申万字段
        code_dict=dict(zip(simple_columns_list,real_columns_list))
        real_columns=[code_dict[item] for item in simple_columns]
        real_fields=','.join(real_columns)

        #配置参数    
        param['where']=where 
        param['fieldlist']=real_fields

        df=pd.DataFrame()
        #url
        url='http://www.swsindex.com/handler.aspx'
        #页面计数器
        page=1

        while True:
            #获取数据
            ret=requests.get(url,data=param,headers=header,timeout=5)
            #链接错误退出
            if not (ret.ok is True):
                break
            #整理引号、日期格式（否则无法json）    
            data=ret.text.replace("'", '"').replace(' 0:00:00','').replace('/','-')

            #解析数据
            data=json.loads(data).get('root')

            #无数据退出
            if len(data)==0:
                break
            #追加数据表（数据json后，列序改变，此处必须声明columns）   
            df=df.append(pd.DataFrame(data,columns=real_columns),ignore_index=True)
            #页面计数器累加
            page+=1
            #设置页面参数
            param['p']=str(page)  
            
            #print '\r已获取：%s %s，%s 条数据！'%(df.SwIndexName.iloc[0],df.SwIndexCode.iloc[0],len(df)),

        # 数据不为空
        if len(df)!=0: 
            #转换为简单字段名
            df.columns=simple_columns
            #返回数据
            return df          
        else:
            return None
        
        
    @staticmethod
    def hist_data(code,start_date=None,end_date=None,period='D'): 
        # 获取申万原始数据
        df=Sws.get_sw_idu(code,start_date,end_date,period,fields=None)
        if df is None :
            return None

        #规范日期格式
        df['date']=pd.to_datetime(df['date'],format='%Y-%m-%d')  
        
        # 设置索引
        df.set_index(['date'],inplace=True)
        df.index.name=None

        # 删除代码和名称
        del df['code']
        del df['name']
        
        # 若干列中有空值
        for item in df.columns:
            # 填充空值为：np.NaN
            df[item]=df[item].apply(lambda x: np.NaN if x=='' else x)
            # 填充np.NaN为：前一个值
            df[item].fillna(method='pad')

        # 转换为浮点格式
        df=df.astype('float')

        # 市值转换为亿元
        df['cap']=np.round(df['cap']/10000.0,2)

        # 市值转换为亿元
        df['roe']=np.round(df['pe']/df['pb'],2)

        #返回数据
        return df     