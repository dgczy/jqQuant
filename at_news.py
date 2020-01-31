
# -*- coding: utf-8 -*-

# 导入基本库
import pandas as pd

# 聚源数据库
from jqdata import jy


#研究、策略中区别配置
try:
    #策略中必须导入kuanke.user_space_api包，用于支持read_file
    from kuanke.user_space_api import read_file,query
except:
    pass
    
    

#\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\
#日报：市场快讯（邮件）
#-------------------------------------------------------------------------------------------------------------------------------------------------

# 获取资讯     
def get_market_news(news_type):
    #今天日期
    today=pd.datetime.today().strftime('%Y-%m-%d')
    #三个时间段
    morning_time=today+' 09:30:00'
    afternoon_time=today+' 13:00:00'
    evening_time=today+' 22:00:00'
    #查询聚源数据库ED_GilBroadcast
    q=query(
        #具体时间
        jy.ED_GilBroadcast.InfoPublTime,
        #标题
        jy.ED_GilBroadcast.InfoTitle,
        #正文
        jy.ED_GilBroadcast.Content,
    ).filter(
        #按照发布日期过虑
        jy.ED_GilBroadcast.InfoPublDate==today 
    ).order_by(
        #按照发布时间排序
        jy.ED_GilBroadcast.InfoPublTime.desc()
        )
    df=jy.run_query(q)  
    #筛选、组织数据
    title='市场快讯（%s DGCIdea）'%(today)
    if news_type=='morning':
        df=df[(df.InfoPublTime<=morning_time)]
        title='早报：%s'%title
    elif news_type=='afternoon':
        df=df[(df.InfoPublTime>morning_time) & (df.InfoPublTime<=afternoon_time)]
        title='午报：%s'%title
    elif news_type=='evening':
        df=df[(df.InfoPublTime>afternoon_time) & (df.InfoPublTime<=evening_time)]
        title='晚报：%s'%title
    #生成html
    if len(df)==0:
        return ('','')
    else:
        news=''
        for i in range(len(df)):
            news=news+'<hr />'
            news=news+'<p>'
            news=news+df.iloc[i].InfoTitle+'<br/>'
            news=news+df.iloc[i].InfoPublTime.strftime('%Y-%m-%d %H:%M:%S') +'<br/>'
            news=news+df.iloc[i].Content.decode('gbk').replace('\n','<br/>')+'<br/>'
            news=news+'<br/></p>'
        return (title,news)


