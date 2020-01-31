
# -*- coding: utf-8 -*-

import pandas as pd 
import numpy as np

from datetime import timedelta,date,datetime

from IPython.display import display
from ipywidgets import *
from IPython.display import display
# import qgrid
# qgrid.enable()


class TView(object):
       
    #名称对应值
    _value={
    # 字段
    u'PE-TTM':'pe', u'PB':'pb',u'PS-TTM':'ps',u'ROE':'roe',u'股息率':'dyr',u'波动率':'vlt',u'收益率':'roi',
    u'收盘点位':'close',u'收盘价格':'close',u'市值':'cap',
    # 算法
    u'等权平均':'e',u'加权平均':'w',u'中位数':'m',u'算数平均':'a',u'与指数编制相同':'e',
    # 时段
    u'10年':10,u'5年':5,u'3年':3,u'所有':0,u'1年':1,u'2年':2,
    # 线型
    u'日线':'D',u'周线':'W',u'月线':'M',
    # 高度线
    u'高度线':True,
    # 辅助图
    u'频率分布':'hist',u'高度对比':'high',
    # 十年期国债市盈率
    u'十年期国债市盈率':True,
    # 排序
    u'PE当前值':'pe',u'PB当前值':'pb',u'PS当前值':'ps',u'PE高度':'pe_ratio',u'PB高度':'pb_ratio',u'PS高度':'ps_ratio',
    '毛利率':'gross_profit','ROE':'roe','ROE均':'roe_mean','营复增':'revenue_grow','利复增':'profit_grow','股息率':'dyr',
    'PEG':'peg', '所属行业':'industry',
    u'当前值':'',u'高度':'ratio',u'升序':True,u'降序':False,
    # 其它
    u'综合':'all',u'全部':'all',u'否':'',u'否 ':False,u'无':False,u'无 ':'',u'全部显示 ':False,
    u'只显示比值':True,  
    u'相对强弱':'close',u'成交量比':'money',
    }
    
    #缺省参数
    _mode=[u'等权平均',u'加权平均',u'中位数',u'算数平均',u'全部']
    _years=[u'10年',u'5年',u'3年',u'所有']
    _right=[u'收盘点位',u'市值',u'否']
    _change=[u'日涨跌',u'本周、本月、本季、本年',u'近五年',u'波动率']
    _freq=[u'频率分布',u'无']
    _high=[u'高度对比',u'无']    
    _line=[u'高度线',u'无']    
    _period=[u'周线',u'日线',u'月线']    
    _y10=[u'十年期国债市盈率',u'无']  
    _sort2=[u'高度',u'当前值']
    _sort_type=[u'升序',u'降序']
    
    #对比指数
    _compare={
        u'000001 上证综指':'000001.SH',
        u'000985 中证全指':'000985.SH',
        u'399106 深证综指':'399106.SZ', 
        u'399106 中小板综':'399101.SZ',
        u'399106 创业板综':'399102.SZ',
        }

    
    #全市场指数对比  
    def show_line_ratio(self,chart,_code,_compare,_item,_years,_only_ratio,_period,value):
        #图表显示
        def get_chart(code,compare,item,years,only_ratio,period): 
            fig=chart.line_ratio(code,compare,self._value[item],self._value[years],
                                 widgets_item.label,self._value[only_ratio],self._value[period])

        #控件
        #全市场指数
        widgets_code1=widgets.Select(description=u'项目',layout=Layout(width='240px',height='60px'),margin=4,
            options=_code,value=_code.values()[0])
        #对比指数
        widgets_code2=widgets.Select(description=u'对比',layout=Layout(width='240px',height='60px'),margin=4,
            options=_compare,value=_compare.values()[0])
        #估值
        widgets_item=widgets.Dropdown(description=u'指标',layout=Layout(width='240px'),margin=4,
            options=_item,value=_item[0])
        #数据时段
        widgets_years=widgets.Dropdown(description=u'时段',layout=Layout(width='240px'),margin=4,
            options=_years,value=_years[0])
        #10y开关
        widgets_only_ratio=widgets.Dropdown(description=u'显示',margin=4,layout=Layout(width='240px'),
            options=_only_ratio,value=_only_ratio[1])
        #数据时段
        widgets_period=widgets.Dropdown(description=u'线型',layout=Layout(width='240px'),margin=4,
            options=_period,value=_period[1])


        #控件布局
        container=widgets.HBox([widgets_code1,widgets_code2,
                                widgets.VBox([widgets_item,widgets_only_ratio]),
                                widgets.VBox([widgets_years,widgets_period])
                               ])
        #绑定函数
        out=interactive_output(get_chart,dict(code=widgets_code1,compare=widgets_code2,item=widgets_item,years=widgets_years,
                       only_ratio=widgets_only_ratio,period=widgets_period))
        #显示组件
        display(container,out)
        #默认值
        if not value is None:
            widgets_code1.value=value

    
    #数据分析表
    def show_table(self,table,_code,_item,_mode,_sort1,_sort2,_sort_type,_years,value=None):

        #显示数据表
        def get_table(code,item,mode,sort1,sort2,sort_type,years):
            #修正mode
            tail='_%s'%(self._value[mode])
            #综合表
            if self._value[item]=='all': 
                #显示不同的排序控件
                widgets_sort1.disabled=False
                widgets_sort2.disabled=True
                sort_str=self._value[sort1] 
                if '_' in sort_str:
                    item_str=sort_str.split('_')[0]
                    sort_str=sort_str.split('_')[1]
                else:
                    item_str=sort_str
                    sort_str=''
            #分类表
            else:   
                #显示不同的排序控件
                widgets_sort1.disabled=True
                widgets_sort2.disabled=False
                #按照当前值或高度排序
                sort_str=self._value[sort2]
                item_str=self._value[item]
            
            #分类表
            if self._value[item] in ['pe','pb','ps']:
                df=table.value(self._code[code],item=item_str,
                            mode=self._value[mode],sort=sort_str,asc=self._value[sort_type],years=self._value[years])
                display(df)
            #综合表 
            else:    
                df=table.integrate(self._code[code],item=item_str,
                            mode=self._value[mode],sort=sort_str,asc=self._value[sort_type],years=self._value[years])
                display(df)

        #控件
        #指数分类
        widgets_code=widgets.Select(description=u'项目',layout=Layout(height='92px'),
            options=_code,value=_code[0])
        #数据表分类
        widgets_item=widgets.Dropdown(description=u'数据表',margin=4,
            options=_item,value=_item[0])
        #算法
        widgets_mode=widgets.Dropdown(description=u'算法',margin=4,
            options=_mode,value=_mode[0])
        #排序指标，适用于综合表
        widgets_sort1=widgets.Dropdown(description=u'排序',margin=4,
            options=_sort1,value=_sort1[0])
        #排序指标，适用于分类表
        widgets_sort2=widgets.Dropdown(description=u'　　',margin=4,disabled=True,
            options=_sort2,value=_sort2[0])
        #排序方向
        widgets_sort_type=widgets.Dropdown(description=u'方向',margin=4,
            options=_sort_type,value=_sort_type[0])
        #时段
        widgets_years=widgets.Dropdown(description=u'时段',margin=4,
            options=_years,value=_years[0])

        #控件布局
        sort_box=widgets.VBox([widgets_sort1,widgets_sort2,widgets_sort_type])
        container=widgets.HBox([widgets.HBox([widgets_code]),
                                widgets.VBox([widgets_item,widgets_mode,widgets_years]),
                                widgets.VBox([sort_box])
                               ])
        widgets_sort1.disabled=True
        widgets_sort2.disabled=False
        #绑定函数
