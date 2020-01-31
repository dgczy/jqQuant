# -*- coding: utf-8 -*-


# 基本包
import numpy as np
import pandas as pd
import math
import os

# 聚源数据、交易日
from jqdata import jy,get_trade_days

# 自定数据引擎
from dm import *
# 环境检测
from tl import IN_BACKTEST,data_to_period,Code,get_volatility

#必须依照以下顺序导入、设置matplotlib
import matplotlib

if IN_BACKTEST:
    #策略中必须导入kuanke.user_space_api包
    from kuanke.user_space_api import *
    #策略中绘图必须使用Agg模式（即后台绘制）
    matplotlib.use('Agg') 
    
import matplotlib.pyplot as plt

# 日期时间
import time 
from datetime import timedelta,date,datetime

    
class TProject(object):
    """
    项目信息
    data_name：'cvs'表示使用文件引擎，其它表示使用数据库名
    data_path：数据库路径或文件路径 
    project_id：项目ID
    project_name：项目名称
    project_note：项目说明
    """
    # 构造函数
    def __init__(self,data_name,data_path,project_name,project_id,project_note):
        self.id=project_id
        self.name=project_name
        self.note=project_note
        # 配置数据引擎
        if data_name=='csv':
            self.dm=Csv(data_path)            
        else:
            self.dm=Sqlite(data_name,data_path)
        # 配置图像存储引擎    
        self.image=Image(data_path)
    
    
class TField(object):
    """
    字段基类
    """    
    #价格字段
    price=[]
    
    #估值字段
    value=[]
    
    change=[]
    
    #财务指标字段
    finance=[]

    #参数对应名称
    label={
        'e':'等权','w':'加权','m':'中位数','a':'算数平均','close':'收盘价格','cap':'市值(亿)','volume':'成交量','money':'成交额',
        'pe_e':'PE','pb_e':'PB',
        'pe':'PE','pb':'PB','ps':'PS','roe':'ROE','dyr':'股息率','roi':'收益率','vlt':'波动率',
        'D':'日线','W':'周线','M':'月线',
        'C10Y':'10年期国债市盈率',
        10:u'10年',5:u'5年',3:u'3年',0:u'所有',1:u'1年',2:u'2年',4:u'4年',
        'value':'估值','change':'行情',
        }     
    

    @staticmethod 
    def name(item):
        return TField.label[item]  
    
    
class TPool(object):
    """
    标的基类
    dm：数据引擎
    project：项目
    """
    def __init__(self,project):
        self.dm=project.dm
        self.project=project
        
        try:
            # 读取标的
            self.__pool=self.read()
            # 转换为代码列表
            self.to_track(self.__pool)
        except:
            print '%s 标的不存在!'%(self.project.note)    
 

    def create(self,pool):
        """
        默认使用字典构造标的，子类可重载
        pool：标的，dict
        """
        df=pd.DataFrame.from_dict(pool,orient='index')
        df=df.rename(columns={0:'name'})  
        # 保存
        self.save(df)
        # 转换为代码列表
        self.to_track(df)

        
    def show(self):
        """
        显示标的，子类可重载
        返回：数据表，df
        """
        df=self.read()
        df=df.rename(columns={'name':'名称'})
        # 返回指数标的
        return df 
 

    def read(self):
        """
        读取标的
        返回：数据表，df
        """
        df=self.dm.read(self.to_name(),encoding='utf-8')
        # 返回指数标的
        return df   

    
    def save(self,df):   
        """
        保存标的
        df：数据表，dataframe
        返回：无
        """
        #总是采用替换模式，采用utf-8编码，否则读取后无法正确显示代码名称
        self.dm.save(self.to_name(),df,append=False,encoding='utf-8')

        
    def name(self,code):
        """
        代码转换为名称
        返回：代码名称，str
        """
        return self.track[code]

    
    def to_track(self,df): 
        """
        生成代码字典，子类可重载
        """
        # 索引转换为字符串格式，如果索引是纯数字
        df.index=df.index.astype('str')
        self.track=df.name.to_dict()     

        
    def to_name(self):  
        """
        获得文件名或数据库表名，子类可重新实现 
        """
        if self.project.name is None :
            return '%s_pool'%(self.project.id)
        else:
            return '%s_pool_%s'%(self.project.id,self.project.name)        
         

            
