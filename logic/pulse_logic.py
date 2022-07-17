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

class PULSElogic(GenericLogic):

    # Connectors
    scope = Connector(interface='dummy_interface')
    mw_source = Connector(interface='dummy_interface')
    pulser= Connector(interface='dummy_interface')
    savelogic = Connector(interface='SaveLogic')
    taskrunner = Connector(interface='TaskRunner')
    time_start = StatusVar('time_start', 0)# start time
    rabi_period = StatusVar('rabi_period', 100e-9)# start time
    pcw = StatusVar('pcw', -10)# CW power
    navg = StatusVar('navg', 40)# number of averages
    threshold = StatusVar('threshold', 2.85e9)# threshold for pulse analysis
    time_reference = StatusVar('time_reference', 1e-3)#  window time for reference
    time_signal = StatusVar('time_signal', 1e-3)# window time for signal
    time_reference_start = StatusVar('time_reference_start', 0.1e-6)# neglet time for signal
    time_signal_start = StatusVar('time_signal_start', 0.1e-6)# neglet time for reference
    npts = StatusVar('npts', 40)# number of points
    time_stop = StatusVar('time_stop', 0.001)# stop time
    pulse_type = StatusVar('pulse_type', 'T1')# stop time
    fcw = StatusVar('fcw', 2.87e9)# CW frequency



    # Update signals
    SigDataUpdated = QtCore.Signal(np.ndarray, np.ndarray)
    SigDataPulseUpdated = QtCore.Signal(np.ndarray, np.ndarray)
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
        with self.threadlock:

            flag_calib=True
            if self.pulse_type!='T1':
                self._mw_device.set_trigger_mode(0)
                self._mw_device.set_fcw(self.fcw)
                self._mw_device.set_pcw(self.pcw)
                self._mw_device.on()
                print('MW is on')

            Pulse_Length=100e-6
            ChannelTrigNumber = 2  # ACQ_chan trigger

            ChannelNumber = 1;
            # Set scope horizontal axis
            self._scope.set_trigger_source(ChannelTrigNumber)
            self._scope.set_Center_Tscale(1, Pulse_Length)  # 1.25*10
            self._scope.set_acquisition_type(1)  # AVG type ACQ
            self._scope.set_acquisition_count(self.navg)  # set the number of avg for oscope
            self._scope.set_trigger_sweep(1)  # set normal mode for ACQ of Oscope
            self._scope.set_trigger_level(1)
            # set the pulse measurement sweep type
            var_sweep_type='linear'
            if var_sweep_type == 'log':
                var_range = np.logspace(np.log10(self.time_start), np.log10(self.time_stop), self.npts, base=10)
            else:
                var_range = np.linspace(self.time_start, self.time_stop, int(self.npts))
            VARResult = []
            i=0
            for variable in var_range:
                if self.stop_acq == True:
                    break
                self._pulser.set_pulse_measurement(variable, self.pulse_type, self.rabi_period)
                self._pulser.start_stream()


                if flag_calib==True:
                    self._scope.set_Pulse_scale(1)
                    flag_calib = False

                DATA = self._scope.get_data([ChannelNumber])

                PulseAmp, PulseTime = DATA[ChannelNumber], DATA[0]
                ############################################################
                # Analysis of the aquired pulses
                ############################################################
                # set min as zero
                minPulseAmp = min(PulseAmp)

                if minPulseAmp > 0:
                    PulseAmp = [(ka - abs(minPulseAmp)) for ka in PulseAmp]
                else:
                    PulseAmp = [(ka + abs(minPulseAmp)) for ka in PulseAmp]
                # Normalize to max avg
                maxindPulseAmp = np.argmax(PulseAmp)
                maxPulseAmpAvg = abs(np.mean(PulseAmp[int(maxindPulseAmp):int(maxindPulseAmp + 100)]))
                PulseAmp = [kar / abs(maxPulseAmpAvg) for kar in PulseAmp]
                # Get timing resolution
                TimeRes = PulseTime[4] - PulseTime[3]
                IntTimeSampleSignal = int(np.floor(self.time_signal / TimeRes))
                IntTimeSampleReference = int(np.floor(self.time_reference / TimeRes))
                IntTimeSampleSignalStart = int(np.floor(self.time_signal_start / TimeRes))
                IntTimeSampleReferenceStart = int(np.floor(self.time_reference_start / TimeRes))
                # Threhold the pulses
                ind_L_pulseAmp = self.ThresholdL(PulseAmp,  self.threshold)+IntTimeSampleSignalStart
                ind_R_pulseAmp = self.ThresholdR(PulseAmp,  self.threshold)-IntTimeSampleReferenceStart
                Ssample=PulseAmp[ind_L_pulseAmp:ind_L_pulseAmp + IntTimeSampleSignal]
                Rsamples=PulseAmp[ind_R_pulseAmp - IntTimeSampleReference:ind_R_pulseAmp]
                # Find reference and signal
                Signal = np.trapz(Ssample, dx=5) /(np.size(Ssample)-1) # Signal Window
                Reference = np.trapz(Rsamples, dx=5)/(np.size(Rsamples)-1)  # Reference Window
                # Calculated the final output
                VARResult.append(Signal / Reference)
                i = i + 1
                # emit and updat the plots
                self.SigDataPulseUpdated.emit(np.array(PulseTime), np.array(PulseAmp))
                self.SigDataUpdated.emit(var_range[0:i], np.array(VARResult))

            self.SigToggleAction.emit()
        if self.pulse_type!='T1':
            # make sure microwave signal generator is off
            self._mw_device.off()
            self.log.info('MW is OFF')

    def stop_data_acquisition(self,state):
        # Fixme mutex threadlock might be required to add
        # if self.module_state() == 'locked':
        #     self.module_state.unlock()
        #     return -1
        self.stop_acq = True

    def set_pulse(self, time_start,time_stop,npts,rabi_period):
        """ Set pulse measurement sweep parameters

        @param float time_start: start duration time of the sweep parameter in s
        @param float time_stop: stop duration time of the sweep parameter in s
        @param int npts: number of points
        @param float rabi_period:  rabi period in s
        """
        self.time_start = time_start
        self.time_stop = time_stop
        self.npts = npts
        self.rabi_period=rabi_period

    def set_pulse_type(self, pulse_type):
        """ Set pulse measurement type
        @param string pulse_type: T1, rabi, Hahnecho, PL
        """
        self.pulse_type=pulse_type

    def set_pcw(self, pcw):
        """ Set microwave power for measurement
        @param float pcw: microwave power
        """
        self.pcw = pcw


    def set_navg(self, navg):
        """ Set number of averages for acquisistion
        @param int navg: number of averages
        """
        self.navg = navg

    def set_pulse_analys_param(self, threshold,time_reference,time_signal,time_reference_start,time_signal_start):
        """ Set pulse analysis parameters
        @param float threshold:
        @param float time_reference:
        @param float time_signal:
        @param float time_reference_start:
        @param float time_signal_start:
        """
        self.threshold = threshold
        self.time_reference = time_reference
        self.time_signal = time_signal
        self.time_reference_start = time_reference_start
        self.time_signal_start = time_signal_start

    def change_navg(self, threshold,time_reference,time_signal):
        """ Sets pulses analysis parameters as measurement continues in real time

        @param float threshold:
        @param float time_reference:
        @param float time_signal:
        @return:
        """
        self.threshold = threshold
        self.time_reference = time_reference
        self.time_signal = time_signal


    def set_fcw(self, fcw):
        """ Set microwave CW frequency
        @param float fcw: microwave cw frequency
        """
        self.fcw = fcw



    def ThresholdL(self,data,t_v):
        """Threshold pulses in an array from left side with t_v
        @param array data: array to be thresholded from left
        @param float t_v:
        """
        t_ind = 0
        for kop in range(len(data)) :
            if data[kop] >= t_v :
                t_ind = kop
                break
        if t_ind==0:
            self.log.info('Probably could not find the begining of the pulse, zero set as begining')
        return t_ind

    def ThresholdR(self,data,t_v):
        """Threshold pulses in an array from right side with t_v
        @param array data: array to be thresholded from right
        @param float t_v: Threshold value
        """
        t_ind = -1
        for kop in range(len(data)) :
            if data[-kop-1] >= t_v :
                t_ind = -kop-1
                break
        if t_ind==-1:
            self.log.info('Probably could not find the begining of the pulse, zero set as begining')
        return t_ind
