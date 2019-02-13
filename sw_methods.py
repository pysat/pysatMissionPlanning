# -*- coding: utf-8 -*-.
"""Provides default routines for solar wind and geospace indices

"""

from __future__ import print_function
from __future__ import absolute_import

import pandas as pds
import numpy as np
import pysat

def combine_kp(standard_inst=None, recent_inst=None, forecast_inst=None,
               start=None, stop=None, fill_val=np.nan):
    """ Combine the output from the different Kp sources for a range of dates

    Parameters
    ----------
    standard_inst : (pysat.Instrument or NoneType)
        Instrument object containing data for the 'sw' platform, 'kp' name,
        and '' tag or None to exclude (default=None)
    recent_inst : (pysat.Instrument or NoneType)
        Instrument object containing data for the 'sw' platform, 'kp' name,
        and 'recent' tag or None to exclude (default=None)
    forecast_inst : (pysat.Instrument or NoneType)
        Instrument object containing data for the 'sw' platform, 'kp' name,
        and 'forecast' tag or None to exclude (default=None)
    start : (dt.datetime or NoneType)
        Starting time for combining data, or None to use earliest loaded
        date from the pysat Instruments (default=None)
    stop : (dt.datetime)
        Ending time for combining data, or None to use the latest loaded date
        from the pysat Instruments (default=None)
    fill_val : (int or float)
        Desired fill value (since the standard instrument fill value differs
        from the other sources) (default=np.nan)

    Returns
    -------
    kp_inst : (pysat.Instrument)
        Instrument object containing Kp observations for the desired period of
        time, merging the standard, recent, and forecasted values based on
        their reliability

    Notes
    -----
    Merging prioritizes the standard data, then the recent data, and finally
    the forecast data

    Will not attempt to download any missing data, but will load data

    """
    notes = "Combines data from"

    # Create an ordered list of the Instruments, excluding any that are None
    all_inst = list()
    tag = 'combined'
    inst_flag = None
    if standard_inst is not None:
        all_inst.append(standard_inst)
        tag += '_standard'
        if inst_flag is None:
            inst_flag = 'standard'

    if recent_inst is not None:
        all_inst.append(recent_inst)
        tag += '_recent'
        if inst_flag is None:
            inst_flag = 'recent'

    if forecast_inst is not None:
        all_inst.append(forecast_inst)
        tag += '_forecast'
        if inst_flag is None:
            inst_flag = 'forecast'

    if len(all_inst) < 2:
        raise ValueError("need at two Kp Instrument objects to combine them")

    # If the start or stop times are not defined, get them from the Instruments
    if start is None:
        stimes = [inst.index.min() for inst in all_inst if len(inst.index) > 0]
        start = min(stimes) if len(stimes) > 0 else None

    if stop is None:
        stimes = [inst.index.max() for inst in all_inst if len(inst.index) > 0]
        stop = max(stimes) if len(stimes) > 0 else None
        stop += pds.DateOffset(days=1)
        
    if start is None or stop is None:
        raise ValueError("must either load in Instrument objects or provide" +
                         " starting and ending times")

    # Initialize the output instrument
    kp_inst = pysat.Instrument()
    kp_inst.platform = all_inst[0].platform
    kp_inst.name = all_inst[0].name
    kp_inst.tag = tag
    kp_inst.date = start
    kp_inst.doy = int(start.strftime("%j"))
    kp_inst.meta = pysat.Meta()
    pysat.instruments.sw_kp.initialize_kp_metadata(kp_inst.meta, 'Kp',
                                                   fill_val=fill_val)

    kp_times = list()
    kp_values = list()

    # Cycle through the desired time range
    itime = start
    while itime < stop and inst_flag is not None:
        # Load and save the standard data for as many times as possible
        if inst_flag == 'standard':
            standard_inst.load(date=itime)

            if notes.find("standard") < 0:
                notes += " the {:} source ({:} to ".format(inst_flag,
                                                           itime.date())

            if len(standard_inst.index) == 0:
                inst_flag = 'forecast' if recent_inst is None else 'recent'
                notes += "{:})".format(itime.date())
            else:
                kp_times.extend(list(standard_inst.index))
                kp_values.extend(list(standard_inst['Kp']))
                itime = kp_times[-1] + pds.DateOffset(hours=3)

        # Load and save the recent data for as many times as possible
        if inst_flag == 'recent':
            # Determine which files should be loaded
            if len(recent_inst.index) == 0:
                files = np.unique(recent_inst.files.files[itime:stop])
            else:
                files = [None] # No load needed, if already initialized

            # Cycle through all possible files of interest, saving relevant data
            for filename in files:
                if filename is not None:
                    recent_inst.load(fname=filename)

                if notes.find("recent") < 0:
                    notes += " the {:} source ({:} to ".format(inst_flag,
                                                               itime.date())

                # Determine which times to save
                local_fill_val = recent_inst.meta['Kp'].fill
                good_times = ((recent_inst.index >= itime) &
                              (recent_inst.index < stop))
                good_vals = recent_inst['Kp'][good_times] != local_fill_val

                # Save output data and cycle time
                kp_times.extend(list(recent_inst.index[good_times][good_vals]))
                kp_values.extend(list(recent_inst['Kp'][good_times][good_vals]))
                itime = kp_times[-1] + pds.DateOffset(hours=3)

            inst_flag = 'forecast' if forecast_inst is not None else None
            notes += "{:})".format(itime.date())

        # Load and save the forecast data for as many times as possible
        if inst_flag == "forecast":
            # Determine which files should be loaded
            if len(forecast_inst.index) == 0:
                files = np.unique(forecast_inst.files.files[itime:stop])
            else:
                files = [None] # No load needed, if already initialized

            # Cycle through all possible files of interest, saving relevant data
            for filename in files:
                if filename is not None:
                    forecast_inst.load(fname=filename)

                if notes.find("forecast") < 0:
                    notes += " the {:} source ({:} to ".format(inst_flag,
                                                               itime.date())

                # Determine which times to save
                local_fill_val = forecast_inst.meta['Kp'].fill
                good_times = ((forecast_inst.index >= itime) &
                              (forecast_inst.index < stop))
                good_vals = forecast_inst['Kp'][good_times] != local_fill_val

                # Save desired data and cycle time
                kp_times.extend(list(forecast_inst.index[good_times][good_vals]))
                kp_values.extend(list(forecast_inst['Kp'][good_times][good_vals]))
                itime = kp_times[-1] + pds.DateOffset(hours=3)
            notes += "{:})".format(itime.date())

            inst_flag = None

    if inst_flag is not None:
        notes += "{:})".format(itime.date())

    # Determine if the beginning or end of the time series needs to be padded
    freq = pysat.utils.calc_freq(kp_times)
    date_range = pds.date_range(start=start, end=stop-pds.DateOffset(days=1),
                                freq=freq)

    if date_range[0] < kp_times[0]:
        # Extend the time and value arrays from their beginning with fill values
        itime = abs(date_range - kp_times[0]).argmin()
        kp_times.reverse()
        kp_values.reverse()
        extend_times = list(date_range[:itime])
        extend_times.reverse()
        kp_times.extend(extend_times)
        kp_values.extend([fill_val for kk in extend_times])
        kp_times.reverse()
        kp_values.reverse()

    if date_range[-1] > kp_times[-1]:
        # Extend the time and value arrays from their end with fill values
        itime = abs(date_range - kp_times[-1]).argmin() + 1
        extend_times = list(date_range[itime:])
        kp_times.extend(extend_times)
        kp_values.extend([fill_val for kk in extend_times])

    # Save output data
    kp_inst.data = pds.DataFrame(kp_values, columns=['Kp'], index=kp_times)

    # Resample the output data, filling missing values
    if(date_range.shape != kp_inst.index.shape or
       abs(date_range - kp_inst.index).max().total_seconds() > 0.0):
        kp_inst.data = kp_inst.data.resample(freq).fillna(method=None)
        if np.isfinite(fill_val):
            kp_inst.data[np.isnan(kp_inst.data)] = fill_val

    # Update the metadata notes for this custom procedure
    notes += ", in that order"
    kp_inst.meta.__setitem__('Kp', {kp_inst.meta.notes_label: notes})

    return kp_inst


