# -*- coding: utf-8 -*-
"""
Created on Thu Jul 19 17:03:47 2012

@author: musicalphysics
"""
import pandas as pds
import numpy as np
import pysat

platform = 'pysat'
name = 'testing'

def init(self):
    self.new_thing=True
    
def load(fnames, tag=None):
    # create an artifical satellite data set
    parts = fnames[0].split('/')
    yr = int('20'+parts[-1][0:2])
    month = int(parts[-3])
    day = int(parts[-2])
    date = pysat.datetime(yr,month,day)
    num = 86400 #int(tag)
    uts = np.arange(num)
    data = pysat.DataFrame(uts, columns=['uts'])


    # need to create simple orbits here. Have start of first orbit 
    # at 2009,1, 0 UT. 14.84 orbits per day	
    time_delta = date  - pysat.datetime(2009,1,1) 
    uts_root = np.mod(time_delta.total_seconds(), 5820)
    mlt = np.mod(uts_root+np.arange(num), 5820)*(24./5820.)
    data['mlt'] = mlt
    
    # do slt, 20 second offset from mlt
    uts_root = np.mod(time_delta.total_seconds()+20, 5820)
    data['slt'] = np.mod(uts_root+np.arange(num), 5820)*(24./5820.)

    index = pds.date_range(date,date+pds.DateOffset(hours=23,minutes=59,seconds=59),freq='S')
    data.index=index
    return data, pysat.Meta()

def list_files(tag=None, data_path=None):
    """Produce a fake list of files spanning a year"""
    
    index = pds.date_range(pysat.datetime(2008,1,1), pysat.datetime(2010,12,31)) 
    names = [ data_path+'/'+date.strftime('%D')+'.nofile' for date in index]
    return pysat.Series(names, index=index)
    
def download(start, stop, data_path=None,user=None, password=None):
    pass
#def meta():
#    
#    code = ['uts', 'yrdoy', 'mlt', 'slt']
#    index = np.arange(len(code))
#    label = ['uts', 'Year Day of Year', 'Magnetic Local Time', 'Solar Local Time']
#    units = ['s', ' ', 'hours', 'hours']
#    description = ['', '', '', '']
#    
#    d = {'code':code, 'index':index, 'label':label, 'units':units, 'description':description}
#    
#    return pysat.DataFrame(d, index=d['code'])