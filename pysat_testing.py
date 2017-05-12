# -*- coding: utf-8 -*-
"""
Produces fake instrument data for testing.
"""

import pandas as pds
import numpy as np
import pysat

platform = 'pysat'
name = 'testing'

meta = pysat.Meta()
meta['uts'] = {'units':'s', 'long_name':'Universal Time', 'custom':False}
meta['mlt'] = {'units':'hours', 'long_name':'Magnetic Local Time'}
meta['slt'] = {'units':'hours', 'long_name':'Solar Local Time'}

        
def init(self):
    self.new_thing=True        
                
def load(fnames, tag=None, sat_id=None):
    # create an artifical satellite data set
    parts = fnames[0].split('/')
    yr = int('20'+parts[-1][0:2])
    month = int(parts[-3])
    day = int(parts[-2])

    date = pysat.datetime(yr, month, day)
    num = 86400 if tag is '' else int(tag)
    num_array = np.arange(num)
    uts = num_array
    data = pysat.DataFrame(uts, columns=['uts'])


    # need to create simple orbits here. Have start of first orbit 
    # at 2009,1, 0 UT. 14.84 orbits per day	
    time_delta = date  - pysat.datetime(2009,1,1) 
    uts_root = np.mod(time_delta.total_seconds(), 5820)
    mlt = np.mod(uts_root+num_array, 5820)*(24./5820.)
    data['mlt'] = mlt
    
    # fake orbit number
    fake_delta = date  - pysat.datetime(2008,1,1) 
    fake_uts_root = fake_delta.total_seconds()

    data['orbit_num'] = ((fake_uts_root+num_array)/5820.).astype(int)
    
    # create a fake longitude, resets every 6240 seconds
    # sat moves at 360/5820 deg/s, Earth rotates at 360/86400, takes extra time 
    # to go around full longitude
    longitude = np.mod(uts_root+num_array, 6240)*(360./6240.)
    data['longitude'] = longitude
    
    latitude = 90.*np.cos(np.mod(uts_root+num_array, 5820)*(2.*np.pi/5820.)) 
    data['latitude'] = latitude
    
    # do slt, 20 second offset from mlt
    uts_root = np.mod(time_delta.total_seconds()+20, 5820)
    data['slt'] = np.mod(uts_root+num_array, 5820)*(24./5820.)
    
    # create latitude area for testing polar orbits

    # create some fake data to support testing of averaging routines
    mlt_int = data['mlt'].astype(int)
    long_int = (data['longitude']/15.).astype(int)
    data['dummy1'] = mlt_int
    data['dummy2'] = long_int
    data['dummy3'] = mlt_int + long_int*1000.
    data['dummy4'] = num_array
    
        
    index = pds.date_range(date, date+pds.DateOffset(seconds=num-1), freq='S')
    data.index=index[0:num]
    data.index.name = 'time'
    return data, meta.copy()

def list_files(tag=None, sat_id=None, data_path=None, format_str=None):
    """Produce a fake list of files spanning a year"""
    
    index = pds.date_range(pysat.datetime(2008,1,1), pysat.datetime(2010,12,31)) 
    names = [ data_path+date.strftime('%D')+'.nofile' for date in index]
    return pysat.Series(names, index=index)
    
def download(date_array, tag, sat_id, data_path=None, user=None, password=None):
    pass
