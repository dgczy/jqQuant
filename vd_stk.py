
# -*- coding: utf-8 -*-

import pandas as pd 
import numpy as np

from IPython.display import display
from ipywidgets import *


from vd import *


class stkView(TView):
    def __init__(self,project,project_name):
        TView.__init__(self) 
        self.__project=project
        self.__project_name=project_name
         
        self._code_list={'%s %s'%(code[0:6],name):code for code,name in self.__project.pool.track.items()}        
        self._code={self.__project_name:self.__project.pool.track.keys()}
        self._mode=[u'无 ']
        self._years=[u'5年',u'3年',u'1年']
        
       
    def table(self):
        code=[self.__project_name] 
        item=[u'PE-TTM',u'PB',u'PS-TTM',u'综合']
        years=[u'5年',u'3年',u'1年']
        sort1=[u'PE高度',u'PB高度',u'PE当前值',u'PB当前值','毛利率','ROE','ROE均','营复增','利复增','股息率','PEG','所属行业']
        self.show_table(self.__project.value.table,code,item,self._mode,sort1,self._sort2,
                        self._sort_type,years,value=None)
        
    
    def line_one(self):
        item=[u'PE-TTM',u'PB',u'PS-TTM',u'ROE',u'股息率']
        self.show_line_single(self.__project.value.chart,self._code_list,item,self._mode,self._years,self._right,
                              self._period,self._line,self._freq,value=None)
           
       
    def line_compar(self):  
        item=[u'收盘点位',u'PE-TTM',u'PB',u'PS-TTM',u'ROE',u'股息率']
        self.show_line_compar(self.__project.value.chart,self._code_list,item,self._mode,self._years,self._period,
                             self.__project_name)

    
    def change(self):
        code=[self.__project_name]
        item=[u'收盘价格',u'PE-TTM', u'PB']
        self.show_change(self.__project.change.chart,code,item,'',None) 
        
        
        
    