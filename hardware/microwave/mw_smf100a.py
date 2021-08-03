# -*- coding: utf-8 -*-

"""
This file contains the Qudi hardware file to control SRS SG devices.

Qudi is free software: you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation, either version 3 of the License, or
(at your option) any later version.

Qudi is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.

You should have received a copy of the GNU General Public License
along with Qudi. If not, see <http://www.gnu.org/licenses/>.

Copyright (c) the Qudi Developers. See the COPYRIGHT.txt file at the
top-level directory of this distribution and at <https://github.com/Ulm-IQO/qudi/>
"""


import pyvisa
import visa
import time

from core.module import Base
from core.configoption import ConfigOption
from interface.dummy_interface import dummy_interface


class MicrowaveSMF100a(Base, dummy_interface):
    """
    H.Babashah

    """

    _instrument_ip = ConfigOption(name='instrument_ip', default='TCPIP::169.254.154.2::INSTR', missing='warn')


    def on_activate(self):
        """ Initialisation performed during activation of the module. """


        # trying to load the visa connection to the module
        #self._gpib_address = 'TCIP0::'+self._instrument_name+'.lab.wainvam-e.com::INSTR'
        # Standard LAN connection (also called VXI-11)
        self.rm = visa.ResourceManager()
        self.connection = self.rm.open_resource(self._instrument_ip)
        self.connection.read_termination = '\n'
        self.connection.write_termination = '\n'
        self.connection.clear()  # Clear instrument io buffers and status

        self.max_power = -10  # maximum allowed ouput power, in dBm

    def on_deactivate(self):
        """ Deinitialisation performed during deactivation of the module."""

        self.set_status('OFF')
        return


    def reset(self):
        self.connection.write('*RST')
        print("reset done")

    #########################################################
    #
    #                General functions
    #
    #########################################################
    def write(self, command):
        self.connection.write(command)

    def set_param(self, param_name, param_value):
        self.connection.write(param_name + ' %s' % param_value)

    def query(self, param_name):
        return self.connection.query(param_name + '?')

    #########################################################
    #
    #                Frequency
    #
    #########################################################
    def set_fcw(self, frequency):
        """ Set output frequency, in Hz """
        print('frequency %s' % frequency)
        self.connection.write('frequency %s' % frequency)

    def get_frequency(self):
        return self.connection.query('frequency?')

    #########################################################
    #
    #                Power
    #
    #########################################################
    def set_pcw(self, power):
        """ Set output power, in dBm """
        power_actual = min(power, self.max_power)
        if power_actual < power:
            print('Warning: For safety reason, requested power too high.\n' +
                  'Setting power to %.0d dBm instead (max. value)' % power_actual)
        self.connection.write('power ' + str(power_actual))

    def get_power(self):
        return self.connection.query('power?')

    #########################################################
    #
    #                Status
    #
    #########################################################
    def set_status(self, stat):
        """ Set RF output ON or OFF """
        self.write('output %s' % stat)

        # if (stat == 'OFF') or (stat == 0):
        #     print('SMF100A output is now OFF')
        # elif (stat == 'ON') or (stat == 1):
        #     print('SMF100A output is now ON')

    def get_status(self):
        return self.query('output')

    #########################################################
    #
    #                IDN
    #
    #########################################################
    def get_identification(self):
        return self.query('*IDN')

    #########################################################
    #
    #                RF Frequeny sweep
    #
    #########################################################

    def set_sweep_param(self, freq_i, freq_f, dfreq):
        """ Set parameters of a frequency sweep
        - freq_i, freq_f : start and end frequency (included in scan), in Hz
        - dfreq : frequency step, in Hz
        """
        # Go to start frequency (must be placed before switching to sweep mode)
        self.set_fcw(freq_i)

        # Fixed parameters for a scan
        self.write(':FREQ:MODE SWEEP')
        self.write(':TRIG:FSW:SOUR EXT')
        self.write(':SWE:SPAC LIN')

        # User defined parameters
        self.write(':FREQ:START %s' % freq_i)
        self.write(':FREQ:STOP %s' % freq_f)
        self.write(':SWE:STEP %s' % dfreq)

    def start_freq_sweep(self):
        self.write(':FREQ:MODE SWEEP')  # Make sure frequency sweep mode is ON
        self.set_status(1)  # Set RF output ON

    def stop_freq_sweep(self):
        self.set_status(0)  # Set RF output OFF
        freq_i = self.query(':FREQ:START')
        self.write(':FREQ:MODE CW')  # Go back to cw mode (probably redundant with following command)
        self.set_fcw(freq_i)  # Go back to start frequency

    #########################################################
    #
    #                FM Modulation
    #
    #########################################################
    def set_fm_modulation(self, deviation, shape, frequency):
        """ Set parameters of frequency modulation
        and set Modulation and LO outputs ON
        - deviation : amplitude of the modulation, in Hz
        - shape : can be 'SIN', 'SQU', 'TRI' or 'TRAP'
        - frequency : frequency of the modulation (and LO output), in Hz"""
        # Fixed parameters for a scan
        self.write('FM1:SOUR LF1')  # LF1 | LF2 | NOISe | EXT1 | EXT2 | INTernal | EXTernal

        # User defined parameters
        self.write('FM1:DEV %s' % deviation)
        self.write('LFO1:SHAP %s' % shape)  # SINE | SQUare | TRIangle | TRAPeze
        self.write('LFO1:FREQ %s' % frequency)

        # Set outputs ON
        self.write('FM1:STAT 1')  # Set modulation output ON
        self.write('SOUR:LFO1 1')  # Set LO output ON (for lock-in REF IN)

    def stop_fm_modulation(self):
        self.write('FM1:STAT 0')  # Set modulation output OFF
        self.write('SOUR:LFO1 0')  # Set LO output OFF