class Tdata(object):
    """
    数据获取基类
    获取、读取、保存数据
    project：项目
    pool：标的
    """
    def __init__(self,project,pool):
        self.dm=project.dm
        self.project=project
        self.pool=pool
        #数据更新日期
        self.update_date=None

        
    def read(self,code,items=None,years=0,start_date=None,period='D'):
        """
        读取数据 
        name：文件名或数据库表名，str，例：idx_sh_000922
        items：字段，list，例：['pe_e','close']
        years：数据时段，int，例：10，表示10年
        start_date：数据开始日期，str，例：2015-08-01，与years不能同时使用
        period：线型，str，例：D、W、M分别表示日、星期、月
        返回：数据表，DataFrame 
        """
        # 代码转换为文件名或表名（数据库）
        df=self.dm.read(self.to_name(code),cols=items,parse_dates=True)
        # 返回指定年数数据 
        if years>0:
            df=df[df.index>=str(df.index[-1].date()-timedelta(365*years))]
        # 返回指定起始日期后的数据    
        if not start_date is None:  
            df=df[df.index>=start_date]    
        # 数据转换，只针对A股指数 
        if period in ['W','M']:
            df=data_to_period(df,period)
        # 返回数据        
        return df

    
    def save(self,code,df,append=True):
        """
        保存数据 
        name：文件名或数据库表名，str，例：idx_sh_000922
        df：数据表 DataFrame 
        append：保存模式，bool，例：True、False分别标识追加、替换模式
        返回无
        """
        # 保存数据
        self.dm.save(self.to_name(code),df,append)
        
    
    def update(self,codes): 
        """
        更新数据，子类可重载
        codes：代码列表，list
        返回：无
        """
        # 更新数量
        n=0
        # 更新日期
        update_date=None
        # 最近一个交易日
        trade_date=get_trade_days(end_date=pd.datetime.today(),count=10)[-2].strftime('%Y-%m-%d')
        # 数据保存模式
        append=False
        
        # 遍历代码列表
        for code in codes:
            print '\r数据更新：%s'%(self.pool.name(code)),
            # 判断数据文件是否存在
            # 不存在则初次获取，存在则追加数据
            try:           
                # 读取数据
                temp_df=self.read(code,years=1)
                # 获取上次更新日期
                update_date=temp_df.index[-1].date()
                # 本次更新日期
                clac_date=(update_date+timedelta(1)).strftime('%Y-%m-%d')
                # 本次更新日期大于最近交易日期，则无需更新
                if clac_date>trade_date:
                    continue
                # 增量获取
                df=self.get_data(code,start_date=clac_date)
                # 追加模式
                append=True
            except IOError: 
                # 替换模式
                append=False
                # 初次获取
                df=self.get_data(code)                
            except Exception as e:
                #print '%s：%s'%(self.pool.name(code),e)
                continue
                
            
            if not df is None :
                # 保存数据 
                self.save(code,df,append=append)
                # 获取更新日期
                #update_date=df.index[-1].date()
                print code
                n+=1
        if n>0:          
            print '\r数据更新：%s，已更新 %s 个'%(self.project.note,n)
        else:
            print '\r数据更新：%s，无需更新'%(self.project.note)
            
        # 记录更新日期
        #self.update_date=update_date
        
    
    def get_data(self,code,start_date=None,end_date=None):
        """
        数据获取，待子类具体实现
        code：代码，str
        start_date：开始日期，date
        end_date：结束日期，date
        """
        pass

    
    def to_name(self,code):  
        """
        获得文件名或数据库表名，子类可重载
        code：代码，str
        """
        return '%s_%s'%(self.project.id,code.lower())  

    
    
class Tanalyse(object):
    """
    数据分析基类
    project：项目信息类
    pool：标的类
    data：数据类
    analyse_name：分析类别名称
    """
    def __init__(self,project,pool,data,analyse_name):
        self.dm=project.dm
        self.project=project
        self.pool=pool
        self.data=data
        self.analyse_name=analyse_name

        
    def read(self,aid):
        """
        读取分析表  
        aid：项目
        """
        #读取数据
        df=self.dm.read(self.to_name())
        # 索引转换为字符串格式，如果索引是纯数字
        df.index=df.index.astype('str')
        #返回数据表
        return df[df['aid']==aid]

    
    def save(self,df):
        """
        保存分析表 
        df：数据表，dataframe
        """
        self.dm.save(self.to_name(),df,append=False)

        
    def to_name(self):  
        """
        转换为文件名或数据库表名，子类可重新实现
        code：代码
        """
        if self.project.name is None: 
            return '%s_%s'%(self.project.id,self.analyse_name) 
        else:
            return'%s_%s_%s'%(self.project.id,self.project.name,self.analyse_name)  

        
    def standard_analysis(self,name,cols,df):
        """
        标准分析
        """
        return []

    
    def standard_columns(self,cols):
        """
        标准分析列名，子类可重载
        返回：list
        """
        return []    

    
    def standard_cols(self):
        """
        标准分析字段，子类可重载
        返回：字段列表，list
        """
        return []

    
    def extend_analysis(self,code,df):
        """
        扩展字段分析，子类可重载
        code：代码，str
        df：数据表
        返回：list
        """
        return [] 

    
    def extend_columns(self):
        """
        扩展字段标题，子类可重载
        返回：列表，list
        """
        return []

    
    def basis_analysis(self,code,df,aid):
        """
        基本字段分析，子类可重载
        code：代码，str
        df：数据表
        返回：不同类型数值
        """
        #更新日期
        update_date=df.index[-1].date()  
        #返回数据
        return [update_date,aid]
 

    def basis_columns(self):
        """
        基本字段列名，子类可重载
        返回：list
        """
        #返回一个list
        return ['update','aid']  

    
    def get_analysis(self,codes,years): 
        """
        数据分析 ，子类必须重载
        codes：代码列表，dict
        years：时段,int
        """
        pass    
    
    
    def get_data_update(self):
        """
        获取数据更新日期
        """
        return self.data.read(self.pool.track.keys()[0],years=1).index[-1].date().strftime('%Y-%m-%d')
    
    
    def update(self,codes,items,force=False):  
        """
        更新分析表  
        codes：代码字典，dict
        items：项目，int or str
        force：强制更新，bool
        """
        # 是否更新标记
        need_analysis=False
        # 判断分析文件是否存存在
        try:
            #文件存在，判断是否需要更新
            # 读取分析表
            df=self.read(items[0])
            # 最近分析更新日期
            update_date=df['update'].iloc[-1]
            # 数据更新日期
            data_update=self.get_data_update()
            # 判断是否需要更新
            if update_date<data_update:
                need_analysis=True 
        except Exception as e:
            #print('%s'%e)
            # 分析文件不存在，需分析
            need_analysis=True  
        # 需要更新，或强制更新    
        if need_analysis or force:
            df=self.get_analysis(codes,items)
            # 保存分析表     
            self.save(df) 
            print '\r数据分析：%s%s，分析完毕'%(self.project.note,TField.name(self.analyse_name))
        else:
            print '\r数据分析：%s%s，无需重新分析'%(self.project.note,TField.name(self.analyse_name))
                 
        
           
