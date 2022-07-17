from qtpy import QtCore
from collections import OrderedDict
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
from scipy.optimize import curve_fit


class Confocallogiccomplex(GenericLogic):
    """
    H.babashah - confocal logic class for aquiring a confocal scan for pulsed and cw measurements
	
    """
    # Connectors
    nicard = Connector(interface='dummy_interface')
    mw_source = Connector(interface='dummy_interface')
    pulser= Connector(interface='dummy_interface')
    piezo= Connector(interface='dummy_interface')
    savelogic = Connector(interface='SaveLogic')
    taskrunner = Connector(interface='TaskRunner')
    fcw = StatusVar('fcw', 2.87e9)# CW frequency
    pcw = StatusVar('pcw', -10)# CW power
    fmin = StatusVar('fmin', 2.85e9)# sweep frequency min
    fmax = StatusVar('fmax', 2.89e9)# sweep frequency max
    fstep = StatusVar('fstep', 1e6)# sweep frequency step
    stime = StatusVar('stime', 0.001)# Step time
    xmin = StatusVar('xmin', 0)# sweep x min
    xmax = StatusVar('xmax', 1e-6)# sweep x max
    xnpts = StatusVar('xnpts', 10)# sweep x points
    ymin = StatusVar('ymin', 0)# sweep y min
    ymax = StatusVar('ymax', 1e-6)# sweep y max
    ynpts = StatusVar('ynpts', 10)# sweep y points
    xpos = StatusVar('xpos', 0)# x position
    ypos = StatusVar('ypos', 0)# y position
    zpos = StatusVar('zpos', 0)# z position
    mes_type = StatusVar('mes_type', 'PL')# stop time
    int_time = StatusVar('int_time', 20e-9)# integration time




    time_start = StatusVar('time_start', 0)# start time
    rabi_period = StatusVar('rabi_period', 100e-9)# start time
    navg = StatusVar('navg', 2)# number of averages
    threshold = StatusVar('threshold', 0.5)# sweep frequency min
    time_reference = StatusVar('time_reference', 1e-3)#  window time for reference
    time_signal = StatusVar('time_signal', 1e-3)# window time for signal
    time_reference_start = StatusVar('time_reference_start', 0.1e-6)# neglet time for signal
    time_signal_start = StatusVar('time_signal_start', 0.1e-6)# neglet time for reference
    npts = StatusVar('npts', 40)# number of points
    time_stop = StatusVar('time_stop', 0.001)# stop time




    # Update signals
    SigDataUpdated = QtCore.Signal(np.ndarray, np.ndarray)
    SigConfocalDataUpdated= QtCore.Signal(np.ndarray)
    SigConfocalArbDataUpdated= QtCore.Signal(np.ndarray)
    SigToggleAction= QtCore.Signal()
    def __init__(self, config, **kwargs):
        super().__init__(config=config, **kwargs)
        self.threadlock = Mutex()

    def on_activate(self):
        """
        H.babashah - connection to the hadware and other logics
        """
        # Get connectors
        self._mw_device = self.mw_source()
        self._nicard = self.nicard()
        self._pulser = self.pulser()
        self._piezo = self.piezo()
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
        self._piezo.mcl_close()

    def start_data_acquisition(self):
        """
		H.Babashah - create the thread for data acqusuitb. 
		"""
        startThread = Thread(target=self.start_data_acquisition_thread)
        startThread.start()

    def start_data_acquisition_thread(self):
        """
		H.Babashah - The task that are required to be processed in a thread 
		"""
        with self.threadlock:
            # FIXME: if self.module_state() == 'locked':
            #     self.log.error('Can not start Confocal scan. Logic is already locked.')
            #     return -1
            #  self.module_state.lock()
            # Set sweep voltage range for xy scan
            V_XvalueRange = np.linspace(self.xmin, self.xmax, int(self.xnpts))
            V_YvalueRange = np.linspace(self.ymin, self.ymax, int(self.ynpts))
            # Fitting exp
            def exponenial_func(x, a, b, c):
                return a * (np.exp(-b * x))
            self.ChannelNumber = 1  # ACQ Chan Number
            # Initialize xy map
            Image_xy = np.zeros((int(np.size(V_XvalueRange)), int(np.size(V_YvalueRange))))
            Image_xy_arb = np.zeros((int(np.size(V_XvalueRange)), int(np.size(V_YvalueRange))))
            # Set meanderline scan flag
            flag_meander = True
            # Set acq card integration time
            self._nicard.set_timing(self.int_time)
            # Set MW CW frequency
            self._mw_device.set_fcw(self.fcw)
            self.Laser_length = 100e-6
            self.Laser_length_s = int(np.ceil(self.Laser_length * self._nicard.get_timing()))
            # Set sweep type
            # Fixme sweep time should be selected in the gui
            var_sweep_type = 'linear'
            # Avoid zero input to pulse generator
            if self.time_start==0:
                self.time_start=10e-9
            # Fixme put it in the gui
            # Set sweep type for pulse measurement
            if var_sweep_type == 'log':
                var_range = np.logspace(np.log10(self.time_start), np.log10(self.time_stop), self.npts,
                                        base=10)
            else:
                var_range = np.linspace(self.time_start, self.time_stop, int(self.npts))

            i = -1;
            for V_Xvalue in V_XvalueRange:
                i = i + 1
                j = 0
                if self.stop_acq == True:
                    break
                for V_Yvalue in V_YvalueRange:
                    if flag_meander == False:
                        j = j - 1
                    t0 = time.time()
                    # Set piezo position
                    self._piezo.gox(V_Xvalue)
                    self._piezo.goz(V_Yvalue)
                    # Determine measurement type
                    if self.mes_type=='Contrast':
                        time.sleep(1e-3)
                        self._mw_device.set_status('OFF')
                    if self.mes_type == 'Contrast_fmax':
                        time.sleep(1e-3)
                        self._mw_device.set_fcw(self.fmax)
                        self._mw_device.set_status('ON')

                    DATA = self._nicard.read_data()
                    Image_xy[i, j] = np.mean(DATA[self.ChannelNumber])
                    self.SigConfocalDataUpdated.emit(Image_xy) 
                    Image_xy_arb[i, j] = np.mean(DATA[self.ChannelNumber])
                    if self.mes_type=='Contrast' or self.mes_type == 'Contrast_fmax':
                        self._mw_device.set_fcw(self.fcw) # For contrast fmax
                        self._mw_device.set_status('ON')
                        self.SigDataUpdated.emit(np.array(DATA[0]), np.array(DATA[self.ChannelNumber]))
                        time.sleep(1e-3)  # Make sure sgn is on
                        DATA2 = self._nicard.read_data()
                        Image_xy_arb[i, j] = 1- np.mean(DATA2[self.ChannelNumber])/Image_xy[i, j]


                    if self.mes_type == 'T1' or self.mes_type == 'Rabi' or self.mes_type == 'Ramsey' or self.mes_type == 'Hahn_echo':
                        self.log.info('start pulse measurement')
                        if self.mes_type == 'Rabi' or self.mes_type == 'Ramsey' or self.mes_type == 'Hahn_echo':
                            self._mw_device.set_status('ON')
                            time.sleep(1e-3)
                        VARResult = []
                        ii = 0
                        for variable in var_range:
                            if self.stop_acq == True:
                                break
                            self._nicard.set_refrence_trigger('Falling',self.Laser_length_s)
                            self._nicard.set_pause_trigger('Low')

                            self._pulser.set_pulse_measurement(self.Laser_length,variable, self.mes_type, self.rabi_period)
                            self._pulser.start_stream()
                            DATA = self._nicard.read_data()

                            DATAavg=np.zeros(self.Laser_length_s)
                            PulseAmp, PulseTime =np.array(DATA[self.ChannelNumber]), DATA[0]
                            for jj in range(int(np.floor(np.size(PulseAmp) / self.Laser_length_s))):
                                DATAavg = DATAavg + PulseAmp[jj * self.Laser_length_s:jj * self.Laser_length_s + self.Laser_length_s]

                            ###  Data   Analysis

                            maxindPulseAmp = np.argmax(PulseAmp)# Set min as zero
                            maxPulseAmpAvg = abs(np.mean(PulseAmp[int(maxindPulseAmp):int(maxindPulseAmp + 100)]))
                            PulseAmp = [kar / abs(maxPulseAmpAvg) for kar in PulseAmp]

                            TimeRes = PulseTime[4] - PulseTime[3]
                            IntTimeSampleSignal = int(np.floor(self.time_signal / TimeRes))
                            IntTimeSampleReference = int(np.floor(self.time_reference / TimeRes))
                            IntTimeSampleSignalStart = int(np.floor(self.time_signal_start / TimeRes))
                            IntTimeSampleReferenceStart = int(np.floor(self.time_reference_start / TimeRes))
                            ind_L_pulseAmp = 0
                            ind_R_pulseAmp = self.Laser_length_s-1
                            Ssample = PulseAmp[ind_L_pulseAmp:ind_L_pulseAmp + IntTimeSampleSignal]
                            Rsamples = PulseAmp[ind_R_pulseAmp - IntTimeSampleReference:ind_R_pulseAmp]
                            Signal = np.trapz(Ssample, dx=5) / (np.size(Ssample) - 1)  # Signal Window
                            Reference = np.trapz(Rsamples, dx=5) / (np.size(Rsamples) - 1)  # Reference Window

                            VARResult.append(Signal / Reference)
                            ii = ii + 1
                            self.SigDataUpdated.emit(var_range[0:ii], np.array(VARResult))


                        # Create a fit
                        if self.mes_type=='T1':
                            popt, pcov = curve_fit(exponenial_func, var_range, VARResult, p0=(.01, 1e-3, 1), maxfev=10000)


                            Image_xy_arb[i, j] =np.array(round(1 / popt[1] * 1e3, 2))
                        else:
                            Image_xy_arb[i, j] = np.array(np.mean(VARResult))
                    if self.mes_type == 'PL':
                        self.SigDataUpdated.emit(np.array(DATA[0]), np.array(DATA[self.ChannelNumber]))
                        time.sleep(1e-3)  # Make sure sgn is on
                    self.SigConfocalArbDataUpdated.emit(Image_xy_arb)
                    if flag_meander == True:
                        j = j + 1
                    if self.stop_acq == True:
                        break

                    t4 = time.time()
                    posread = self._piezo.get_position()

                V_YvalueRange = np.flip(V_YvalueRange)
                flag_meander = not_(flag_meander)
            self._mw_device.set_status('OFF')
            self.SigToggleAction.emit()




    def set_cordinate_sparam(self,xmin,xmax,xnpts,ymin,ymax,ynpts):
        """
		H.Babashah - set the position of the piezo
		"""
        self.xmin = xmin*1e6
        self.xmax = xmax*1e6
        self.xnpts = xnpts
        self.ymin = ymin*1e6
        self.ymax = ymax*1e6
        self.ynpts = ynpts

    def set_move_to_position(self, xpos, ypos,zpos):
        """
		H.Babashah - move the piezo
		@param float xpos: x position in m
		@param float xpos: x position in m
		@param float xpos: x position in m
		"""
        self.xpos = xpos*1e6
        self.ypos = ypos*1e6
        self.zpos = zpos*1e6

    def move_to_position(self):
        """
		H.Babashah - position for simultaneous signal acqusition
		"""
        self._piezo.gox(self.xpos)
        self._piezo.goz(self.ypos)
        self._piezo.goy(self.zpos)
        self.ChannelNumber = 1
        self._nicard.set_timing(self.int_time)
        DATA = self._nicard.read_data()
        self.SigDataUpdated.emit(np.array(DATA[0]), np.array(DATA[self.ChannelNumber]))

    def set_fcw(self, fcw):
        """
		H.Babashah -Set the microwave frequency
		@param float fcw: microwave cw frequency
		"""
        self.fcw = fcw
        self._mw_device.set_fcw(self.fcw)



    def stop_data_acquisition(self,state):
        """
		H.Babashah -stop acquiring data from any DAQ
		"""
        #Fixme mutex threadlock might be required to add

        self.stop_acq = True


    def set_pcw(self, pcw):
        """
		H.Babashah -set microwave power
		"""
        self._mw_device.set_pcw(pcw)
        self.pcw = pcw
    def set_ODMR(self, stime,npts):
        """
		H.Babashah -set and intialize the ODMR measurement
		"""
        self.stime = stime
        self.npts = npts

    def set_sweep_param(self, fmin,fmax,fstep):
        """
		H.Babashah -set sweep parameters of microwave for ODMR measurement
		"""
        self._mw_device.set_sweep_param(fmin,fmax,fstep)
        self.fmin = fmin
        self.fmax = fmax
        self.fstep = fstep
    def set_scope_param(self,int_time,navg):
        """
		H.Babashah -set integration time and number of averages
		"""
        self.int_time = int_time
        self.navg = navg

    def set_mes_type(self, mes_type):
        """
		H.Babashah -Defin the type of confocal measurement
		input is string as follows:
		T1
		T2
		Hahn echo
		ODMR
		"""
        self.mes_type=mes_type
        self.log.info(mes_type)
    def ThresholdL(self,data,t_v):
        """
		H.Babashah -Threshold the lower value of data and t_v 
		return the threshold value in time t_ind
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
        """
		H.Babashah -Threshold the higher value of data and t_v 
		return the threshold value in time t_ind
		"""
        t_ind = -1
        for kop in range(len(data)) :
            if data[-kop-1] >= t_v :
                t_ind = -kop-1
                break
        if t_ind==-1:
            self.log.info('Probably could not find the begining of the pulse, zero set as begining')
        return t_ind
    def set_navg(self, navg):
        """
		H.Babashah -set number of avg for confocal measurement
		"""
        self.navg = navg
    def set_pulse(self, time_start,time_stop,npts,rabi_period):
        """
		H.Babashah - set the pulse parameters 
		"""
        self.time_start = time_start
        self.time_stop = time_stop
        self.npts = npts
        self.rabi_period=rabi_period
    def set_pulse_analysi_param(self, threshold,time_reference,time_signal,time_reference_start,time_signal_start):
        """
		H.Babashah - set the pulse analysis parameters 
		"""
        self.threshold = threshold
        self.time_reference = time_reference
        self.time_signal = time_signal
        self.time_reference_start = time_reference_start
        self.time_signal_start = time_signal_start