#         out=interactive_output(get_table,code=widgets_code,item=widgets_item,mode=widgets_mode,
#                     sort1=widgets_sort1,sort2=widgets_sort2,sort_type=widgets_sort_type,
#                     years=widgets_years)
        out=interactive_output(get_table,{'code':widgets_code,'item':widgets_item,'mode':widgets_mode,
                    'sort1':widgets_sort1,'sort2':widgets_sort2,'sort_type':widgets_sort_type,
                    'years':widgets_years})
        #显示组件
        display(container,out)
        #默认值
        if not value is None:
            widgets_code.value=value
    
    
    
    def show_line_multi(self,chart,_code,_item,_mode,_years,_period,_assist,_y10,value=None):
        #显示图表
        def get_chart(code,item='pe',mode=None,years=10,period='W',assist='',y10=False):  
            #其它指数分类
            #在pe、pb
            if self._value[item] in ['pe','pb','ps']:
                widgets_mode.disabled=False
                widgets_assist.disabled=False
                widgets_code.height=112
                fig,start_date=chart.line_multi(self._code[code],item=self._value[item],
                                     mode=self._value[mode],years=self._value[years],
                                     title=widgets_code.label,period=self._value[period])  
                #在pe状态下，控制10年期国债市盈率
                if self._value[item] in ['pe']:
                    widgets_10y.disabled=False
                    if self._value[y10]:
                        chart.line_10y(fig,start_date)
                else:
                    widgets_10y.disabled=True 
                #显示相关图
                if self._value[assist]=='high':
                    chart.bar_multi(self._code[code],item=self._value[item],mode=self._value[mode],
                                 years=self._value[years],title=widgets_code.label)  
            #roe等  
            elif self._value[item] in ['roe','dyr']: 
                widgets_assist.disabled=False
                widgets_mode.disabled=True
                widgets_10y.disabled=True 
                widgets_period.disabled=False 
                widgets_code.height=112
                fig=chart.line_multi(self._code[code],item=self._value[item],mode='',
                                  years=self._value[years],title=widgets_code.label,period=self._value[period])
                if self._value[assist]=='high':
                    chart.bar_multi(self._code[code],item=self._value[item],mode='',
                                 years=self._value[years],title=widgets_code.label) 
            #波动率
            elif self._value[item] in ['vlt','roi']:  
                widgets_assist.disabled=True
                widgets_mode.disabled=True            
                widgets_10y.disabled=True 
                widgets_period.disabled=True 
                widgets_code.height=74
                chart.bar_multi(self._code[code],item=self._value[item],mode='',
                             years=self._value[years],title=widgets_code.label)

        #控件
        #指数分类
        widgets_code=widgets.Select(description=u'项目',layout=Layout(height='92px'),margin=4,
            options=_code,value=_code[0])
        #数据指标
        widgets_item=widgets.Dropdown(description=u'指标',margin=4,
            options=_item,value=_item[0])
        #算法
        widgets_mode=widgets.Dropdown(description=u'算法',margin=4,
            options=_mode,value=_mode[0])
        #时段
        widgets_years=widgets.Dropdown(description=u'时段',margin=4,
            options=_years,value=_years[0])
        #10y开关
        widgets_10y=widgets.Dropdown(description=u'对比',margin=4,
            options=_y10,value=_y10[1])
        #数据时段
        widgets_period=widgets.Dropdown(description=u'线型',margin=4,
            options=_period,value=_period[0])
        #辅助图
        widgets_assist=widgets.Dropdown(description=u'相关图',margin=4,
            options=_assist,value=_assist[1]) 

        #控件布局
        container=widgets.HBox([widgets.VBox([widgets_code]),
                        widgets.VBox([widgets_item,widgets_mode,widgets_10y]),
                        widgets.VBox([widgets_years,widgets_period,widgets_assist])
                       ])

        #绑定函数
        out=interactive_output(get_chart,dict(code=widgets_code,item=widgets_item,mode=widgets_mode,years=widgets_years,
                    period=widgets_period,assist=widgets_assist,y10=widgets_10y))
