
# -*- coding: utf-8 -*-

import pandas as pd 
import numpy as np

from IPython.display import display
from ipywidgets import *

from vd import *


class idxView(TView):
    def __init__(self,project):
        TView.__init__(self) 
        self.__project=project
        
        # 项目
        self._code={    
        u'A股指数':self.__project.pool.hs.keys(),
        u'A股主要宽基指数':self.__project.pool.qsc.keys()+self.__project.pool.kj.keys(),u'A股主要窄基指数':self.__project.pool.zj.keys(),
        u'港股指数':self.__project.pool.hk.keys(),u'美股指数':self.__project.pool.us.keys(),u'海外市场指数':self.__project.pool.hw.keys(),
        u'主要跟踪指数':self.__project.pool.watch.keys(),u'全部指数':self.__project.pool.track.keys()
        }
    
        self._code_hs={'%s %s'%(code[0:6],self.__project.pool.track[code]):code for code in self.__project.pool.hs}
        self._code_hw={'%s %s'%(code[0:6],self.__project.pool.track[code]):code for code in self.__project.pool.hw if code in self.__project.pool.watch}
        
        self._sort1=[u'PE高度',u'PB高度',u'PS高度',u'PE当前值',u'PB当前值',u'PS当前值',u'ROE',u'股息率',u'波动率',u'收益率']
        self._item=[u'PE-TTM',u'PB',u'PS-TTM',u'ROE',u'股息率',]#u'波动率',u'收益率'


    #全市场指数对比  
    def _line_qsc(self,_item,_mode,_years,_period,_assist,_y10):
        #图表显示
        def get_chart(code,item,mode,years,period,assist,y10): 
            if self._value[item] in ['pe']:
                widgets_10y.visible=True
                y10=self._value[y10]
            else:
                widgets_10y.visible=False 
                y10=False
            fig=self.__project.value.chart.line_qsc('000902.SH',item=self._value[item],mode=self._value[mode],
                        code2=code,years=self._value[years],
                        period=self._value[period],y10=y10)    
            if self._value[assist]=='hist':
                fig=self.__project.value.chart.hist('000902.SH',item=self._value[item],mode=self._value[mode],
                        years=self._value[years])

        #控件
        #全市场指数
        widgets_code1=widgets.Select(description=u'全市场',layout=Layout(height='28px'),margin=4,
            options=[u'A股全市场指数'],value=u'A股全市场指数')
        #对比指数
        widgets_code2=widgets.Select(description=u'对比指数',layout=Layout(height='60px'),margin=4,
            options=self._compare,value='000001.SH') 
        #估值
        widgets_item=widgets.Dropdown(description=u'指标',margin=4,
            options=_item,value=_item[0])
        #算法
        widgets_mode=widgets.Dropdown(description=u'算法',margin=4,
            options=_mode,value=_mode[0])
        #数据时段
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
        container=widgets.HBox([widgets.VBox([widgets_code1,widgets_code2]),
                                widgets.VBox([widgets_item,widgets_mode,widgets_10y]),
                                widgets.VBox([widgets_years,widgets_period,widgets_assist])
                               ])

        #绑定函数
        out=interactive_output(get_chart,dict(code=widgets_code2,item=widgets_item,mode=widgets_mode,years=widgets_years,
                        period=widgets_period,assist=widgets_assist,y10=widgets_10y))

        #显示组件
        display(container,out)
        widgets_code2.value='399106.SZ'
    
    
    # 全市场指数
    def line_qsc(self):
        self._line_qsc(self._item[:3],self._mode[:4],self._years,self._period,
                       self._freq,self._y10)
 

    # 估值表    
    def table(self):
        code=[u'A股指数',u'A股主要宽基指数',u'A股主要窄基指数',u'海外市场指数',u'主要跟踪指数',u'全部指数']
        item=[u'PE-TTM',u'PB',u'PS-TTM',u'综合']
        value=u'全部指数'
        self.show_table(self.__project.value.table,code,item,self._mode[:4],self._sort1,self._sort2,
                        self._sort_type,self._years,value)
    
    
    # 指数走势对比
    def line_multi(self):
        code=[u'A股主要宽基指数',u'A股主要窄基指数',u'主要跟踪指数'] 
        value=u'A股主要窄基指数'
        self.show_line_multi(self.__project.value.chart,code,self._item,self._mode,self._years[:3],
                             self._period,self._high,self._y10,value)
        
        
    # 海外指数走势    
    def line_hs(self):
        self.show_line_single(self.__project.value.chart,self._code_hs,self._item[:5],self._mode,self._years,self._right,
                              self._period,self._line,self._freq,value=None)

    # 比值
    def line_ratio(self):
        item=[u'相对强弱',u'成交量比']
        years=[u'1年',u'2年',u'3年']
        only_ratio=[u'只显示比值',u'全部显示 ']
        self.show_line_ratio(self.__project.value.chart,self._code_hs,self._compare,item,years,only_ratio,self._period,None)   

        
    # 沪深指数走势
    def line_hw(self):
        item=[u'PE-TTM',u'股息率']
        mode=[u'与指数编制相同']
        period=[u'月线']
        right=[u'收盘点位',u'否']
        self.show_line_single(self.__project.value.chart,self._code_hw,item,mode,self._years,right,
                              period,self._line,self._freq,value=None)    
    
    # A股指数走势自定义对比
    def line_compar(self):  
        self.show_line_compar(self.__project.value.chart,self._code_hs,self._item,self._mode[:4],
                              self._years[:3],self._period,'A股指数对比')

    # 行情
    def change(self):
        code=[u'A股主要宽基指数',u'A股主要窄基指数',u'海外市场指数',u'主要跟踪指数']
        item=[u'收盘点位',u'PE-TTM', u'PB']
        value=u'主要跟踪指数'    
        self.show_change(self.__project.change.chart,code,item,'e',value) 
        
        
        
    