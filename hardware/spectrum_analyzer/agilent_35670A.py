import pyvisa
from interface.fft_interface import FFTInterface

import os
import time
import numpy as np
import scipy.interpolate
from fnmatch import fnmatch
from collections import OrderedDict
from abc import abstractmethod
import re

from core.module import Base
from core.configoption import ConfigOption
from interface.pulser_interface import PulserInterface, PulserConstraints, SequenceOption
from core.util.modules import get_home_dir

class Agilent_35670A(Base, FFTInterface):
    """
    H. Babashah - Hardware code for fft analyzer Keysight 35670A.
    """

    _instrument_name = ConfigOption(name='instrument_name', default='fft01', missing='warn')
    _gate_name = ConfigOption(name='gate_name', default='gate01', missing='warn')

    if _instrument_name.default == 'fft01':
        _instr_address = 'gpib0,1'
    _visa_address = 'TCPIP0::'+_gate_name.default+'::'+_instr_address+'::INSTR'

    def __init__(self, config, **kwargs):
        super().__init__(config=config, **kwargs)

        self._BRAND = ''
        self._MODEL = ''
        self._SERIALNUMBER = ''
        self._FIRMWARE_VERSION = ''

        self._sequence_mode = False         # set in on_activate()
        self._debug_check_all_commands = False       # # For development purpose, might slow down


    def on_activate(self):
        """
        H. Babashah - Inspired from Qudi - Initialisation performed during activation of the module.
        """
        self._rm = pyvisa.ResourceManager()

        # connect to awg using PyVISA
        try:
            self.fft = self._rm.open_resource(self._visa_address)

        except:
            self.fft = None
            self.log.error('VISA address "{0}" not found by the pyVISA resource manager.\nCheck '
                           'the connection or that instrument is on.'
                           ''.format(self._visa_address))
            return

        if self.fft is not None:
            idn = self.fft.query('*IDN?').split(',')
            self._brand, self._model, self._ser, self._fw_ver = idn

            self.log.info('Load the device model "{0}" from "{1}" with '
                          'serial number "{2}" and firmware version "{3}" '
                          'successfully.'.format(self._brand, self._model,
                                                 self._ser,
                                                 self._fw_ver))

            self.fft.read_termination = '\n'
            self.fft.timeout = 600000 #Sets a huge timeout to avoid I/O pyvisa errors when asking for long acquisition.


    def on_deactivate(self):
        """
        H. Babashah - Inspired from Qudi - Required tasks to be performed during deactivation of the module.
        """

        try:
            self.fft.close()
            self.connected = False
        except:
            self.log.warning('Closing AWG connection using pyvisa failed.')
        self.log.info('Closed connection to AWG')


    def set_span(self, span):
        """
        H. Babashah - Sets frequency span on screen.
        """
        self.fft.write('FREQuency:SPAN '+str(span))
        self._span = span


    def set_resolution(self, resolution_lines):
        """
        H. Babashah - Sets the resolution in lines.
        """
        self.fft.write('FREQuency:RESolution ' + str(np.int(resolution_lines)))
        self._lines = np.int(resolution_lines)


    def set_window(self, window):
        """
        H. Babashah - Sets the fft window type.
        """
        self.fft.write('WINDow:TYPE '+window)
        self._window = window

    def set_unit(self, unit):
        """
        H. Babashah - Sets voltage unit of spectrum
        !!! To be finished
        """
        pass

    def get_rbw(self):
        """
        H. Babashah - Gets the Resolution Bandwidth.
        """
        self._window = self.fft.query('WINDow:TYPE?')
        self._span = float(self.fft.query('SENS:FREQuency:SPAN?'))
        window_factor = {
            'UNIF' : 0.125/100,
            'HANN' : 0.185/100,
            'FLAT' : 0.450/100
        }
        resolution_factor = {
            100 : 8,
            200 : 4,
            400 : 2,
            800 : 1,
            1600 : 0.5
        }
        rbw = window_factor.get(self._window)*resolution_factor.get(self._lines)*self._span

        return rbw


    def get_acquisition(self):
        """
        H. Babashah - Data acquisition.
        """
        self._lines = int(float(self.fft.query('FREQuency:RESolution?')))
        self.fft.write('INIT:IMM') #Starts a new acquisition on screen (equivalent start button)
        self.fft.query('*OPC?') #Waits for the end of acquisition
        fft = np.array([float(i) for i in self.fft.query('CALC:DATA?').split(',')])
        freq = np.array([float(i) for i in self.fft.query('CALC:X:DATA?').split(',')][:self._lines + 1])

        return freq, fft