class Tvalue(Tanalyse):
    """
    估值分析基类
    project：项目类
    pool：标的类
    data：数据类
    """
    def __init__(self,project,pool,data):
        Tanalyse.__init__(self,project,pool,data,'value')  
        #机会百分比
        self.chance=20
        #危险百分比
        self.danger=80 
        
        
    def to_state(self,quantile):
        """
        分为值转换为区间说明
        quantile：分为值
        """
        if quantile < 10.0:
            return u'极低'
        elif 10 <= quantile and quantile < 20:
            return u'较低'
        elif 20 <= quantile and quantile < 40:
            return u'偏低'
        elif 40 <= quantile and quantile < 60:
            return u'合理'
        elif 60 <= quantile and quantile < 80:
            return u'偏高'
        elif 80 <=quantile and quantile < 90:
            return u'较高'
        elif 90 <= quantile:
            return u'极高'

        
    def basis_analysis(self,code,df,aid):
        """
        基本字段分析
        code：代码，str
        df：数据表
        返回：不同类型数值
        """
        #样本数量
        sample=len(df) 
        #数据起始日期
        start_date=df.index[0].date()
        #更新日期
        update_date=df.index[-1].date()  
        #返回数据
        return sample,start_date,update_date,aid

    
    def basis_columns(self):
        """
        基本字段列名
        返回：list
        """
        #返回一个list
        return ['sample','start','update','aid']          

    
    def standard_analysis(self,name,cols,df):
        """
        标准字段分析
        name：代码名称，str
        cols：字段列表，list
        df：数据表
        返回：分析数据，list
        """
        # 分析结果list
        val_results=[name]
        #遍历字段
        for col in cols:
            #当前值、最小、最大、中位
            val=round(df[col].iloc[-1],2)
            val_min=round(df[col].min(),2)
            val_max=round(df[col].max(),2)
            val_median=round(df[col].median(),2)
            val_mean=round(df[col].mean(),2)
            #高度、区间
            val_ratio=round(len(df[col][df[col]<val])/float(len(df[col]))*100,2)
            val_state=self.to_state(val_ratio)
            #分为点
            val_q=[df[col].quantile(i/10.0) for i in range(11)]
            val_q=[round(i,2) for i in val_q]
            #最大跌幅比
            val_drop=round((val_min-val)/val*100,2) if val>0 else float(np.NaN) 
            #追加数据
            val_results+=[val,val_ratio,val_state,val_min,val_max,val_median,val_mean,val_drop,
                val_q[1],val_q[2],val_q[4],val_q[5],val_q[6],val_q[8],val_q[9]]  
        #返回分析结果    
        return val_results

    
    def standard_columns(self,cols):
        """
        获取标准分析字段标题
        cols：字段列表,list
        返回：字段标题，list
        """
        val_columns=['name']
        #生成分析字段标题
        for col in cols:
            val_columns+=[col,col+'_ratio',col+'_state',col+'_min',col+'_max',col+'_median',col+'_mean',col+'_drop',
                    col+'_q10',col+'_q20',col+'_q40',col+'_q50',col+'_q60',col+'_q80',col+'_q90']    
        #返回标题列表    
        return val_columns    

     
    def get_analysis(self,codes,items): 
        """
        数据分析 
        codes：代码列表，dict
        years：时段,int
        """
        #数据list
        data_list=[]
        #代码list
        code_list=[]  
        #标准分析字段
        cols=self.standard_cols()
        for item in items:
            #遍历所有字段
            for code,name in codes.items():
                print u'\r数据分析：%s，[ %s ] 数据'%(name,TField.name(item)),
                #print code
                #读取数据
                df=self.data.read(code,years=item)
                #标准分析
                val_results=self.standard_analysis(name,cols,df)
                #扩展分析、子类实现
                val_results+=self.extend_analysis(code,df)
                #基本分析
                val_results+=self.basis_analysis(code,df,item)
                #追加数据    
                data_list.append(val_results)
                #追加代码
                code_list.append(code)
        #标准字段名
        data_columns=self.standard_columns(cols)
        #扩展字段名，子类实现
        data_columns+=self.extend_columns()
        #基本字段名
        data_columns+=self.basis_columns()
        #生成数据表
        df=pd.DataFrame(data=data_list,index=code_list,columns=data_columns)     
        #返回数据
        return df  

    
    
