import pyvisa
from interface.lock_in_interface import LockinInterface
from interface.hard_interface import HardInterface
import os
import time
import numpy as np
import scipy.interpolate
from fnmatch import fnmatch
from collections import OrderedDict
from abc import abstractmethod


from core.module import Base
from core.configoption import ConfigOption
from interface.pulser_interface import PulserInterface, PulserConstraints, SequenceOption
from core.util.modules import get_home_dir

class SRS_lockin(Base, LockinInterface, HardInterface):
    """
    H. Babashah - Hardware code for fft analyzer Keysight 35670A.
    """

    _instrument_name = ConfigOption(name='instrument_name', default='srs01', missing='warn')
    _gate_name = ConfigOption(name='gate_name', default='gate01', missing='warn')

    def __init__(self, config, **kwargs):
        super().__init__(config=config, **kwargs)

        if self._instrument_name == 'srs01':
            self._instr_address = 'gpib0,2'
        elif self._instrument_name == 'srs02':
            self._instr_address = 'gpib0,3'

        self._visa_address = 'TCPIP0::' + self._gate_name + '::' + self._instr_address + '::INSTR'

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

        # connect to instrument using PyVISA
        try:
            self.cmd = self._rm.open_resource(self._visa_address)

        except:
            self.cmd = None
            self.log.error('VISA address "{0}" not found by the pyVISA resource manager.\nCheck '
                           'the connection or that instrument is on.'
                           ''.format(self._visa_address))
            return

        if self.cmd is not None:
            idn = self.cmd.query('*IDN?').split(',')
            self._brand, self._model, self._ser, self._fw_ver = idn

            self.log.info('Load the device model "{0}" from "{1}" with '
                          'serial number "{2}" and firmware version "{3}" '
                          'successfully.'.format(self._brand, self._model,
                                                 self._ser,
                                                 self._fw_ver))

            self.cmd.read_termination = '\n'

    def on_deactivate(self):
        """
        deactive the module
        """
        self.cmd.close()

    def get_hard_type(self):
        """ H. Babashah - Only function of HardInterface - Get the type of hardware. """
        ramp_parameters = ['amplitude', 'frequency']
        hard_type = ('LockIn', self._instrument_name, ramp_parameters)
        return hard_type

    def set_ramp_parameter(self, text, value):
        """
        set ramp sweep parameters
        @param string: ramp type selection frequency/amplitude
        @param value: frequency/amlitude of the ramp
        """
        if text == 'amplitude':
            self.set_amplitude(value)
        elif text == 'frequency':
            self.set_frequency(value)

    def get_offset_expand(self):
        """
        H. Babashah - Gets the offset and expand gain of the srs lock-in
        """

        str_offset, str_i_expand = self.cmd.query('OEXP? 1').split(',')
        offset = float(str_offset)
        i_expand = float(str_i_expand)

        expand = {
            0 : 1,
            1 : 10,
            2 : 100
        }

        return offset, expand.get(i_expand)


    def get_gain(self):
        """
        H. Babashah - Gets the global gain output/input of the srs lock-in
        """

        sensitivity = self.get_sensitivity()
        offset, expand = self.get_offset_expand()

        if offset == 0 :
            return (10*expand)/sensitivity
        else :
            self.log.warning('non nul offset on '+self.name+'. Function not implemented.')



    def set_amplitude(self, value):
        """
        Set the input amplitude sensitivity
        @param float value: input sensitivity voltage
        """
        self.cmd.write('SLVL '+str(value))

    def set_frequency(self, value):
        """
        Set frequency modulation value
        @param float value: modulation frequency in Hz
        """
        self.cmd.write('FREQ '+str(value))
		
		

    def get_sensitivity(self):
        """
        H. Babashah - Gets the input sensitivity of the srs lock-in
        """

        i = int(self.cmd.query('SENS?'))

        sensitivity={
            0 : 2*10**-9,
            1 : 5*10**-9,
            2 : 10*10**-9,
            3 : 20*10**-9,
            4 : 50*10**-9,
            5 : 100*10**-9,
            6 : 200*10**-9,
            7 : 500*10**-9,
            8 : 1*10**-6,
            9 : 2*1**-6,
            10 : 5*1**-6,
            11 : 10*1**-6,
            12 : 20*1**-6,
            13 : 50*1**-6,
            14 : 100*10**-6,
            15 : 200*1**-6,
            16 : 500*1**-6,
            17 : 1*10**-3,
            18 : 2*10**-3,
            19 : 5*10**-3,
            20 : 10*10**-3,
            21 : 20*10**-3,
            22 : 50*10**-3,
            23 : 100*10**-3,
            24 : 200*10**-3,
            25 : 500*10**-3,
            26 : 1
        }

        return sensitivity.get(i, 'Invalid')
		