#         out=interactive_output(get_chart,{'code':widgets_code,'item':widgets_item,'mode':widgets_mode,'years':widgets_years,
#                     'period':widgets_period,'assist':widgets_assist,'y10':widgets_10y})
        #显示控件
        display(container,out)
        #默认值
        if not value is None:
            widgets_code.value=value

    
    
    #走势图        
    def show_line_single(self,chart,_code,_item,_mode,_years,_right,_period,_line,_assist,value=None):

        #显示走势图
        def get_chart(code,item,mode,years,right,period,line,assist):  
            if self._value[item] in ['roe','dyr']:
                widgets_mode.disabled=True
                widgets_line.disabled=True
                #显示roe、股息率走势
                fig=chart.line_one(code,item=self._value[item],mode='',years=self._value[years],
                     right=self._value[right],period=self._value[period],quantile=False)
                if self._value[assist]=='hist':
                        fig=chart.hist(code,item=self._value[item],mode='',years=self._value[years]) 
            else:
                widgets_mode.disabled=False
                #显示算法对比
                if self._value[mode]=='all':
                    widgets_line.disabled=True
                    fig=chart.line_mode(code,item=self._value[item],years=self._value[years],
                                           right=self._value[right],period=self._value[period])
                #显示pe、pb等走势及高度图
                else:
                    widgets_line.disabled=False
                    fig=chart.line_one(code,item=self._value[item],mode=self._value[mode],years=self._value[years],
                             right=self._value[right],period=self._value[period],quantile=self._value[line])
                    if self._value[assist]=='hist':
                        fig=chart.hist(code,item=self._value[item],mode=self._value[mode],years=self._value[years]) 

        #控件
        #列表
        widgets_code=widgets.Select(description=u'项目',layout=Layout(height='92px'),margin=4,
            options=_code,value=_code.values()[0])
        #估值
        widgets_item=widgets.Dropdown(description=u'指标',layout=Layout(width='344px'),margin=4,
            options=_item,value=_item[0])
        #算法
        widgets_mode=widgets.Dropdown(description=u'算法',layout=Layout(width='344px'),margin=4,
            options=_mode,value=_mode[0])
        #对比
        widgets_right=widgets.Dropdown(description=u'对比',layout=Layout(width='170px'),margin=4,
            options=_right,value=_right[0])
        #数据时段
        widgets_years=widgets.Dropdown(description=u'时段',width=50,margin=4,
            options=_years,value=_years[0])
        #高度线开关
        widgets_line=widgets.Dropdown(description=u'参照',margin=4,layout=Layout(width='170px'),
            options=_line,value=_line[0])
        #数据时段
        widgets_period=widgets.Dropdown(description=u'线型',width=50,margin=4,
            options=_period,value=_period[0])
        #辅助图
        widgets_assist=widgets.Dropdown(description=u'相关图',width=50,margin=4,
            options=_assist,value=_assist[1]) 

        #控件布局
        container=widgets.HBox([widgets.VBox([widgets_code]),
                                widgets.VBox([widgets_item,widgets_mode,widgets.HBox([widgets_right,widgets_line])]),
                                widgets.VBox([widgets_years,widgets_period,widgets_assist])])
        #函数绑定
        out=interactive_output(get_chart,dict(code=widgets_code,item=widgets_item,mode=widgets_mode,years=widgets_years,
                    right=widgets_right,period=widgets_period,line=widgets_line,assist=widgets_assist))
        #显示组件
        display(container,out)
        #默认值
        if not value is None:
            widgets_code.value=value
    
    
    #指数走势对比
    def show_line_compar(self,chart,_code,_item,_mode,_years,_period,_title):

        #显示图表
        def get_chart(code,item,mode,years,period):  
            #组织标题
            selecteds=len(widgets_code.label)
            if selecteds==1 or selecteds>8 :
                print u'至少选择2个、最多8个！'
                return

            if self._value[item] in ['pe','pb','ps'] :
                #pe、pb等对比
                widgets_mode.disabled=False
                real_mode=self._value[mode]
            else:   
                #股息率、roe对比
                widgets_mode.disabled=True
                real_mode=''
            fig=chart.line_multi(code,item=self._value[item],mode=real_mode,title=_title,
                              years=self._value[years],period=self._value[period]) 

        #控件
        #指数列表
        widgets_code=widgets.SelectMultiple(description=u'项目',width=150,height=75,rows=3,
            options=_code,value=[_code.values()[0]])
        #估值
        widgets_item=widgets.Dropdown(description=u'指标',width=80,margin=4,
            options=_item,value=_item[0])
        #算法
        widgets_mode=widgets.Dropdown(description=u'算法',width=80,margin=4,
            options=_mode,value=_mode[0])
        #数据时段
        widgets_years=widgets.Dropdown(description=u'时段',width=50,margin=4,
            options=_years,value=_years[0])
        #数据时段
        widgets_period=widgets.Dropdown(description=u'线型',width=50,margin=4,
            options=_period,value=_period[0])
        
        #控件布局
        container=widgets.HBox([widgets.VBox([widgets_code]),
                        widgets.VBox([widgets_item,widgets_mode]),
                        widgets.VBox([widgets_years,widgets_period])])
        #函数绑定
        out=interactive_output(get_chart,dict(code=widgets_code,item=widgets_item,mode=widgets_mode,
                        years=widgets_years,period=widgets_period))
        #显示组件
        display(container,out)

        
    def show_change(self,chart,_code,_item,_mode,value=None):

        # 显示图表
        def get_chart(code,item,cols=[]):  
            cols_list=[]
            if u'日涨跌' in cols:
                cols_list+=['近1日','5日','10日','20日','30日','60日','90日']
            if u'本周、本月、本季、本年' in cols:
                cols_list+=['本周','本月','本季','本年']    
            if u'近五年' in cols:
                year=datetime.now().year  
                cols_list+=[str(y)+'年' for y in range(year-5,year)]  
            if u'波动率' in cols:
                cols_list+=['波动率']   
            
            if self._value[item] in ['pe','pb','ps'] :
                real_mode=_mode
            else:   
                real_mode=''
            #主要跟踪指数不显示走势图
            fig=chart.heat(self._code[code],item=self._value[item],mode=real_mode,cols=cols_list,
                           title=widgets_code.label)

        # 控件
        # 分类
        widgets_code=widgets.Select(description=u'项目',layout=Layout(height='80px'),margin=4,
            options=_code,value=_code[0])

        # 指标
        widgets_item=widgets.Select(description=u'指标',layout=Layout(height='80px'),margin=4,
            options=_item,value=_item[0])

        # 阶段
        widgets_col=widgets.SelectMultiple(description=u'阶段',layout=Layout(height='80px'),margin=4,
            options=self._change,value=self._change)
        
        # 控件布局
        container=widgets.HBox([widgets_code,widgets_item,widgets_col])

        # 绑定函数
        out=interactive_output(get_chart,dict(code=widgets_code,item=widgets_item,cols=widgets_col))
        # 显示控件
        display(container,out)
        # 默认值
        if not value is None:
            widgets_code.value=value




