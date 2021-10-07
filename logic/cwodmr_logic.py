from qtpy import QtCore
from collections import OrderedDict
from interface.microwave_interface import MicrowaveMode
from interface.microwave_interface import TriggerEdge
import numpy as np
import time
import datetime
import matplotlib.pyplot as plt

from logic.generic_logic import GenericLogic
from core.util.mutex import Mutex
from core.connector import Connector
from core.configoption import ConfigOption
from core.statusvariable import StatusVar
from threading import *

class CWODMRlogic(GenericLogic):

    # Connectors
    scope = Connector(interface='dummy_interface')
    mw_source = Connector(interface='dummy_interface')
    pulser= Connector(interface='dummy_interface')
    savelogic = Connector(interface='SaveLogic')
    taskrunner = Connector(interface='TaskRunner')
    pcw = StatusVar('pcw', -10)# CW power
    fmin = StatusVar('fmin', 2.85e9)# sweep frequency min
    fmax = StatusVar('fmax', 2.89e9)# sweep frequency max
    fstep = StatusVar('fstep', 1e6)# sweep frequency step
    stime = StatusVar('stime', 0.001)# Step time
    navg = StatusVar('navg', 40)# number of averages
    npts = StatusVar('npts', 500)# number of points

    # Update signals
    SigDataUpdated = QtCore.Signal(np.ndarray, np.ndarray)
    SigToggleAction= QtCore.Signal()

    def __init__(self, config, **kwargs):
        super().__init__(config=config, **kwargs)
        self.threadlock = Mutex()

    def on_activate(self):

        # Get connectors
        self._mw_device = self.mw_source()
        self._scope = self.scope()
        self._pulser = self.pulser()
        self._save_logic = self.savelogic()
        self._taskrunner = self.taskrunner()

        """ Needs to be implemented
        # Get hardware constraints
        limits = self.get_hw_constraints()
        """

        self.data_freq = np.array([])
        self.data_spectrum = np.array([])

    def on_deactivate(self):
        """
        Deinitialisation performed during deactivation of the module.
        """
        # Disconnect signals
        #self.sigDataUpdated.disconnect()
    def start_data_acquisition(self):
        startThread = Thread(target=self.start_data_acquisition_thread)
        startThread.start()

    def start_data_acquisition_thread(self):
     #   for i in range(30):
        with self.threadlock:
            self._mw_device.set_sweep_param(self.fmin, self.fmax, self.fstep)

            self._mw_device.set_sweep_time(self.stime)

            self._mw_device.set_trigger_mode(1)

            self._mw_device.on()

            self.npts_frequency=np.ceil((-self.fmin+self.fmax)/self.fstep)
            IntegrationTime = self.npts_frequency * self.stime;

            ChannelTrigNumber = 2  # ACQ_chan trigger
            self._scope.set_trigger_source(ChannelTrigNumber)

            self._scope.set_delay(IntegrationTime/2)
            self._scope.set_timebase_range(IntegrationTime)
            #self._scope.set_Center_Tscale(1, IntegrationTime / 1.25)  # 1.25*10
            self._scope.set_acquisition_type(1) #AVG type ACQ
            self._scope.set_trigger_sweep(1)  # set normal mode for ACQ of Oscope

            self._scope.set_trigger_level(1)

            ChannelNumber = 1;

            self._pulser.set_ODMR(self.stime, self.npts_frequency)
            self._pulser.start_stream()
            print('meaow')
            self._scope.set_acquisition_count(2)  # set the number of avg for oscope

            self._scope.set_ODMR_scale(1)

            self._scope.set_acquisition_count(self.navg)  # set the number of avg for oscope

            self._scope.set_wavepoint(self.npts)


            DATA = self._scope.get_data([ChannelNumber])          # get the data from oscope

            self._mw_device.off()

            if self.stop_acq == False:
                ODMR_Signal=np.array(DATA[ChannelNumber])
                self.SigDataUpdated.emit(np.linspace(self.fmin,self.fmax,np.size(np.array(DATA[0]))),ODMR_Signal/max(ODMR_Signal))

            self.SigToggleAction.emit()
    def stop_data_acquisition(self,state):
        #Fix me mutex threadlock might be required to add
        # if self.module_state() == 'locked':
        #     self.module_state.unlock()
        #     return -1
        self.stop_acq = True
    def set_pcw(self, pcw):
        self._mw_device.set_pcw(pcw)
        self.pcw = pcw
    def set_ODMR(self, stime):
        self.stime = stime
    def set_scope_param(self,navg,npts):
        self.navg = navg
        self.npts = npts


    def set_sweep_param(self, fmin,fmax,fstep):
        self.fmin = fmin
        self.fmax = fmax
        self.fstep = fstep