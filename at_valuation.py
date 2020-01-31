
# -*- coding: utf-8 -*-

# 导入基本库
import numpy as np
import pandas as pd

# 导入自定义库
from pf_idx import Index

#研究、策略中区别配置
try:
    #策略中必须导入kuanke.user_space_api包，用于支持read_file
    from kuanke.user_space_api import read_file,get_price,normalize_code
except:
    pass
    

#\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\
# 市场关注
#-------------------------------------------------------------------------------------------------------------------------------------------------

FILE_PATH='Data/'


# 初始化对象 
index=Index('csv',FILE_PATH)

# 估值图文件名
image_name=['idx-img-qscpe','idx-img-qscpb','idx-img-kj',
    'idx-img-zj','idx-img-pes','idx-img-pbs']

#估值图标题
image_title=['全市场-PE估值图','全市场-PB估值图','宽基指数-PE对比图',
    '行业主题指数-PE对比图','PE估值表','PB估值表']
        

#\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\
# 周报：指数估值图表（邮件）
#-------------------------------------------------------------------------------------------------------------------------------------------------

def get_index_chart():

    #全市场PE估值图
    fig=index.value.chart.line_one(index.pool.qsc.keys()[0],item='pe',mode='e') 
    index.value.chart.to_image(fig,image_name[0]) 
    print('生成图表：全市场PE')
    
    #全市场PB估值图
    fig=index.value.chart.line_one(index.pool.qsc.keys()[0],item='pb',mode='e') 
    index.value.chart.to_image(fig,image_name[1]) 
    print('生成图表：全市场PB')
    
    #宽基指数PE估值对比图
    fig=index.value.chart.line_multi(index.pool.qsc.keys()+index.pool.kj.keys(),title='宽基指数')
    index.value.chart.to_image(fig[0],image_name[2]) 
    print('生成图表：宽基指数PE对比')
    
    #行业主题指数PE估值对比图
    fig=index.value.chart.line_multi(index.pool.zj.keys(),title='行业主题指数')
    index.value.chart.to_image(fig[0],image_name[3]) 
    print('生成图表：行业主题指数PE对比')
    
    #PE估值表
    df=index.value.table.value(index.pool.watch.keys(),item='pe',mode='e') 
    index.value.table.to_image(df,image_name[4])
    print('生成图表：PE估值表')
    
    #PB估值表
    df=index.value.table.value(index.pool.watch.keys(),item='pb',mode='e') 
    index.value.table.to_image(df,image_name[5])
    print('生成图表：PB估值表')
        
    df=index.value.table.analyse.read(10)
    update=df['update'].iloc[0]
    
    title='周报：指数估值'
    author='DGCIdea'
    
    subject='%s（%s %s）'%(title,update,author)
    message=('<h2>%s</h2>')%(title)
    message+=('<p>%s<br/>')%author
    message+=('更新日期：%s<br/></p>')%update
    
    for name,title in zip(image_name,image_title):
        message+=('<h3>%s</h3><p><img src="cid:%s"></p><br/>')%(title,name)
        
    return subject,message,image_name


#\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\
# 日报：指数估值数据表（邮件）
#-------------------------------------------------------------------------------------------------------------------------------------------------

def get_index_table():

    # 读取表
    table=[index.value.table.value(index.pool.value,item='pe'),
        index.value.table.value(index.pool.value,item='pb'),
        index.value.table.finance(index.pool.value)]
        
    # 添加标记
    for item in table:
        item['名称']='#'+item['名称']
        item.index='@'+item.index+'@'
        item.rename(columns={'名称':'$名称'},inplace=True)

    # 更新日期    
    date_str=index.value.table.analyse.read(10)['update'].iloc[0]
    
    # 内容
    msg='<h2>日报：指数估值</h2>'
    msg+='<p>'+"DGC'Idea"+'<br/>'
    msg+='更新日期：%s<br/></p>'%date_str
    msg+='<h3>PE估值表(等权 10年)</h3>%s'%table[0].to_html()
    msg+='<h3>PB估值表(等权 10年)</h3>%s'%table[1].to_html()
    msg+='<h3>财务指标表</h3>%s'%table[2].to_html()
   
    # 格式化
    msg=msg.replace('class="dataframe"','')\
        .replace('<table border="1" class="dataframe">','<table border="1" cellspacing="0" cellpadding="6" rules="rows" frame="void" width="100%">')\
        .replace('<th></th>','<th>$代码</th>').replace('<tr>','<tr align="right">')\
        .replace('<th>$','<th align="left">').replace('<td>#','<td align="left">')\
        .replace('<th>@','<td align="left">').replace('@</th>','</td>')\
        .replace('NaN','*')
 
    title='日报：指数估值（%s DGCIdea）'%(date_str)
    
    return title,msg