class Tchange(Tanalyse):
    """
    行情分析基类
    project：项目类
    pool：标的类
    data：数据类
    """
    def __init__(self,project,pool,data):
        Tanalyse.__init__(self,project,pool,data,'change')

        
    def get_analysis(self,codes,items):
        """
        数据分析 
        codes：代码列表，dict
        items：项目,str
        """
        #数据list
        data_list=[]
        #代码list
        code_list=[]  
        #标准分析字段
        for item in items:
            for code,name in codes.items():
                print u'\r数据分析：%s，[ %s ] 数据'%(name,TField.name(item)),
                #获取数据
                df=self.data.read(code,items=[item]) 
                #标准分析
                val_results=self.standard_analysis(name,item,df)
                #扩展分析、子类实现
                val_results+=self.extend_analysis(code,df,item)
                #基本分析
                val_results+=self.basis_analysis(code,df,item)
                #追加数据    
                data_list.append(val_results)
                #追加代码
                code_list.append(code)
        #标准字段名
        data_columns=self.standard_columns()
        #扩展字段名，子类实现
        data_columns+=self.extend_columns()
        #基本字段名
        data_columns+=self.basis_columns()
        #生成数据表
        df=pd.DataFrame(data=data_list,index=code_list,columns=data_columns)     
        #返回数据
        return df 
     
    
    def __get_day_change(self,col,df):
        """
        日涨跌
        col：字段，str
        df：数据表，df
        返回：列表，list
        """
        val_results=[]
        for d in [2,6,11,21,31,61,91]:
            val_results.append(round((df[col].iloc[-1]-df[col].iloc[-d])/df[col].iloc[-d]*100.0,2))
        return val_results


    def __get_week_change(self,col,df):
        """
        周涨跌
        col：字段，str
        df：数据表，df
        返回：浮点数，float
        """
        # 当前时间      
        now = datetime.now()
        # 上周最后交易日的日期
        start_date=now-timedelta(days=now.weekday()+3)
        # 本周最后交易日的日期
        end_date=now+timedelta(days=4-now.weekday())

        # 取小于start_date的最后一个交易日（最后一个交易日并不一定等于start_date，
        # 因为start_date可能正好是假期即非交易日）
        start_val=df[df.index<=start_date][col].iloc[-1]
        # 取小于end_date的最后一个交易日，说明同上
        end_val=df[df.index<=end_date][col].iloc[-1]

        return round((end_val-start_val)/start_val*100.0,2)


    def __get_month_change(self,col,df):
        """
        月涨跌
        col：字段，str
        df：数据表，df
        返回：浮点数，float
        """
        # 当前时间
        now = datetime.now()
        # 上月最后一天日期（本月第一天日期减去一天）
        start_date =datetime(now.year,now.month,1)-timedelta(days=1)
        # 本月最后一天日期(下月第一天减去一天)
        if now.month==12:
            end_date=datetime(now.year,12,31)
        else:    
            end_date = datetime(now.year, now.month + 1, 1) - timedelta(days=1)

        # 取小于start_date的最后一个交易日（最后一个交易日并不一定等于start_date，
        # 因为start_date可能正好是假期即非交易日）
        start_val=df[df.index<=start_date][col].iloc[-1]
        # 取小于end_date的最后一个交易日，说明同上
        end_val=df[df.index<=end_date][col].iloc[-1]

        return round((end_val-start_val)/start_val*100.0,2)


    def __get_quarter_change(self,col,df):
        """
        季涨跌
        col：字段，str
        df：数据表，df
        返回：浮点数，float
        """
        # 当前时间
        now = datetime.now()
        month = (now.month - 1) - (now.month - 1) % 3 + 1
        # 上季最后一天日期（本月第一天日期减去一天）
        start_date =datetime(now.year, month, 1) - timedelta(days=1)
        # 本季最后一天日期
        if month>9:
            # 第四季度最后一天
            end_date=datetime(now.year,12,31)
        else:  
            # 其它季度
            end_date=datetime(now.year,month+3,1)-timedelta(days=1)

        # 取小于start_date的最后一个交易日（最后一个交易日并不一定等于start_date，
        # 因为start_date可能正好是假期即非交易日）
        start_val=df[df.index<=start_date][col].iloc[-1]
        # 取小于end_date的最后一个交易日，说明同上
        end_val=df[df.index<=end_date][col].iloc[-1]

        return round((end_val-start_val)/start_val*100.0,2)


    def __get_year_change(self,col,df):
        """
        年涨跌
        col：字段，str
        df：数据表，df
        返回：浮点数，float
        """
        # 当前时间
        now = datetime.now()
        # 上年最后一天日期（本月第一天日期减去一天）
        start_date =datetime(now.year, 1, 1)- timedelta(days=1)
        # 本年最后一天日期
        end_date = datetime(now.year + 1, 1, 1) - timedelta(days=1)

        # 取小于start_date的最后一个交易日（最后一个交易日并不一定等于start_date，
        # 因为start_date可能正好是假期即非交易日）
        start_val=df[df.index<=start_date][col].iloc[-1]
        # 取小于end_date的最后一个交易日，说明同上
        end_val=df[df.index<=end_date][col].iloc[-1]

        return round((end_val-start_val)/start_val*100.0,2)


    def __get_5year_change(self,col,df):
        """
        近5年涨跌
        col：字段，str
        df：数据表，df
        返回：列表，list
        """
        val_results=[]
        # 当前年份
        year=datetime.now().year
        for y in range(year-5,year):
            start_date=str(y)+'-01-01'
            end_date=str(y)+'-12-31'
            try:
                # 取小于start_date的最后一个交易日（最后一个交易日并不一定等于start_date，
                # 因为start_date可能正好是假期即非交易日）
                start_val=df[df.index<start_date][col].iloc[-1]
                # 取小于end_date的最后一个交易日，说明同上
                end_val=df[df.index<=end_date][col].iloc[-1]
            
                val_results.append(round((end_val-start_val)/start_val*100.0,2)) 
            except:
                val_results.append(None)
        return val_results

    
    def standard_analysis(self,name,col,df):
        """
        标准字段分析
        name：代码名称，str
        cols：字段列表，list
        df：数据表
        返回：分析数据，list
        """
        # 分析结果list
        val_results=[name]

        val_results += self.__get_day_change(col,df)   
        val_results += [self.__get_week_change(col,df)]
        val_results += [self.__get_month_change(col,df)]
        val_results += [self.__get_quarter_change(col,df)]
        val_results += [self.__get_year_change(col,df)]
        val_results += self.__get_5year_change(col,df)

        #返回分析结果    
        return val_results
     
    
    def standard_columns(self):
        """
        获取标准分析字段标题
        cols：字段列表,list
        返回：字段标题，list
        """
        # 当前年份
        year=datetime.now().year
        val_columns=['name','1d','5d','10d','20d','30d','60d','90d','tw','tm','tq','ty']
        # 生成分析字段标题
        val_columns+=[str(y)+'y' for y in range(year-5,year)]    
        # 返回标题   
        return val_columns       
    
    
    def standard_label(self):
        """
        获取标准分析字段标题
        cols：字段列表,list
        返回：字段标题，list
        """
        # 当前年份
        year=datetime.now().year
        val_columns=['近1日','5日','10日','20日','30日','60日','90日','本周','本月','本季','本年']
        # 生成分析字段标题
        val_columns+=[str(y)+'年' for y in range(year-5,year)]    
        val_columns+=['波动率']
        # 返回标题   
        return val_columns  

    
    def extend_analysis(self,code,df,col):
        """
        扩展分析
        """
        #波动率、回报率
        vlt=get_volatility(df[[col]])
        return [vlt]

    
    def extend_columns(self):
        """
        扩展分析标题
        """
        return ['vlt'] 
    
       
        
class Tchart(object):
    """
    图表基类
    project：项目类
    pool：标的类
    data：数据类
    analyse：分析类
    """
    def __init__(self,project,pool,data,analyse):
        self.image=project.image
        self.pool=pool    
        self.data=data
        self.analyse=analyse
        
        
    @staticmethod 
    def set_title2(ax,title):
        """
        图像标题，用于热力图
        """
        ax.text(-2.0,-1,title[1],fontsize=16,alpha=0.8,color='gray')
        ax.text(-2.0,-1.5,title[0],fontsize=24,alpha=0.8,color='black')

        
    @staticmethod 
    def set_title(ax,title):   
        """
        标题，用于折线图
        """
        fig=ax.get_figure()
