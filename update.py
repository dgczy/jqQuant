
# -*- coding: utf-8 -*-

#导入基本包
import numpy as np
import pandas as pd

#研究、策略中区别配置
try:
    from kuanke.user_space_api import *
    _DATA_PATH='Data/'
except:
    _DATA_PATH='Data/'


from pf_idx import Index
from pf_mcr import Mcr
from pf_idu import Industry
from pf_plt import Plt
from pf_cmm import Cmm


def update():
    # 指数
    index=Index('csv',_DATA_PATH)
    index.data.update(index.pool.track)
    index.value.update(index.pool.value,[10,5,3,0],True)
    index.change.update(index.pool.track,['close','pe_e','pb_e'],True)
    
    # 板块
    plt=Plt('csv',_DATA_PATH)
    plt.data.update(plt.pool.track)
    plt.value.update(plt.pool.track,[10,5,3,0],True)
    plt.change.update(plt.pool.track,['dyr','pe','pb'],True)

    # 行业
    idu=Industry('csv',_DATA_PATH,project_name='sw1')
    idu.data.update(idu.pool.track)
    idu.value.update(idu.pool.track,[10,5,3,0],True)
    idu.change.update(idu.pool.track,['close','pe','pb'],True)
    
    # 商品
    cmm=Cmm('csv',_DATA_PATH)
    cmm.data.update(cmm.pool.track)
    cmm.value.update(cmm.pool.track,[10],True)
    cmm.change.update(cmm.pool.track,['close'],True)

    # 宏观
    mcr=Mcr('csv',_DATA_PATH)
    mcr.data.update(mcr.pool.track)