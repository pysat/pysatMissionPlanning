# -*- coding: utf-8 -*-
"""Supports the Plasma Analyzer Instrument (Instrument Analyseur de Plasma, or
IAP) onboard the Detection of Electro-Magnetic Emissions Transmitted from
 Earthquake Regions (DEMETER) Microsatellite.

The IAP consists of a Velocity Analyzer (ADV) and Retarding potential analyzer
(APR) to provide plasma velocities, ion density and temperature, and
satellite potential.  The computation of the ion plasma parameters works well
when there are at least two ions being considered.  Also, the ADV requires
currents of at least 1 nA to produce believable measurements.  The IAP was run
in both survey and burst mode.

Downloads data from the Plasma physics data center (Centre de donees de la
physique des plasmas, CDPP), the French national data center for natural
plasmas of the solar system.  This data product requires registration and user
initiated downloading after ordering a data product.

Parameters
----------
platform : string
    'demeter'
name : string
    'iap'
tag : string
    'survey' or 'burst'
sat_id : string
    None supported

Example
-------
    import pysat
    demeter = pysat.Instrument('demeter', 'iap', 'survey', clean_level='none')
    demeter.load(2009,363)

"""

from __future__ import print_function, absolute_import

import sys
import functools
import pandas as pds
import numpy as np

import pysat
from . import demeter_methods

platform = 'demeter'
name = 'iap'
tags = {'survey': 'Survey mode',
        'burst': 'Burst mode'}
sat_ids = {'': list(tags.keys())}
test_dates = {'': {'survey': pysat.datetime(2010, 1, 1)}}

apid = {'survey': 1140, 'burst': 1139}

multi_file_day = True

# Use default demeter download method
download = demeter_methods.download

# use default demeter list_remote_files method
# as of 04 Dec 2018 this is a placeholder
list_remote_files = demeter_methods.list_remote_files


def init(self):
    print(' '.join(("When using this data please include a version of the,"
                    "acknowledgement outlined in the metadata attribute",
                    "'info.acknowledgements'.  We recommend that data users",
                    "contact the experiment PI early in their study. ",
                    "Experiment reference information is available in the",
                    "metadata attribute 'info.reference'")))


def list_files(tag="survey", sat_id='', data_path=None, format_str=None,
               index_start_time=True):
    """Return a Pandas Series of every file for DEMETER IAP satellite data

    Parameters
    ----------
    tag : (string)
        Denotes type of file to load.  Accepted types are 'survey'; 'burst'
        will be added in the future.  (default='survey')
    sat_id : (string or NoneType)
        Specifies the satellite ID for a constellation.  Not used.
        (default='')
    data_path : (string or NoneType)
        Path to data directory.  If None is specified, the value previously
        set in Instrument.files.data_path is used.  (default=None)
    format_str : (string or NoneType)
        User specified file format.  If None is specified, the default
        formats associated with the supplied tags are used. (default=None)
    index_start_time : (bool)
        Determine time index using file start time (True) or end time (False)
        (default=True)

    Returns
    -------
    pysat.Files.from_os : (pysat._files.Files)
        A class containing the verified available files

    """

    if format_str is None:
        if tag not in list(apid.keys()):
            raise ValueError('unknown {:s} {:s} tag: {:s}'.format(platform,
                                                                  name, tag))
        if index_start_time:
            time_str = '{year:4d}{month:02d}{day:02d}_??????_????????_??????'
        else:
            time_str = '????????_??????_{year:4d}{month:02d}{day:02d}_??????'

        format_str = ''.join(('DMT_N1_{:d}_??????_'.format(apid[tag]),
                              time_str, '.DAT'))

    return pysat.Files.from_os(data_path=data_path, format_str=format_str)


def load(fnames, tag='survey', sat_id=''):
    """ Load DEMETER IAP data

    Parameters
    ----------
    fnames : (list)
        List of file names
    tag : (string)
        Denotes type of file to load.  Accepted types are 'survey'; 'burst'
        will be added in the future.  (default='survey')
    sat_id : (string or NoneType)
        Specifies the satellite ID for a constellation.  Not used.
        (default='')

    Returns
    -------
    data : (pds.DataFrame)
        DataFrame of DEMETER satellite data
    meta :
        Metadata object

    """

    if len(fnames) == 0:
        print('need list of filenames')
        return pysat.DataFrame(None), None

    # Load the desired data and cast as a DataFrame
    data = list()
    for fname in fnames:
        fdata, fmeta = demeter_methods.load_binary_file(fname,
                                                        load_experiment_data)
        data.extend(fdata)

    data = np.vstack(data)
    data = pysat.DataFrame(data, index=data[:, 3], columns=fmeta['data names'])

    # Assign metadata
    if len(data.columns) > 0:
        meta = demeter_methods.set_metadata(name, fmeta)
    else:
        meta = pysat.Meta(None)

    return data, meta


