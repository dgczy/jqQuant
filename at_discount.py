
# -*- coding: utf-8 -*-

'''
华宝油气预估净值=T-2日华宝油气净值×（1+T-1日SPSIOP涨跌幅×0.95）×（1+ T-1日USDCNY涨跌幅）
'''

# 导入基本库
import numpy as np
import pandas as pd

# 导入聚宽库
from jqdata import *

# 导入自定义库
from ds_invest import *
from ds_wall import *
from ds_jisilu import *

#研究、策略中区别配置
try:
    #策略中必须导入kuanke.user_space_api包，用于支持read_file
    from kuanke.user_space_api import get_extras,get_price
except:
    pass
    
FILE_PATH='Data/'

def get_discount_162411():

    today=pd.datetime.today().strftime('%Y-%m-%d')

    trade_days=get_trade_days(end_date=today, count=10)
    t3=trade_days[-4].strftime('%Y-%m-%d')
    t2=trade_days[-3].strftime('%Y-%m-%d')
    t1=trade_days[-2].strftime('%Y-%m-%d')
    print 'T-1日 %s,T-2日 %s,T-3日 %s'%(t1,t2,t3)
    
    loop=True
    loop_count=1
    while loop:
        try:
            # T-2日华宝油气净值（聚宽取净值函数有问题）
            #dt=get_extras( 'acc_net_value', '162411.XSHE', end_date=t2, df=True, count=1)
            #t2_extras=dt['162411.XSHE'].iloc[0]
            
            df=get_jsl_data('t0_qdii')
            df=df[df['fund_id']=='162411']
            t2_extras=float(df['fund_nav'].iloc[0])
            print 'T-2日净值 %s %s'%(t2,t2_extras)

            # T-1日SPSIOP涨跌幅
            dt=Invest.hist_price('SPSIOP',start_date=t3,end_date=today)
            t1_spsiop=(dt['close'].iloc[-1]-dt['close'].iloc[-2])/dt['close'].iloc[-2]
            print 'T-1日SPSIOP涨跌幅 %s %.2f%%'%(t1,t1_spsiop*100)

            # T-1日USDCNY涨跌幅
            dt=Wall.hist_price('UCY',start_date=t2,end_date=t1)
            t1_usdcny=(dt['close'].iloc[-1]-dt['close'].iloc[-2])/dt['close'].iloc[-2]
            print 'T-1日USDCNY涨跌幅 %s %.2f%%'%(t1,t1_usdcny*100)


            dt=get_price('162411.XSHE', end_date=today, frequency='daily', fields=None, skip_paused=False, fq='pre', count=1)
            t_price=dt['close'].iloc[0]
            print '当前价格 %s %.3f'%(today,t_price)

            # 预估净值
            t_extras=t2_extras*(1+t1_spsiop*0.95)*(1+t1_usdcny)
            print '预估净值 %s %.3f'%(today,t_extras)

            # 溢价
            t_premium=(t_price-t_extras)/t_extras*100
            print '溢价 %.2f%%'%(t_premium)

            loop=False
        except Exception as e:
            print e
            if loop_count>3:
                return None
            loop_count+=1
            loop=True

    df=pd.DataFrame(data=[
                    ['#华宝油气','','','','',''],
                    ['#溢价率','　当前价格','　%s日净值'%(t2[-2:]),'　%s日估值'%(today[-2:]),'　SPSIOP','　USDCNY'],
                    ['#%.2f%%'%(t_premium),'%.3f'%(t_price),'%.3f'%(t2_extras),'%.3f'%(t_extras),
                        '%.2f%%'%(t1_spsiop*100),'%.2f%%'%(t1_usdcny*100)]
                    ],columns=range(6)) 

    info1=df.to_html(
        index=False,
        header=False,
        classes='')\
        .replace('<table border="1" class="dataframe">','<table border="1" cellspacing="0" cellpadding="6" rules="rows" frame="void" width="100%">')\
        .replace('<td>#','<td style="text-align:left;font-weight:bold">')\
        .replace('<tbody>','<tbody style="text-align:right;font-size:12.5px">')\
        .replace('None','')

    
    fix_premium=abs(t_premium)
 
    if fix_premium<=1.5:    
        info=[['#无套利机会','' ]] 
    if fix_premium>1.5 and fix_premium<2.5:  
        if t_premium<0:
            info=[
                ['#防守型','' ],
                ['T日','收盘前场内赎回'],
                ['T+1日','买入同等场内份额'],
                ['T+2日','场外申购确认'],
                ['T+6日','赎回资金到账'],
                ['T+7日','赎回资金可用'],
                ] 
        elif t_premium>0:  
            info=[
                ['#溢价套利','' ],
                ['#防守型','' ],
                ['T日','收盘前场外申购同等场内份额（按T日净值计算）'],
                ['T+1日','卖出场内份额'],
                ['T+2日','场外申购确认'],
                ['T+3日','场外转场内'],
                ['T+4日','场外转场内确认'],
                ['T+5日','转入场内的份额可以交易'],
                ] 
    elif fix_premium>=2.5:
        if t_premium<0:
            info=[
                ['#折价套利','' ],
                ['#进攻型','' ],
                ['T日','1、收盘前场内赎回'],
                ['','2、场内买入同等份额'],
                ['T+2日','场外申购确认'],
                ['T+6日','赎回资金到账'],
                ['T+7日','赎回资金可用'],
                ['#防守型','' ],
                ['T日','收盘前场外赎回同等场内份额（按T日净值计算）'],
                ['T+1日','买入同等场内份额'],
                ['T+2日','场外申购确认'],
                ['T+6日','赎回资金到账'],
                ['T+7日','赎回资金可用'],
                ]
        elif t_premium>0:  
            info=[
                ['#溢价套利','' ],
                ['#进攻型','' ],
                ['T日','1、卖出场内份额'],
                ['','2、收盘前场外申购同等份额（按T日净值计算）'],
                ['T+2日','场外申购确认'],
                ['T+3日','场外转场内'],
                ['T+4日','场外转场内确认'],
                ['T+5日','转入场内的份额可以交易'],
                ['#防守型','' ],
                ['T日','收盘前场外申购同等场内份额（按T日净值计算）'],
                ['T+1日','卖出场内份额'],
                ['T+2日','场外申购确认'],
                ['T+3日','场外转场内'],
                ['T+4日','场外转场内确认'],
                ['T+5日','转入场内的份额可以交易'],
                ]

    df=pd.DataFrame(data=info,columns=range(2)) 
    info2=df.to_html(
        index=False,
        header=False,
        classes='')\
        .replace('<table border="1" class="dataframe">','<table border="1" cellspacing="0" cellpadding="6" rules="rows" frame="void" width="100%">')\
        .replace('<td>#','<td style="text-align:left;font-weight:bold">')\
        .replace('<tbody>','<tbody style="text-align:left;font-size:12.5px">')\
        .replace('None','')
    
    
    #返回信息
    return info1 + info2  
    
    