#         fig.suptitle(title[1],horizontalalignment='left',x=0.095,fontsize=16,alpha=0.8,color='gray')
#         ax.set_title(title[0],fontsize=22,loc='left',position=[-0.04,1.13],alpha=0.8)
        fig.text(0.07,1,title[0],fontsize=24,alpha=0.8,multialignment='left')
        fig.text(0.07,0.96,title[1],fontsize=16,alpha=0.5,multialignment='left')

        
    @staticmethod 
    def set_ylabel(ax,label):
        """
        设置Y轴标题
        """        
        ax.set_ylabel(label,fontsize=13,alpha=0.8)  

        
    @staticmethod 
    def set_xlabel(ax,label):
        """
        设置X轴标题
        """
        ax.set_xlabel(label,fontsize=13,alpha=0.8) 
        
        
    @staticmethod 
    def set_legend(ax,labels,loc=1,ncol=1):
        """
        设置图例
        """
        ax.legend(labels,fontsize=12,loc=loc,frameon=False,ncol=ncol)

        
    @staticmethod 
    def set_grid(ax,xy='x'):
        """
        设置网格线
        """   
        #网格线（不显示纵向网格线）
        ax.grid(True,alpha=0.5,linewidth=0.3,linestyle='solid',color='gray')
        if xy=='x':
            ax.xaxis.grid(False)
        else:
            ax.yaxis.grid(False)

            
    @staticmethod 
    def set_left(ax):
        """
        设置边框、刻度
        """   
        #去除右、上边框颜色，设置左、下边框为灰色
        ax.spines['right'].set_color("none")
        ax.spines['top'].set_color("none")
        ax.spines['left'].set_color("gray")
        ax.spines['bottom'].set_color("gray")
        #去除上、右刻度线（保留左、下刻度线）
        ax.get_xaxis().tick_bottom()
        ax.get_yaxis().tick_left()

        
    @staticmethod 
    def set_right(ax):
        """
        设置边框、刻度
        """   
        #去除左、上边框颜色，设置右、下边框为灰色
        ax.spines['left'].set_color("none")
        ax.spines['top'].set_color("none")
        ax.spines['right'].set_color("gray")
        ax.spines['bottom'].set_color("none")
        #去除上刻度线（保留下刻度线）
        ax.get_xaxis().tick_bottom() 

        
    @staticmethod 
    def set_all(ax):
        """
        设置边框、刻度
        """        
        #去除左、上、右、下边框
        ax.spines['left'].set_color("none")
        ax.spines['top'].set_color("none")
        ax.spines['right'].set_color("none")
        ax.spines['bottom'].set_color("none")
        #去除右、下刻度线
        ax.get_xaxis().tick_top()
        ax.get_yaxis().tick_left()  

   
    def to_image(self,fig,file_name,file_type='png'):
        """
        数据表保存为图片
        fig：画板对象
        file_name：文件名
        file_type：文件扩展名，机图片类型
        """
        self.image.save(fig,file_name,file_type)

   
    def line_one(self,code,item='pe',mode='',years=10,right='',period='W',quantile=True):
        """
        走势图
        code：代码
        item：字段，pe、pb、ps、roe、dyr
        mode：算法，e、w、m、a对应等权、加权、中位数、算数平均数，为空时表示roe、dyr
        years：时段，10、5、3、0对应10年、5年、3年、全部时段
        right：右轴对比，close、cap对应收盘点位、市值，为空时表示关闭对比
        period：线型
        quantile：分为点线开关
        """
        #item名称
        item_name=TField.label[item]
        #算法名称
        mode_name='' if mode=='' else TField.label[mode]+' '
        #字段修正
        item=item if mode=='' else '%s_%s'%(item,mode)
        #字段列表    
        item_list=[item]
        if right!='':
            item_list+=[right]
        #读取数据
        df=self.data.read(code,years=years,items=item_list,period=period)     
        #获取数据分析表数据
        table=self.analyse.read(years)
        #当前值
        item_val=table.ix[code,item]       
        #百分位
        item_ratio=table.ix[code,item+'_ratio']
        #中位值、机会值、危险值
        item_median=table.ix[code,item+'_median']
        item_chance=table.ix[code,item+'_q'+str(self.analyse.chance)]
        item_danger=table.ix[code,item+'_q'+str(self.analyse.danger)]
        item_min=table.ix[code,item+'_min']
        item_max=table.ix[code,item+'_max']
        item_mean=table.ix[code,item+'_mean']
        #画线
        ax=df.plot(figsize=(18,8),secondary_y=[right],fontsize=12.5,linewidth=1,grid=True,mark_right=False,
                   rot=0,style=['b','orange'])
        #是否显示分为线
        if quantile==True:
            #当前值、机会值、中位值、危险值
            ax.axhline(y=item_val,linewidth=0.8,color='blue',linestyle=':',alpha=1.0)
            ax.axhline(y=item_chance,linewidth=0.8,color='green',linestyle='solid',alpha=0.7)
            ax.axhline(y=item_median,linewidth=0.8,color='black',linestyle='solid',alpha=0.7)
            ax.axhline(y=item_danger,linewidth=0.8,color='red',linestyle='solid',alpha=0.7)
            item_legend_front=[item_name,
                u'当前 %.2f %.2f%%'%(item_val,item_ratio),u'机会 %.2f 20%%'%item_chance,
                u'中位 %.2f 50%%'%item_median,u'危险 %.2f 80%%'%item_danger]
        else:
            item_legend_front=[u'当前 %.2f'%item_val]
        #最小、最大、平均值线（并不显示线）    
        ax.axhline(y=item_min,linewidth=0.0,color='white',linestyle='solid',alpha=0.0)
        ax.axhline(y=item_max,linewidth=0.0,color='white',linestyle='solid',alpha=0.0)
        ax.axhline(y=item_mean,linewidth=0.0,color='white',linestyle='solid',alpha=0.0)    
        #图例   
        item_legend=item_legend_front+[u'最小 %.2f'%item_min,u'最大 %.2f'%item_max,u'平均 %.2f'%item_mean]
        #标题
        title=[(u'%s-%s')%(self.pool.name(code),item_name),(u'%s%s %s  %s')%(mode_name,TField.label[years],
            TField.label[period],df.index[-1].strftime('%Y年%m月%d日'))]
        #设置标题
        self.set_title(ax,title)
        #设置Y轴标题
        self.set_ylabel(ax,item_name)
        #设置图例 
        self.set_legend(ax,item_legend,2,8)
        #设置网格线
        self.set_grid(ax)
        #美化边框、刻度
        self.set_left(ax)
        #获取画板和r_ax
        fig=ax.get_figure()
        if right!='':
            r_ax=fig.get_axes()[1] 
            #y轴标题
            r_ylabel=TField.label[right]
            #图例标题
            r_legend=[u'%s %.2f'%(r_ylabel,df[right].iloc[-1])]
            #设置Y轴标题
            self.set_ylabel(r_ax,r_ylabel)
            #设置图例 
            self.set_legend(r_ax,r_legend,4)
            #美化边框、刻度
            self.set_right(r_ax) 
        #返回figure对象    
        return fig    
    
    
    def hist(self,code,item='pe',mode='',years=10):  
        """
        频谱图 
        code：代码
        item：字段，pe、pb、ps、roe、dyr
        mode：算法，e、w、m、a对应等权、加权、中位数、算数平均数，为空时表示roe、dyr
        years：时段，10、5、3、0对应10年、5年、3年、全部时段
        """
        #修正item
        item_name=TField.label[item]
        mode_name='' if mode=='' else TField.label[mode]+' '
        item=item if mode=='' else  '%s_%s'%(item,mode)
        #获取数据
        df=self.data.read(code,years=years,items=[item],period='D')
        #获取分析表数据
        table=self.analyse.read(years)
        #当前值、高度
        item_val=table.ix[code,item]       
        item_ratio=table.ix[code,item+'_ratio']      
        #设置画板
        fig,ax=plt.subplots(figsize=(18,7))     
        #画出频率分布图
        (n,bins,patches)=ax.hist(df[item],bins=50,facecolor='b',alpha=0.6,edgecolor='white') 
        #标记当前位置 
        for i in range(len(n)):  
            if item_val<=bins[i]:
                j=(0 if i==0 else i-1)
                ax.bar(bins[j],n[j],width=patches[i].get_width(),
                         facecolor='orange',edgecolor='white',alpha=1) 
                break  
        #主标题、左侧y轴标题
        title=[(u'%s-%s分布频率')%(self.pool.track[code],item_name),(u'%s%s  %s')%(mode_name,TField.label[years],
              df.index[-1].strftime('%Y-%m-%d'))]
        item_legend=[u'分布频率',u'当前位置 %s %.2f%%'%(item_val,item_ratio)]
        #设置标题
        self.set_title(ax,title)
        #设置Y轴标题
        self.set_ylabel(ax,item_name)
        #设置网格线
        self.set_grid(ax)
        #设置图例 
        self.set_legend(ax,item_legend,2)
        #美化边框、刻度
        self.set_left(ax)
        return fig           
    
    
    def heat(self,codes,item='pe',mode='',cols=[],title=None):
        """
        热力图 
        code：代码
        item：字段，pe、pb、ps、roe、dyr
        mode：算法，e、w、m、a对应等权、加权、中位数、算数平均数，为空时表示roe、dyr
        cols：字段，list
        title：标题，str
        """
        item_name=TField.label[item]
        item=item if mode=='' else  '%s_%s'%(item,mode)
        #读取数据
        df=self.analyse.read(item)
        #最近分析日期
        update_date=str(df['update'].iloc[0])[0:10]
        #筛选
        df=df[df.index.isin(codes)]
        #重置索引
        df.index=df['name']
        df.index.name=None
        del df['name']
        del df['update']
        del df['aid']
        df.columns=self.analyse.standard_label()
        if cols:
            df=df[cols]
        fig,ax=plt.subplots(figsize=(72,len(df))) 
        #画图
        p=ax.imshow(df,cmap=plt.cm.jet,interpolation='nearest')
 
        x_ticks=range(len(df.columns))
        y_ticks=range(len(df))
        x_labels=df.columns  
        y_labels=df.index

        ax.set_xticks(x_ticks)
        ax.set_xticklabels(x_labels,fontsize=13,rotation=0)
        ax.set_yticks(y_ticks)
        ax.set_yticklabels(y_labels,fontsize=13)
        
        #强弱值
        for x in x_ticks:
            for y in y_ticks:
                val=df.iloc[y,x]
                val='' if np.isnan(val) else '%6.2f'%(val)
                ax.text(x-0.25,y,val,fontsize=13,color='black',alpha=0.5)
        
        #美化边框、刻度
        self.set_all(ax)
        self.set_title2(ax,['%s-%s 阶段涨跌'%(title,item_name),update_date])
        ax.xaxis.set_ticks_position('top')  
        
        #返回画板对象     
        return fig  

        
    def line_ratio(self,code,compare='000902.XSHG',item='close',years=1,title=None,only_ratio=False,period='W'):
        """
        相对强弱图 
        code：代码
        item：项目
        compare：对比代码
        years：时长
        """
        # 修正字段，
        if item=='close':
            # 当比值数据为close时
            items=['close']
        else:
            # 当比值数据为mony时
            items=['close',item]
            
        # 根据是否只显示比值线，配置线型
        style=['w','w','gray'] if only_ratio else ['b','red','gray']  
            
        # 对比数据
        df_compare=self.data.read(compare,years=years,period=period)[items]
        # 标的数据
        df_code=self.data.read(code,years=years,period=period)[items]
        
        df=pd.DataFrame()  
        # 收盘价格
        df['code']=df_code['close']
        df['compare']=df_compare['close']   
        # 比值
        df['saw']=df_code[item]/df_compare[item]*100.0

        # 绘图
        ax=df.plot(figsize=(18,8),secondary_y=['saw'],mark_right=False,rot=0,
                       grid=True,linewidth=1.0,style=style) 
        
        # 名称
        code_name=self.pool.track[code]
        compare_name=self.pool.track[compare]
        # 图例   
        legend=['%s  收盘价格 %.2f'%(code_name,df_code['close'].iloc[-1]),
                '%s  收盘价格 %.2f'%(compare_name,df_compare['close'].iloc[-1])]  
        # 标题
        title=['%s - %s %s'%(code_name,compare_name,title),
               '近%s年  %s'%(years,df.index[-1].strftime('%Y年%m月%d日'))]

        # 设置标题
        self.set_title(ax,title)
        # 设置Y轴标题
        #self.set_ylabel(ax,item_name)
        # 设置图例 
        self.set_legend(ax,legend,2,2)
        # 设置网格线
        self.set_grid(ax)
        # 美化边框、刻度
        self.set_left(ax)

        #获取画板和r_ax
        fig=ax.get_figure()
        r_ax=fig.get_axes()[1] 
        #y轴标题
        #r_ylabel=TField.label[right]
        #图例标题
        r_legend=['%s 比  %.2f%%'%(TField.label[item],df['saw'].iloc[-1])]
        #设置Y轴标题
        #self.set_ylabel(r_ax,r_ylabel)
        #设置图例 
        self.set_legend(r_ax,r_legend,1)
        #美化边框、刻度
        self.set_right(r_ax) 
     
    
    def line_multi(self,codes,item='pe',mode='e',title='',years=10,period='W'):      
        """        
        走势对比图
        codes：指数代码列表
        item：字段，pe、pb、ps、roe、dyr
        mode：算法，e、w、m、a对应等权、加权、中位数、算数平均数，为空时表示roe、dyr
        title：图表标题
        years：时段，10、5、3、0对应10年、5年、3年、全部时段
        period：线型
        """ 
        #参数检查、修正
        item_name=TField.label[item]
        mode_name='' if mode=='' else TField.label[mode]+' '
        item=item if mode=='' else '%s_%s'%(item,mode)
        #图例列表
        item_legend=[]
        #遍历指数列表
        df=pd.DataFrame()
        for code in codes:
            #名称列表
            item_legend.append(self.pool.track[code] )
            #读取数据，并转换为周数据
            df[code]=self.data.read(code,years=years,period=period)[item]
        #画图
        ax=df.plot(figsize=(18,8),fontsize=12.5,grid=True,linewidth=1.0,rot=0,)
        #主标题
        title=[(u'%s-%s对比')%(title,item_name),(u'%s%s %s  %s')%(mode_name,TField.label[years],TField.label[period],
                                              df.index[-1].date().strftime('%Y年%m月%d日'))] 
        #设置标题
        self.set_title(ax,title)
        #设置Y轴标题
        self.set_ylabel(ax,item_name)
        #设置图例 
        self.set_legend(ax,item_legend,2)
        #设置网格线
        self.set_grid(ax)
        #美化边框、刻度
        self.set_left(ax)
        #返回figure对象、数据表的起始日期
        return ax.get_figure(),df.index[0]   
        

    def bar_multi(self,codes,item='pe',mode='e',title='',years=10):
        """
        柱状对比图  
        index_list：指数代码列表
        item：字段，pe、pb、ps、roe、dyr
        mode：算法，e、w、m、a对应等权、加权、中位数、算数平均数，为空时表示roe、dyr
        title：图表标题
        years：时段，10、5、3、0对应10年、5年、3年、全部时段
        """
        #参数检查、修正
        item_name=TField.label[item]
        mode_name='' if mode=='' else TField.label[mode]+' '
        item=item if mode=='' else  '%s_%s_ratio'%(item,mode)
        #读取数据
        df=self.analyse.read(years)[['name',item,'update']]
        #最近分析日期
        item_update=str(df['update'].iloc[0])[0:10]
        #筛选
        df=df[df.index.isin(codes)]
        #重置索引
        df.index=df['name']
        df.index.name=None
        #删除多余列
        del df['name']
        del df['update']
        #更改列名
        df=df.rename(columns={item:item_name})
        #标题
        title=['%s-%s对比'%(title,item_name),'%s%s  %s'%(mode_name,TField.label[years],item_update)]
        #画图
        ax=df.plot(kind='barh',figsize=(18,8),grid=True,fontsize=12.5,alpha=0.5,color='b') 
        #设置标题
        self.set_title(ax,title)
        #设置图例 
        self.set_legend(ax,[item_name],1)
        #设置Y轴标题
        self.set_xlabel(ax,item_name)
        #设置网格线
        self.set_grid(ax,'y')
        #美化边框、刻度
        self.set_left(ax)
        #返回figure对象
        return ax.get_figure()       

    