def load_experiment_data(fhandle):
    """ Load survey mode binary file

    Parameters
    ----------
    fhandle : (file)
        file handle

    Returns
    -------
    data : np.ndarray
        Numpy array of data values containing: housekeeping and status,
        H+ density, He+ density, O+ density, Ion tempearture,
        ion velocity along Oz axis, angle between ion velocity and -Oz axis,
        angle between projection of ion velocity on the xOy plane and Ox axis,
        satellite potential
    meta : dict
        Dictionary with meta data for keys: 'data type', 'data units',
        'data names'

    """
    import codecs  # ensures encode is python 2/3 compliant

    chunk = fhandle.read(108)

    data = list()
    data_names = list()
    data_units = dict()
    # Load the house-keeping and status flags
    for i in range(32):
        data.append(int(codecs.encode(chunk[10+i], 'hex'), 16))
        data_names.append('status_flag_{:02d}'.format(i))
        data_units[data_names[-1]] = "N/A"

    data.append(demeter_methods.bytes_to_float(chunk[42:46]))  # Time resolution
    data_names.append('time_resolution')
    data_units[data_names[-1]] = "s"

    # Load the rest of the data
    i = 76
    exp_data = ['H+_density', 'He+_density', 'O+_density', 'Ion_temperature',
                'iv_Oz', 'iv_negOz_angle', 'iv_xOy_Ox_angle',
                'satellite_potential']
    while i < 108:
        data.append(demeter_methods.bytes_to_float(chunk[i:i+4]))
        i += 4
    data_names.extend(exp_data)

    for dname in exp_data:
        if dname.find('density') > 0:
            data_units[dname] = chunk[46:52]
        elif dname.find('temperature') > 0:
            data_units[dname] = chunk[52:58]
        elif dname.find('potential') > 0:
            data_units[dname] = chunk[64:70]
        elif dname.find('angle') > 0:
            data_units[dname] = chunk[70:76]
        elif dname.find('iv') == 0:
            data_units[dname] = chunk[58:64]

    # Load the metadata
    meta = {'data type': chunk[0:10], 'data names': data_names,
            'data units': data_units}

    return data, meta


def clean(iap):
    """ Remove data to the desired level of cleanliness

    Parameters
    ----------
    iap : pysat.Instrument
        DEMETER IAP instrument class object

    Return
    ------
    Updates data by removing times where data quality fails the conditions
    for the specified cleaning level

    Notes
    -----
    clean : only data when at least two ions are considered and currents >= 1nA
    dusty : not applicable
    dirty : not applicable
    """

    if iap.clean_level in ['dusty', 'dirty']:
        print(''.join("'dusty' and 'dirty' levels not supported, ",
                      "defaulting to 'clean'"))
        iap.clean_level = 'clean'

    if iap.clean_level == 'clean':
        # Determine the number of ions present, using a threshold for the
        # minimum significant density for one of the three ion species
        oplus_thresh = 5.0e2  # From Berthelier et al. 2006
        nions = np.zeros(shape=iap.data.index.shape)
        for i, oplus in enumerate(iap.data['O+_density']):
            if oplus >= oplus_thresh:
                nions[i] += 1

                # From Berthelier et al. 2006
                if iap.data['H+_density'][i] > oplus * 0.02:
                    nions[i] += 1
                if iap.data['He+_density'][i] > oplus * 0.02:
                    nions[i] += 1

                # Need Level 0 files to select data with J >= 1 nA
                print("WARNING: Level 0 files needed to finish cleaning data")

                # Select times with at least two ion species
                idx, = np.where(nions > 1)
    else:
        idx = slice(0, iap.index.shape[0])

    iap.data = iap[idx]

    return


