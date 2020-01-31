# -*- coding: utf-8 -*-

#爬取集思录数据

#导入库
import numpy as np
import pandas as pd
import requests
import json

#返回数据格式
#{"page":1,"rows":[
#{"id":"159901","cell":
#{"fund_id":"159901","fund_nm":"\u6df1100ETF","index_id":"399330","creation_unit":"20","amount":"76197","unit_total":"36.39",
#"unit_incr":"-0.01","price":"4.776","volume":"1512.44","last_time":"13:13:27","increase_rt":"0.46%","estimate_value":"4.7795",
#"last_est_time":"13:13:31","discount_rt":"-0.07%","fund_nav":"4.7519","nav_dt":"2018-03-28",
#"index_nm":"\u6df1\u8bc1100","index_increase_rt":"0.57%","pe":"21.896","pb":"2.905","owned":"0",
#"fund_nm_color":"\u6df1100ETF","fund_id_color":"159901"}},.....

#url列表
item_dict={
    #指数etf
    'index_etf':'https://www.jisilu.cn/jisiludata/etf.php?owned_user_id=&___jsl=LST___t=1521011241034&rp=25&page=1',
    #黄金etf
    'gold_etf':'https://www.jisilu.cn/jisiludata/etf.php?qtype=pmetf&owned_user_id=&___jsl=LST___t=1521031571182&rp=25&page=1',
    #股票lof
    'stock_lof':'https://www.jisilu.cn/data/lof/stock_lof_list/?___jsl=LST___t=1521032417514&rp=25&page=1',
    #指数lof
    'index_lof':'https://www.jisilu.cn/data/lof/index_lof_list/?___jsl=LST___t=1521032503443&rp=25&page=1',
    #T+0QDII
    't0_qdii':'https://www.jisilu.cn/data/qdii/qdii_list/?___jsl=LST___t=1521719002039&rp=25&page=1',
    #分级基金a
    'a_sfund':'https://www.jisilu.cn/data/sfnew/funda_list/?___jsl=LST___t=1521033817407',
    #分级基金b
    'b_sfund':'https://www.jisilu.cn/data/sfnew/fundb_list/?___jsl=LST___t=1521720312022',
    #分级基金母基金
    'm_sfund':'https://www.jisilu.cn/data/sfnew/fundm_list/?___jsl=LST___t=1521720384599',
    #可转债
    'sell_cbond':'https://www.jisilu.cn/data/cbnew/cb_list/?___jsl=LST___t=1521454858565',
    #可转债（专业版）
    'new_cbond':'https://www.jisilu.cn/data/cbnew/pre_list/?___jsl=LST___t=1521541045672',
    #A股、港股比价
    'ah_stock':'https://www.jisilu.cn/data/ha/index2list/?___jsl=LST___t=1521601615737',
    #A股新股
    'new_stock':'https://www.jisilu.cn/data/new_stock/super/?___jsl=LST___t=1521613233148&rp=22&page=1&pageSize=50',
    #A股历史新股
    'hit_stock':'https://www.jisilu.cn/data/new_stock/apply/?___jsl=LST___t=1521607109955&rp=22&page=1&pageSize=2000', 
    #银行理财
    'bank_money':'https://www.jisilu.cn/data/repo/finance_product_list/?___jsl=LST___t=1521618468408',
    #交易所理财
    'trade_money':'https://www.jisilu.cn/data/money_fund/list/?___jsl=LST___t=1521622422447&rp=25&page=1',  
    #T+0货基
    't0_money':'https://www.jisilu.cn/data/repo/trade_money_fund_list/?___jsl=LST___t=1521776507162',
    #深市逆回购
    'sz_money':'https://www.jisilu.cn/data/repo/sz_repo_list/?___jsl=LST___t=1521618468330', 
    #沪市逆回购
    'sh_money':'https://www.jisilu.cn/data/repo/sh_repo_list/?___jsl=LST___t=1521618468235',  
    #港股新股
    'hnew_stock':'https://www.jisilu.cn/data/new_stock/hkipo/?___jsl=LST___t=1521775933492', 
    }
    
def get_web_data(url):
    #数据头
    web_requests=requests.session()
    user_agent="Mozilla/5.0 (Windows NT 10.0; WOW64) AppleWebKit/537.36 \
                        (KHTML, like Gecko) Chrome/47.0.2526.106 Safari/537.36"
    web_requests.headers.update({'User-Agent':user_agent})
    # jsl_requests.headers.update({"Upgrade-Insecure-Requests":"1"})
    web_requests.headers.update({'X-Requested-With':'XMLHttpRequest'})
    #返回页面
    content=web_requests.get(url,timeout=5)
    #json 数据
    data=content.json()
    return data
    
#获取集思录网站数据
#item：页面代码
def get_jsl_data(item):
    #采用haeaders请求方式
    data=get_web_data(item_dict[item])
    #整理数据
    df=pd.DataFrame()
    #返回的数据比较特殊，只能逐行转换
    data_list=[]
    #遍历所有cell
    for row in data['rows']:
        data_list.append(row['cell'])
    #列表转换为dataframe  
    df=pd.DataFrame(data_list)
    #返回dataframe格式数据    
    return df