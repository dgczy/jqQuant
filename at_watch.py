
# -*- coding: utf-8 -*-

# 导入基本库
import numpy as np
import pandas as pd
from six import StringIO

# 导入自定义库
from ds_sina import *
from ds_wall import *
from ds_jisilu import *

#研究、策略中区别配置
try:
    #策略中必须导入kuanke.user_space_api包，用于支持read_file
    from kuanke.user_space_api import read_file,get_price,normalize_code
except:
    pass
    
FILE_PATH='Data/'

    
#\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\
#日报：市场关注（微信）
#-------------------------------------------------------------------------------------------------------------------------------------------------
        
# 套利
def get_discount_fund():
    #爬取集思录数据
    df=get_jsl_data('t0_qdii')
    df=df[df['fund_id']=='162411']
    info=pd.DataFrame(
            data=[
                ['#套利','','','','',''],
                ['华宝油气','溢价率','当前价格',
                 '%s日净值'%(df['nav_dt'].iloc[0][-2:]),'%s日估值'%(df['est_val_dt'].iloc[0][-2:]),
                 '指数涨幅'],
                ['',df['discount_rt'].iloc[0],df['price'].iloc[0],
                 round(float(df['fund_nav'].iloc[0]),3),round(float(df['estimate_value'].iloc[0]),3),
                df['ref_increase_rt'].iloc[0]]],
            columns=range(6)) 
    return info


# 新股
def get_new_stock():
    #爬取集思录数据
    a_df=get_jsl_data('new_stock')
    #获取今日日期并转换格式
    today=pd.datetime.today().strftime('%m-%d')
    #筛选A股今日新股（生成股票名称列表）
    #爬取集思录数据
    h_df=get_jsl_data('hnew_stock')
    #筛选港股今日新股（生成股票名称列表）
    info=pd.DataFrame(
                  data=[['#新股','','','','',''],
                        ['A股']+a_df[a_df['apply_dt'].str[0:5]==today]['stock_nm'][0:4].tolist(),
                        ['港股']+h_df[h_df['apply_dt'].str[0:5]==today]['stock_nm'][0:4].tolist()],
                  columns=range(6)) 
    #返回信息
    return info


#可转债
def get_new_cbond():
    #爬取集思录数据
    df=get_jsl_data('new_cbond')
    #获取今日日期并转换格式
    today=pd.datetime.today().strftime('%m-%d')
    #筛选今日可申购转债（ap_flag为A）
    #筛选今日上市转债（ap_flag为D）
    info=pd.DataFrame(
        data=[['#可转债','','','','',''],
            ['申购']+df[df['ap_flag'].str[0:1]=='A']['bond_nm'].tolist(),#apply_cd
            ['上市']+df[df['ap_flag'].str[0:1]=='D']['bond_nm'].tolist()],
        columns=range(6)) 
    #返回信息
    return info


#逆回购
def get_rep_money():
    #爬取集思录数据（上海逆回购）
    hs_df=get_jsl_data('sh_money')[0:5] 
    
    #爬取集思录数据（深圳逆回购）
    ss_df=get_jsl_data('sz_money')[0:5] 

    info=pd.DataFrame(
        data=[
            ['#逆回购','','','','',''],
            ['沪市']+['%s/%s'%(price,d) for d,price in zip([1,2,3,4,7],hs_df['price'].tolist())],
            ['深市']+['%s/%s'%(price,d) for d,price in zip([1,2,3,4,7],ss_df['price'].tolist())]
            ],
        columns=range(6))  
    #返回信息
    return info


#货基
def get_t0_money():
    #待选货基列表
    fund_list=['511850','511800','511830','511700','511820','511900',
        '511690','511810','511660','511990','511880']
    #爬取集思录数据
    df=get_jsl_data('t0_money')[['fund_id','sell_price']] 
    #按照待选列表筛选数据
    df=df[df['fund_id'].isin(fund_list)]
    #转换价格为浮点类型，否则排序不准确，保留四位小数
    df['sell_price']=np.round(df['sell_price'].astype('float'),4)
    #从高到底排序,取价格最低的前4个
    df=df.sort('sell_price',ascending=True)[0:6]

    info=pd.DataFrame(
        data=[
            ['#货基','','','','',''],
            df['fund_id'].tolist(),df['sell_price'].tolist()],
        columns=range(6))  

    #返回信息
    return info