def combine_f107(standard_inst, forecast_inst, start=None, stop=None):
    """ Combine the output from the measured and forecasted F10.7 sources

    Parameters
    ----------
    standard_inst : (pysat.Instrument or NoneType)
        Instrument object containing data for the 'sw' platform, 'f107' name,
        and '', 'all', 'prelim', or 'daily' tag
    forecast_inst : (pysat.Instrument or NoneType)
        Instrument object containing data for the 'sw' platform, 'f107' name,
        and 'prelim', '45day' or 'forecast' tag
    start : (dt.datetime or NoneType)
        Starting time for combining data, or None to use earliest loaded
        date from the pysat Instruments (default=None)
    stop : (dt.datetime)
        Ending time for combining data, or None to use the latest loaded date
        from the pysat Instruments (default=None)

    Returns
    -------
    f107_inst : (pysat.Instrument)
        Instrument object containing F10.7 observations for the desired period
        of time, merging the standard, 45day, and forecasted values based on
        their reliability

    Notes
    -----
    Merging prioritizes the standard data, then the 45day data, and finally
    the forecast data

    Will not attempt to download any missing data, but will load data

    """
    # Initialize metadata and flags
    notes = "Combines data from"
    stag = standard_inst.tag if len(standard_inst.tag) > 0 else 'default'
    tag = 'combined_{:s}_{:s}'.format(stag, forecast_inst.tag)
    inst_flag = 'standard'

    # If the start or stop times are not defined, get them from the Instruments
    if start is None:
        stimes = [inst.index.min() for inst in [standard_inst, forecast_inst]
                  if len(inst.index) > 0]
        start = min(stimes) if len(stimes) > 0 else None

    if stop is None:
        stimes = [inst.index.max() for inst in [standard_inst, forecast_inst]
                  if len(inst.index) > 0]
        stop = max(stimes) + pds.DateOffset(days=1) if len(stimes) > 0 else None

    if start is None or stop is None:
        raise ValueError("must either load in Instrument objects or provide" +
                         " starting and ending times")

    if start >= stop:
        raise ValueError("date range is zero or negative")

    # Initialize the output instrument
    f107_inst = pysat.Instrument()
    f107_inst.platform = standard_inst.platform
    f107_inst.name = standard_inst.name
    f107_inst.tag = tag
    f107_inst.date = start
    f107_inst.doy = int(start.strftime("%j"))
    fill_val = None

    f107_times = list()
    f107_values = list()

    # Cycle through the desired time range
    itime = start

    while itime < stop and inst_flag is not None:
        # Load and save the standard data for as many times as possible
        if inst_flag == 'standard':
            # Test to see if data loading is needed
            if not np.any(standard_inst.index == itime):
                if standard_inst.tag == 'daily':
                    # Add 30 days
                    standard_inst.load(date=itime+pds.DateOffset(days=30))
                else:
                    standard_inst.load(date=itime)

            good_times = ((standard_inst.index >= itime) &
                          (standard_inst.index < stop))

            if notes.find("standard") < 0:
                notes += " the {:} source ({:} to ".format(inst_flag,
                                                           itime.date())

            if np.any(good_times):
                if fill_val is None:
                    f107_inst.meta = standard_inst.meta
                    fill_val = f107_inst.meta['f107'].fill
                
                good_vals = standard_inst['f107'][good_times] != fill_val
                f107_times.extend(list(standard_inst.index[good_times][good_vals]))
                f107_values.extend(list(standard_inst['f107'][good_times][good_vals]))
                itime = f107_times[-1] + pds.DateOffset(days=1)
            else:
                inst_flag = 'forecast'
                notes += "{:})".format(itime.date())

        # Load and save the forecast data for as many times as possible
        if inst_flag == "forecast":
            # Determine which files should be loaded
            if len(forecast_inst.index) == 0:
                files = np.unique(forecast_inst.files.files[itime:stop])
            else:
                files = [None] # No load needed, if already initialized

            # Cycle through all possible files of interest, saving relevant data
            for filename in files:
                if filename is not None:
                    forecast_inst.load(fname=filename)

                if notes.find("forecast") < 0:
                    notes += " the {:} source ({:} to ".format(inst_flag,
                                                               itime.date())

                # Check in case there was a problem with the standard data
                if fill_val is None:
                    f107_inst.meta = forecast_inst.meta
                    fill_val = f107_inst.meta['f107'].fill

                # Determine which times to save
                good_times = ((forecast_inst.index >= itime) &
                              (forecast_inst.index < stop))
                good_vals = forecast_inst['f107'][good_times] != fill_val

                # Save desired data and cycle time
                f107_times.extend(list(forecast_inst.index[good_times][good_vals]))
                f107_values.extend(list(forecast_inst['f107'][good_times][good_vals]))
                itime = f107_times[-1] + pds.DateOffset(days=1)

            notes += "{:})".format(itime.date())

            inst_flag = None

    if inst_flag is not None:
        notes += "{:})".format(itime.date())

    # Determine if the beginning or end of the time series needs to be padded
    freq = pysat.utils.calc_freq(f107_times)
    date_range = pds.date_range(start=start, end=stop-pds.DateOffset(days=1),
                                freq=freq)

    if date_range[0] < f107_times[0]:
        # Extend the time and value arrays from their beginning with fill values
        itime = abs(date_range - f107_times[0]).argmin()
        f107_times.reverse()
        f107_values.reverse()
        extend_times = list(date_range[:itime])
        extend_times.reverse()
        f107_times.extend(extend_times)
        f107_values.extend([fill_val for kk in extend_times])
        f107_times.reverse()
        f107_values.reverse()

    if date_range[-1] > f107_times[-1]:
        # Extend the time and value arrays from their end with fill values
        itime = abs(date_range - f107_times[-1]).argmin() + 1
        extend_times = list(date_range[itime:])
        f107_times.extend(extend_times)
        f107_values.extend([fill_val for kk in extend_times])

    # Save output data
    f107_inst.data = pds.DataFrame(f107_values, columns=['f107'],
                                   index=f107_times)

    # Resample the output data, filling missing values
    if(date_range.shape != f107_inst.index.shape or
       abs(date_range - f107_inst.index).max().total_seconds() > 0.0):
        f107_inst.data = f107_inst.data.resample(freq).fillna(method=None)
        if np.isfinite(fill_val):
            f107_inst.data[np.isnan(f107_inst.data)] = fill_val

    # Update the metadata notes for this custom procedure
    notes += ", in that order"
    f107_inst.meta.__setitem__('f107', {f107_inst.meta.notes_label: notes})

    return f107_inst

