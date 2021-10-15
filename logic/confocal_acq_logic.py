from qtpy import QtCore
from collections import OrderedDict
from interface.microwave_interface import MicrowaveMode
from interface.microwave_interface import TriggerEdge
import numpy as np
import time
import datetime
import matplotlib.pyplot as plt
from operator import not_
from logic.generic_logic import GenericLogic
from core.util.mutex import Mutex
from core.connector import Connector
from core.configoption import ConfigOption
from core.statusvariable import StatusVar
from threading import *

class Confocallogic(GenericLogic):

    # Connectors
    scope = Connector(interface='dummy_interface')
    mw_source = Connector(interface='dummy_interface')
    pulser= Connector(interface='dummy_interface')
    savelogic = Connector(interface='SaveLogic')
    taskrunner = Connector(interface='TaskRunner')
    fcw = StatusVar('fcw', 2.87e9)# CW frequency
    pcw = StatusVar('pcw', -10)# CW power
    fstep = StatusVar('fstep', 1e6)# sweep frequency step
    npts = StatusVar('npts', 40)# number of points
    stime = StatusVar('stime', 0.001)# Step time
    xmin = StatusVar('xmin', 0)# sweep x min
    xmax = StatusVar('xmax', 1e-6)# sweep x max
    xnpts = StatusVar('xnpts', 10)# sweep x points
    ymin = StatusVar('ymin', 0)# sweep y min
    ymax = StatusVar('ymax', 1e-6)# sweep y max
    ynpts = StatusVar('ynpts', 10)# sweep y points


    # Update signals
    SigDataUpdated = QtCore.Signal(np.ndarray, np.ndarray)
    SigConfocalDataUpdated= QtCore.Signal(np.ndarray)
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

    def start_data_acquisition(self):
        startThread = Thread(target=self.start_data_acquisition_thread)
        startThread.start()

    def start_data_acquisition_thread(self):
        with self.threadlock:
            # if self.module_state() == 'locked':
            #     self.log.error('Can not start Confocal scan. Logic is already locked.')
            #     return -1
            # self.module_state.lock()
            V_XvalueRange = np.linspace(self.xmin, self.xmax, int(self.xnpts))
            V_YvalueRange = np.linspace(self.ymin, self.ymax, int(self.ynpts))

            self._scope.set_Center_Tscale(1, self.int_time / 1.25)  # 1.25*10
            self._scope.set_trigger_sweep(0)  # set normal mode for ACQ of Oscope
            self._scope.set_trigger_level(1)
            self.ChannelNumber = 1  # ACQ Chan Number
            ChannelTrigNumber = 2  # ACQ_chan trigger
            self._scope.set_trigger_source(ChannelTrigNumber)
            self._pulser.set_confocal(0, 0)  # intialize the confocal
            self._pulser.start_stream()  # start stream
            self._scope.set_timeout()
            self._scope.set_init_scale(1)
            self._scope.set_scope_range(1, 3)
            self._scope.set_Voffset(1, 1.5, 1)
            i = -1;
            Image_xy = np.zeros((int(np.size(V_XvalueRange)), int(np.size(V_YvalueRange))))
            # AutoVscale=True
            flag = True
            for V_Xvalue in V_XvalueRange:
                i = i + 1
                j = 0
                if self.stop_acq == True:
                    break
                for V_Yvalue in V_YvalueRange:
                    if flag == False:
                        j = j - 1
                    self._pulser.set_confocal(V_Xvalue, V_Yvalue)

                    self._pulser.start_stream()
                    DATA = self._scope.get_data([self.ChannelNumber])  #
                    Image_xy[i, j] = np.mean(DATA[self.ChannelNumber])
                    self.SigConfocalDataUpdated.emit(Image_xy)  # np.random.rand(5, 5)
                    self.SigDataUpdated.emit(np.array(DATA[0]), np.array(DATA[self.ChannelNumber]))
                    if flag == True:
                        j = j + 1
                    if self.stop_acq == True:
                        break

                V_YvalueRange = np.flip(V_YvalueRange)
                flag = not_(flag)
            self.SigToggleAction.emit()
            # if self.module_state() == 'locked':
            #     self.module_state.unlock()
            #     return -1

    def set_cordinate_sparam(self,xmin,xmax,xnpts,ymin,ymax,ynpts):
        self.xmin = xmin
        self.xmax = xmax
        self.xnpts = xnpts
        self.ymin = ymin
        self.ymax = ymax
        self.ynpts = ynpts

    def set_move_to_position(self, xpos, ypos):
        self.xpos = xpos
        self.ypos = ypos


    def set_fcw(self, fcw):
        self._mw_device.set_fcw(fcw)
        self.fcw = fcw


    def stop_data_acquisition(self,state):
        #Fix me mutex threadlock might be required to add
        # if self.module_state() == 'locked':
        #     self.module_state.unlock()
        #     return -1
        self.stop_acq = True


    def set_pcw(self, pcw):
        self._mw_device.set_pcw(pcw)
        self.pcw = pcw
    def set_ODMR(self, stime,npts):
        self._pulser.set_ODMR(stime,npts)
      #  self._mw_device.set_ODMR(stime,npts)
        self.stime = stime
        self.npts = npts
