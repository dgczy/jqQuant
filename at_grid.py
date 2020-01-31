
# -*- coding: utf-8 -*-

#引入包
import numpy as np
import pandas as pd
import xlrd
import collections


#研究、策略中区别配置
try:
    #策略中必须导入kuanke.user_space_api包，用于支持read_file
    from kuanke.user_space_api import read_file,get_price,normalize_code
except:
    pass


FILE_NAME='网格-交易A.xlsm'
FILE_PATH='Data/'
    
def get_wg_info(file_path=FILE_PATH,file_name=FILE_NAME):

    # 打开excel文件
    content=read_file('%s%s'%(file_path,file_name))
    xlr_f=xlrd.open_workbook(file_contents=content)
    
    # 获取第一个表
    table=xlr_f.sheet_by_index(0)

    # 获取标的列表
    etf_list=[str(item)[:6] for item in table.col_values(2)[4:] if item is not u'']

    # 标的信息有序字典 
    etf_dict={}
    etf_dict=collections.OrderedDict()
    
    # 遍历所有工作表
    for i,code in zip(range(1,len(etf_list)+2),etf_list):
        table=xlr_f.sheet_by_index(i)
        
        # 获取标的的网格价格、买入数量、卖出数量
        price_list=[round(item,3) for item in table.col_values(2)[6:] if item is not u'']
        buy_list=[int(item) for item in table.col_values(4)[6:] if item is not u'']
        sell_list=[int(item) for item in table.col_values(5)[6:] if item is not u'']
               
        # 保存到字典
        etf_dict.update({code:{'name':table.name,
                           'value':{'price': price_list, 'buy': buy_list, 'sell': sell_list}}})
    return etf_dict


def get_wg_notice(etf_dict):    
    data_ist=[] 
        
    # 当前时间
    end_date=pd.datetime.today()
    
    # 遍历标的信息字典
    for code in etf_dict.keys():
        # 获取收盘价格
        current_price=get_price(normalize_code(code),end_date=end_date,count=1,
                        frequency='daily',fields=['close'])['close'].iloc[-1]
        current_price=round(current_price,3)
        
        # 获取名称、当前价格、网格价格表、买入数量表、卖出数量表
        name=etf_dict.get(code).get('name')
        price_list=etf_dict.get(code).get('value').get('price')
        buy_list=etf_dict.get(code).get('value').get('buy')
        sell_list=etf_dict.get(code).get('value').get('sell')
        
        # 价格格位计数器
        i=0
        
        # 最接近的价格
        near_price=0
        
        # 遍历价格列表
        for item in price_list:
            # 以当前价格查找最接近的格位价格
            if current_price >= item :
                # 找到则跳出循环
                near_price=item
                break
            # 档位计数器递增
            i+= 1  
        
        count=len(price_list)
        # 判断格位情况
        if i==count:  
            # 当前价格低于最后一格，即破网、满仓
            # print name,code,current_price,0,0,price_list[i-2],sell_list[i-2],'破网'
            data_ist.append([name,code,current_price,'-','满仓',price_list[i-2],sell_list[i-2],
                             '破网','-',price_list[-1],price_list[0],count])
        elif i==0:
            # 当前价格高于0格，即清仓
            # print name,code,current_price,price_list[i+1],buy_list[i+1],'-','清仓','清仓'
            data_ist.append([name,code,current_price,price_list[i+1],buy_list[i+1],'-','清仓',
                             '清仓','-',price_list[-1],price_list[0],count])
        elif i==(count-1):
            # 当前价格在最后一格前
            # print name,code,current_price,price_list[i],buy_list[i],price_list[i-2],sell_list[i-2] 
            data_ist.append([name,code,current_price,price_list[i],buy_list[i],price_list[i-2],sell_list[i-2],
                             '',near_price,price_list[-1],price_list[0],count])
        else:  
            # 当前价格在其余格内
            # print name,code,current_price,price_list[i+1],buy_list[i+1],price_list[i-1],sell_list[i-1]        
            data_ist.append([name,code,current_price,price_list[i+1],buy_list[i+1],price_list[i-1],sell_list[i-1],
                             '',near_price,price_list[-1],price_list[0],count])
    
    notice_df=pd.DataFrame(data=data_ist,columns=['名称','代码','当前价','买入价','买入数',
                                           '卖出价','卖出数','说明','当前格','末格','首格','格数'])    
    return notice_df
 
def get_wg_report(notice_df,simple=True):
    # 保留必要信息
    if simple:
        del notice_df['说明']
        del notice_df['当前格']
        del notice_df['末格']
        del notice_df['首格']
        del notice_df['格数']
    # 整理对齐方式
    notice_df['名称']='#'+notice_df['名称']
    notice_df['代码']='#'+notice_df['代码']
    notice_df.rename(columns={'名称':'$名称','代码':'$代码'},inplace=True)
    # 返回表格
    return notice_df.to_html(
        index=False,
        #justify='right',
        #classes='border="1" cellspacing="0" cellpadding="6" rules="rows" frame="void"'
                    )\
        .replace('<table border="1" class="dataframe">','<table border="1" cellspacing="0" cellpadding="6" rules="rows" frame="void" width="100%">')\
        .replace('<thead>','<thead style="font-size:14px">')\
        .replace('<tbody>','<tbody style="text-align:right;font-size:14px">')\
        .replace('<th></th>','<th>$代码</th>').replace('<tr>','<tr align="right">')\
        .replace('<th>$','<th align="left">').replace('<td>#','<td align="left">')
        