#指数估值      
def get_value_index():
    #指数关注列表       
    index_list=[
        'HSCEI',#恒生国企,
        'HSI',#恒生指数
        'SPX',#恒生指数
        '000902.SH',#全市场
        '000300.SH',#沪深300
        '000905.SH',#中证500
        '399006.sz',#创业板指
        '399005.sz',#中小板指  
        '000991.SH',#全指医药
        '000992.SH',#全指金融
        '000990.SH',#全指消费
        '000993.SH',#全指信息
        '399812.sz',#中证养老
        '000807.SH',#食品饮料
        '000922.SH',#中证红利 
        '399967.sz',#中证军工
        '399989.sz',#中证医疗
        '000827.SH',#中证环保
        '399971.sz',#中证传媒
        '399986.sz',#中证银行
        '399975.sz',#全指证券
        '000015.SH',#上证红利
        ]
    #读取指数分析表
    df=pd.read_csv(StringIO(read_file(FILE_PATH+'idx_value.csv')),index_col=0)
    df=df[df['aid']==10]
    #按照关注列表筛选
    df=df[df.index.isin(index_list)]
    #全市场估值
    code='000902.SH'
    #当前估值、百分位、区间
    #区间为极低的前5个指数名称
    info=pd.DataFrame(
        data=[
            ['#估值','','','','',''],
            ['全市场','PE:%s'%(df.ix[code,'pe_e']),'%s%%'%(df.ix[code,'pe_e_ratio']),#,df.ix[code,'pe_e_state']
                      'PB:%s'%(df.ix[code,'pb_e']),'%s%%'%(df.ix[code,'pb_e_ratio'])],#,df.ix[code,'pb_e_state']
            ['关注']+df[df['pe_e_state']=='极低']['name'][0:5].tolist()],
        columns=range(6))  
    #返回信息
    return info
    

    
#实时价格    
def get_real_price():
    #获取wall实时价格
    price=Wall.real_price('000001.SS,399300.SZ,399006.SZ,399001.SZ,\
SPX500INDEX,US30INDEX,NASINDEX,HKG33INDEX,GER30INDEX,SP500VIXINDEX,UK100INDEX,BDIINDEX,\
USDOLLARINDEX,USDCNH,USDCNY,USDJPY,HKDCNY,BTCUSD,\
XAUUSD,XAGUSD,\
UKOIL,USOIL,\
US10YEAR,US5YEAR,US3YEAR,CHINA10YEAR,CHINA5YEAR,CHINA3YEAR')
    info=pd.DataFrame(
        data=[
            ['#股指','','','','',''],
            ['上证综指','沪深300','创业板指','深证成指','恒生指数','BDI指数'],
            [round(price['000001.SS'],2),round(price['399300.SZ'],2),round(price['399006.SZ'],2),                                                    round(price['399001.SZ'],2),price['HKG33INDEX'],price['BDIINDEX']],
            ['标普500','道琼斯','纳斯达克','德国DAX','英国富时','VIX波动'],
            [price['SPX500INDEX'],price['US30INDEX'],price['NASINDEX'],price['GER30INDEX'],
             price['UK100INDEX'],price['SP500VIXINDEX']],
            ['#商品','','','','',''],
            ['黄金','白银','金银比','布原油','WTI原油','金油比'],
            [price['XAUUSD'],price['XAGUSD'],round(price['XAUUSD']/price['XAGUSD'],3),
            price['UKOIL'],price['USOIL'],round(price['XAUUSD']/price['UKOIL'],3)],
            ['#外汇','','','','',''],
            ['美元指数','离岸￥','在岸￥','港币/￥','＄/日元 ','比特币/＄'],
            [price['USDOLLARINDEX'],price['USDCNH'],price['USDCNY'],price['HKDCNY'],price['USDJPY'],price['BTCUSD']],
            ['#国债','','','','',''],
            ['美国10年','美国5年','美国3年','中国10年','中国5年','中国3年'],
            [price['USDOLLARINDEX'],price['USDJPY'],price['USDCNH'],
            price['CHINA10YEAR'],price['CHINA5YEAR'],price['CHINA3YEAR']]
            ],
          columns=range(6)) 
    #返回信息
    return info       
    
    
#获取关注信息     
def get_market_watch():
    try:
        df=get_value_index()
    except:
        pass
    try:
        df=pd.concat([df,get_real_price()])
    except:
        pass
    try:
        df=pd.concat([df,get_rep_money()])
    except:
        pass
    try:
        df=pd.concat([df,get_t0_money()])
    except:
        pass
    try:
        df=pd.concat([df,get_new_stock()])
    except:
        pass
    try:
        df=pd.concat([df,get_new_cbond()])
    except:
        pass  
    try:
        return df.to_html(
            index=False,
            header=False,
            classes='')\
            .replace('<table border="1" class="dataframe">','<table border="1" cellspacing="0" cellpadding="6" rules="rows" frame="void" width="100%">')\
            .replace('<td>#','<td style="text-align:left;font-weight:bold">')\
            .replace('<tbody>','<tbody style="text-align:right;font-size:12.5px">')\
            .replace('None','')
    except:
        return None
