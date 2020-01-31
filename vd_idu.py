
# -*- coding: utf-8 -*-

import pandas as pd 
import numpy as np

from IPython.display import display
from ipywidgets import *

from vd import *


class iduView(TView):
    def __init__(self,project,project_name):
        TView.__init__(self) 
        self.__project=project
        self.__project_name=project_name
        
        self._code_list={'%s %s'%(code[0:6],name):code for code,name in self.__project.pool.track.items()}
        self._code={self.__project_name:self.__project.pool.track.keys()}
        
        self._mode=[u'无 ']
        self._sort1=[u'PE高度',u'PB高度',u'PE当前值',u'PB当前值',u'ROE',u'股息率',u'波动率',u'收益率']
    
    # 估值表    
    def table(self):
        code=[self.__project_name]
        item=[u'PE-TTM',u'PB',u'综合']
        self.show_table(self.__project.value.table,code,item,self._mode,self._sort1,self._sort2,
                        self._sort_type,self._years,value=None)        
       
    def line_one(self):
        item=[u'PE-TTM',u'PB',u'ROE',u'股息率']
        self.show_line_single(self.__project.value.chart,self._code_list,item,self._mode,self._years,self._right,
                              self._period,self._line,self._freq,value=None)    
    
    def line_compar(self):  
        item=[u'收盘点位',u'PE-TTM',u'PB',u'ROE',u'股息率']
        self.show_line_compar(self.__project.value.chart,self._code_list,item,self._mode,self._years[:3],self._period,
                             self.__project_name)

    # 行情
    def change(self):
        code=[self.__project_name]
        item=[u'收盘价格',u'PE-TTM', u'PB']
        self.show_change(self.__project.change.chart,code,item,'',None) 
        
        
        
    