class Ttable(object):
    """
    数据表基类
    project：项目类
    pool：标的类
    data：数据类
    analyse：分析类
    """        
    def __init__(self,project,pool,data,analyse):
        self.image=project.image
        self.pool=pool    
        self.data=data
        self.analyse=analyse

        
    def value_columns(self,item,item_name):
        return {'name':'名称',item:item_name,item+'_ratio':'高度(%)',item+'_state':'区间',
            item+'_min':'最低值',item+'_max':'最高值',item+'_median':'中位值',item+'_drop':'距底(%)',
           item+'_q'+str(self.analyse.chance):'机会值',item+'_q'+str(self.analyse.danger):'危险值',
            }
 

    def value_cols(self,item):
        return ['name',item,item+'_ratio',item+'_state',item+'_min',item+'_max',item+'_median',item+'_drop',
            #机会值、危险值
            item+'_q'+str(self.analyse.chance),item+'_q'+str(self.analyse.danger)
            ]
 

    def finance_columns(self):
        return {
            'name':'名称','roe':'ROE(%)','dyr':'股息率(%)','roi':'收益率(%)','vlt':'波动率',
            'start':'数据起点','sample':'样本数','stocks':'成份股数'}

    
    def finance_cols(self):
        return ['name','roe','dyr','roi','vlt','start','sample','stocks']

        
    def integrate_columns(self,mode):
        return {
            'name':'名称',
            'pe'+mode:'PE','pe'+mode+'_ratio':'高度(%)','pe'+mode+'_state':'区间',
            'pb'+mode:'PB','pb'+mode+'_ratio':'高度(%)','pb'+mode+'_state':'区间',
            'ps'+mode:'PS','ps'+mode+'_ratio':'高度(%)','ps'+mode+'_state':'区间',
            'roe':'ROE','dyr':'股息率(%)','vlt':'波动率','roi':'收益率(%)',
            'start':'数据起点','sample':'样本数','stocks':'成份股数'}
    
    
    def integrate_cols(self,mode):
        return [
            'name',
            'pe'+mode,'pe'+mode+'_ratio','pe'+mode+'_state',
            'pb'+mode,'pb'+mode+'_ratio','pb'+mode+'_state',
            'ps'+mode,'ps'+mode+'_ratio','ps'+mode+'_state',
            'roe','dyr','vlt','roi',
            'start','sample','stocks'
            ]
    
    
    def value(self,codes,item='pe',mode='e',sort='ratio',asc=True,years=10):
        """
        估值表
        codes：指数代码列表
        item：字段，pe、pb、ps
        mode：算法，e、w、m、a对应等权、加权、中位数、算数平均数
        sort：排序，ratio表示高度，为空表示当前值
        asc：排序方向，True/False，升序或降序
        years：时段，10、5、3、0对应10年、5年、3年、全部时段
        """        
        #修正
        item_name=TField.label[item]
        item=item if mode=='' else '%s_%s'%(item,mode)
        sort=item if sort=='' else '%s_%s'%(item,sort)
        #读取分析表
        df=self.analyse.read(years)[self.value_cols(item)]
        #显示指定指数
        df=df[df.index.isin(codes)]
        #排序
        df=df.sort([sort],ascending=asc)
        #更改标题
        df=df.rename(columns=self.value_columns(item,item_name)) 
        return df
    

    def finance(self,codes,sort='roe',asc=True,years=10):
        """
        财务指标表
        codes：指数代码列表
        sort：排序，ratio表示高度，为空表示当前值
        asc：排序方向，True/False，升序或降序
        years：时段，10、5、3、0对应10年、5年、3年、全部时段
        """
        #读取分析表
        df=self.analyse.read(years)[self.finance_cols()]
        #显示指定指数
        df=df[df.index.isin(codes)]
        #排序
        df=df.sort([sort],ascending=asc)
        #更改标题
        df=df.rename(columns=self.finance_columns()) 
        return df


    def integrate(self,codes,item='pe',mode='e',sort='ratio',asc=True,years=10):
        """
        估值综合表
        codes：指数代码列表
        item：字段，pe、pb、ps
        mode：算法，e、w、m、a对应等权、加权、中位数、算数平均数
        sort：排序，ratio表示高度，为空表示当前值
        asc：排序方向，True/False，升序或降序
        years：时段，10、5、3、0对应10年、5年、3年、全部时段
        """
        #修正
        mode='' if mode=='' else '_%s'%(mode)
        if item in ['pe','pb','ps']:
            sort='' if sort=='' else '_%s'%(sort)  
            sort=item+mode+sort
        else:
            sort=item   
        df=self.analyse.read(years)[self.integrate_cols(mode)]
        #显示指定指数
        df=df[df.index.isin(codes)]
        #去除代码后缀、转换为大写
        try:
            df.index=df.index.astype('str').str.upper() 
            df.index=df.index.astype('str').str[0:6]  
        except:
            pass
        #排序
        df=df.sort([sort],ascending=asc)
        #更改标题    
        df=df.rename(columns=self.integrate_columns(mode)) 
        return df

    
    def render_table(self,data,col_width=1.9,row_height=0.625,font_size=14,
        header_color='#40466e',row_colors=['#f1f1f2','w'],edge_color='#f1f1f2',
        bbox=[0,0,1,1],header_columns=0,ax=None,**kwargs):
        """
        数据表转换为图像
        data：数据表对象
        col_width：列宽
        row_height：行高
        font_size：字体大小
        header_color：标题背景色
        row_colors：行背景色
        edge_color：边框色
        bbox：边框
        header_columns：标题
        ax：画板子对象
        """
        if ax is None:
            #计算画板大小
            size=(np.array(data.shape[::-1])+np.array([0,1]))*np.array([col_width,row_height])
            fig,ax=plt.subplots(figsize=size)
            #关闭坐标轴
            ax.axis('off')
        #绘制表格    
        mpl_table=ax.table(cellText=data.values,bbox=bbox,colLabels=data.columns,**kwargs)
        #关闭文字设置
        mpl_table.auto_set_font_size(False)
        #设置文字大小
        mpl_table.set_fontsize(font_size)
        #遍历所有单元格
        for k,cell in six.iteritems(mpl_table._cells):
            #设置格子边框
            cell.set_edgecolor(edge_color)
            #判断是否为列标题
            if k[0]==0 or k[1]<header_columns:
                #文字加粗，颜色为白色
                cell.set_text_props(weight='bold',color='w')
                #设置边框颜色
                cell.set_facecolor(header_color)
            else:
                #设置单元格颜色
                cell.set_facecolor(row_colors[k[0]%len(row_colors)])
        #返回画板对象        
        return fig 

    
    def to_image(self,df,file_name,file_type='png'):
        """
        数据表保存为图片
        df：数据表
        file_name：文件名
        file_type：图片类型，即文件扩展名
        """
        fig=self.render_table(df)
        self.image.save(fig,file_name,file_type)
        