def calc_daily_Ap(ap_inst, ap_name='3hr_ap', daily_name='Ap',
                  running_name=None):
    """ Calculate the daily Ap index from the 3hr ap index

    Parameters
    ----------
    ap_inst : (pysat.Instrument)
        pysat instrument containing 3-hourly ap data
    ap_name : (str)
        Column name for 3-hourly ap data (default='3hr_ap')
    daily_name : (str)
        Column name for daily Ap data (default='Ap')
    running_name : (str or NoneType)
        Column name for daily running average of ap, not output if None
        (default=None)

    Returns
    -------
    Void : updates intrument to include daily Ap index under daily_name

    Notes
    -----
    Ap is the mean of the 3hr ap indices measured for a given day

    Option for running average is included since this information is used
    by MSIS when running with sub-daily geophysical inputs

    """

    # Test that the necessary data is available
    if ap_name not in ap_inst.data.columns:
        raise ValueError("bad 3-hourly ap column name: {:}".format(ap_name))

    # Test to see that we will not be overwritting data
    if daily_name in ap_inst.data.columns:
        raise ValueError("daily Ap column name already exists: " + daily_name)

    # Calculate the daily mean value
    ap_mean = ap_inst[ap_name].rolling(window='1D', min_periods=8).mean()

    if running_name is not None:
        ap_inst[running_name] = ap_mean

        meta_dict = {ap_inst.meta.units_label: '',
                     ap_inst.meta.name_label: running_name,
                     ap_inst.meta.desc_label: "running daily Ap index",
                     ap_inst.meta.plot_label: "24-h average ap",
                     ap_inst.meta.axis_label: "24-h average ap",
                     ap_inst.meta.scale_label: 'linear',
                     ap_inst.meta.min_label: 0,
                     ap_inst.meta.max_label: 400,
                     ap_inst.meta.fill_label:
                     ap_inst.meta[ap_name][ap_inst.meta.fill_label],
                     ap_inst.meta.notes_label: '24-h running average of '
                     + '3-hourly ap indices'}

        ap_inst.meta.__setitem__(running_name, meta_dict)

    # Resample, backfilling so that each day uses the mean for the data from
    # that day only
    #
    # Pad the data so the first day will be backfilled
    ap_pad = pds.Series(np.full(shape=(1,), fill_value=np.nan),
                        index=[ap_mean.index[0] - pds.DateOffset(hours=3)])
    # Extract the mean that only uses data for one day
    ap_sel = ap_pad.combine_first(ap_mean[[i for i,tt in
                                           enumerate(ap_mean.index)
                                           if tt.hour == 21]])
    # Backfill this data
    ap_data = ap_sel.resample('3H').backfill()

    # Save the output for the original time range
    ap_inst[daily_name] = pds.Series(ap_data[1:], index=ap_data.index[1:])

    
    # Add metadata
    meta_dict = {ap_inst.meta.units_label: '',
                 ap_inst.meta.name_label: 'Ap',
                 ap_inst.meta.desc_label: "daily Ap index",
                 ap_inst.meta.plot_label: "Ap",
                 ap_inst.meta.axis_label: "Ap",
                 ap_inst.meta.scale_label: 'linear',
                 ap_inst.meta.min_label: 0,
                 ap_inst.meta.max_label: 400,
                 ap_inst.meta.fill_label:
                 ap_inst.meta[ap_name][ap_inst.meta.fill_label],
                 ap_inst.meta.notes_label: 'Ap daily mean calculated from '
                 + '3-hourly ap indices'}

    ap_inst.meta.__setitem__(daily_name, meta_dict)

    return