def add_drift_sat_coord(iap):
    """ Calculate the ion velocity in satellite x,y,z coordinates

    Parameters
    ----------
    iap : pysat.Instrument
        DEMETER IAP instrument class object

    Return
    ------
    Adds data values iv_Ox, iv_Oy

    """

    # Because np.radians isn't working for data coming from the DataFrame :(
    rad = np.array([np.radians(rr) for rr in iap['iv_negOz_angle']])
    vxy = - iap['iv_Oz'] * np.tan(rad)
    rad = np.array([np.radians(rr) for rr in iap['iv_xOy_Ox_angle']])

    iap['iv_Ox'] = vxy * np.cos(rad)
    iap['iv_Oy'] = vxy * np.sin(rad)
    iap.meta.data.units['iv_Ox'] = iap.meta.data.units['iv_Oz']
    iap.meta.data.units['iv_Oy'] = iap.meta.data.units['iv_Oz']

    # Because the ADV instrument is not fully aligned with the axis of the
    # satellite, reposition into satellite coordinates
    # (IS THIS ALREADY CORRECTED IN FILES?)
    print("WARNING the ADV instrument is not fully aligned with the axis of "
          + "the satellite and this may not have been corrected")

    return


def add_drift_lgm_coord(iap):
    """ Calcuate the ion velocity in local geomagneic coordinates

    Parameters
    ----------
    iap : pysat.Instrument
        DEMETER IAP instrument class object

    Return
    ------
    Adds data values iv_par (parallel to B vector at satellite),
    iv_pos (perpendictular to B, in the plane of the satellite),
    iv_perp (completes the coordinate system).  If iv_Ox and iv_Oy
    do not exist yet, adds them as well

    """

    sc_keys = ['iv_Ox', 'iv_Oy', 'iv_Oz']

    # Test for ion velocity in spacecraft coordinates, add if not present
    if not np.all([kk in iap.data.keys() for kk in sc_keys]):
        add_drift_sat_coord(iap)

    # Construct a numpy array of the velocity vectors
    sc_vel = iap.data[sc_keys].values

    # Construct a numpy array of the rotational matrix that convert
    # from satellite to local geomagnetic coordinates.  Then calculate the
    # velocity in local geomagnetic coordinates
    lgm_vel = list()
    for i, ind in enumerate(iap.data.index):
        sat2geo = np.matrix([[iap['sat2geo_{:d}{:d}'.format(j+1, k+1)][ind]
                              for k in range(3)] for j in range(3)])
        geo2lgm = np.matrix([[iap['geo2lgm_{:d}{:d}'.format(j+1, k+1)][ind]
                              for k in range(3)] for j in range(3)])
        sat2lgm = np.matmul(geo2lgm, sat2geo)

        lgm_vel.append(np.matmul(sat2lgm, np.array(sc_vel[i], dtype=float)))
    lgm_vel = np.array(lgm_vel).reshape((len(lgm_vel), 3))

    # Save the data
    for i, name in enumerate(['iv_pos', 'iv_perp', 'iv_par']):
        iap[name] = pds.Series(lgm_vel[:, i], index=iap.data.index, name=name)
        iap.meta.data.units[name] = iap.meta.data.units[sc_keys[-1]]

    return


def add_drift_geo_coord(iap):
    """ Calcuate the ion velocity in geographic coordinates

    Parameters
    ----------
    iap : pysat.Instrument
        DEMETER IAP instrument class object

    Return
    ------
    Adds data values iv_geo_x (towards the intersection of equator and
    Grennwich meridian), iv_geo_y (completes coordinate system),
    iv_geo_z (follows Earth's rotational axis, positive Northward).
    If iv_Ox,y do not exist yet, adds them as well

    """

    sc_keys = ['iv_Ox', 'iv_Oy', 'iv_Oz']

    # Test for ion velocity in spacecraft coordinates, add if not present
    if not np.all([kk in iap.data.keys() for kk in sc_keys]):
        add_drift_sat_coord(iap)

    # Construct a numpy array of the velocity vectors
    sc_vel = iap.data[sc_keys].values

    # Construct a numpy array of the rotational matrix that convert
    # from satellite to local geomagnetic coordinates.  Then calculate the
    # velocity in local geomagnetic coordinates
    geo_vel = list()
    for i, ind in enumerate(iap.data.index):
        sat2geo = np.matrix([[iap['sat2geo_{:d}{:d}'.format(j+1, k+1)][ind]
                              for k in range(3)] for j in range(3)])

        geo_vel.append(np.matmul(sat2geo, np.array(sc_vel[i], dtype=float)))
    geo_vel = np.array(geo_vel).reshape((len(geo_vel), 3))

    # Save the data
    for i, name in enumerate(['iv_geo_x', 'iv_geo_y', 'iv_geo_z']):
        iap[name] = pds.Series(geo_vel[:, i], index=iap.data.index, name=name)
        iap.meta.data.units[name] = iap.meta.data.units[sc_keys[-1]]

    return
