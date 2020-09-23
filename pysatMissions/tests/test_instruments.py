# -*- coding: utf-8 -*-
"""
Basic test of the instrument objects in pysatMissions

To be replaced once pysat testing techniques are finalized
"""

import datetime as dt
import numpy as np
import os

import pysat


class TestSGP4():
    def setup(self):
        """Runs before every method to create a clean testing setup."""
        from pysatMissions.instruments import pysat_sgp4
        self.testInst = pysat.Instrument(inst_module=pysat_sgp4, sat_id='100')
        self.targets1 = ['position_eci_x', 'position_eci_y', 'position_eci_z',
                         'velocity_eci_x', 'velocity_eci_y', 'velocity_eci_z']
        self.targets2 = []

    def teardown(self):
        """Clean up test environment after tests"""
        del self

    def test_basic_instrument_load(self):
        """Checks if instrument loads proper data and metadata"""
        # Check if instrument is instrument
        assert isinstance(self.testInst, pysat._instrument.Instrument)

        self.testInst.load(date=dt.datetime(2018, 1, 1))
        # Check for completeness of first set of targets
        for target in self.targets1:
            # Check if data is added
            assert target in self.testInst.data.keys()
            assert not np.isnan(self.testInst[target]).any()
            # Check if metadata is added
            assert target in self.testInst.meta.data.index
        # Check for completeness of second set of targets
        for target in self.targets2:
            # Check if data is added
            assert target in self.testInst.data.keys()
            # First and last values are NaN if related to velocity
            assert not np.isnan(self.testInst[target][1:-1]).any()
            assert np.isnan(self.testInst[target][0])
            assert np.isnan(self.testInst[target][-1])
            # Check if metadata is added
            assert target in self.testInst.meta.data.index


class TestEphem(TestSGP4):
    def setup(self):
        """Runs before every method to create a clean testing setup."""
        # NOTE: aacgm not checked here because undefined near the equator
        # TODO: add check for aacgm values
        from pysatMissions.instruments import pysat_ephem
        self.testInst = pysat.Instrument(inst_module=pysat_ephem, tag='all',
                                         sat_id='100')
        self.targets1 = ['glong', 'glat', 'alt', 'obs_sat_slant_range',
                         'obs_sat_az_angle', 'obs_sat_el_angle',
                         'position_ecef_x', 'position_ecef_y', 'position_ecef_z',
                         'qd_lat', 'qd_long', 'mlt']
        pyglow_targets = ['e_temp', 'frac_dens_h', 'frac_dens_he', 'frac_dens_o',
                          'ion_dens', 'ion_temp',
                          'B', 'B_east', 'B_north', 'B_up', 'B_ecef_x',
                          'B_ecef_y', 'B_ecef_z',
                          'Nn', 'Nn_H', 'Nn_He', 'Nn_N', 'Nn_N2', 'Nn_O', 'Nn_O2',
                          'Nn_Ar', 'Tn_msis',
                          'total_wind_x', 'total_wind_y', 'total_wind_z']
        if (os.environ.get('TRAVIS') == 'false'):
            for target in pyglow_targets:
                self.targets.append(target)
        self.targets2 = ['velocity_ecef_x', 'velocity_ecef_y', 'velocity_ecef_z',
                         'sc_xhat_ecef_x', 'sc_xhat_ecef_y', 'sc_xhat_ecef_z',
                         'sc_yhat_ecef_x', 'sc_yhat_ecef_y', 'sc_yhat_ecef_z',
                         'sc_zhat_ecef_x', 'sc_zhat_ecef_y', 'sc_zhat_ecef_z',
                         'sim_wind_sc_x', 'sim_wind_sc_y', 'sim_wind_sc_z']

    def teardown(self):
        """Clean up test environment after tests"""
        del self
