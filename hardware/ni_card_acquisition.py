import copy
import numpy as np
import ctypes
import time
import PyDAQmx as daq

from core.module import Base
from core.configoption import ConfigOption
from core.util.helpers import natural_sort
from interface.data_instream_interface import DataInStreamInterface, DataInStreamConstraints
from interface.dummy_interface import dummy_interface

from interface.process_control_interface import ProcessControlInterface
from interface.data_instream_interface import StreamingMode, StreamChannelType, StreamChannel


class NICard_Acquisition(Base, dummy_interface):
    """
    H.babashah - NI card hardware for continuous acquisition on analog inputs
    """

    # config options
    _device_name = ConfigOption(name='device_name', default='Dev1', missing='warn')
    _device_name_ao = ConfigOption(name='device_name_ao', default='Dev3', missing='warn')
    _analog_inputs = ConfigOption(name='analog_inputs', default=list(), missing='warn')
    _analog_outputs = ConfigOption(name='analog_outputs', default=list(), missing='warn')
    _trigger_terminal = ConfigOption(name='trigger_terminal', default='PFI0', missing='info')
    _sampling_frequency = ConfigOption(name='sampling_frequency', default=200*10**3, missing='info')


    def on_activate(self):
        """
        H.babashah - Creates and starts the continuous acquisition task. If buffer is full, all non-used data will be automatically destroyed.
        """
        # Create the acquisition task
        self._ai_task = daq.TaskHandle()
        self._ao_task = daq.TaskHandle()
        self.clock_task = daq.TaskHandle()
        self.read = daq.int32()
        self.samplesWritten = daq.int32()

        daq.DAQmxCreateTask("", daq.byref(self._ai_task))

        # Create the list of channels to acquire
        self.nb_chan = 0
        for channel in self._analog_inputs:
            daq.CreateAIVoltageChan(self._ai_task, self._device_name+'/'+channel, None, daq.DAQmx_Val_RSE, -10, 10, daq.DAQmx_Val_Volts, None) # RSE or NRSE or Diff
            self.nb_chan += 1

        # self.nb_chan = 0
        # for channel in self._analog_outputs:
        #     daq.CreateAOVoltageChan(self._ao_task, self._device_name_ao+'/'+channel, None, daq.DAQmx_Val_Diff, -10, 10, daq.DAQmx_Val_Volts, None) # RSE or NRSE or Diff
        #     self.nb_chan += 1


    def on_deactivate(self):
        daq.DAQmxStopTask(self._ai_task)
        daq.DAQmxClearTask(self._ai_task)

    def set_timing(self, acquisition_time):
        """ H.Babashah - Define the timing of the acquisition. """
        self._acquisition_time = acquisition_time
        self.nb_samps_per_chan = int(self._acquisition_time*self._sampling_frequency)
        self._buffer_size = int(self._acquisition_time*self._sampling_frequency*self.nb_chan)
        self.raw_data = np.zeros(int(self._buffer_size))
        daq.CfgSampClkTiming(self._ai_task, '', int(self._sampling_frequency), daq.DAQmx_Val_Rising,
                             daq.DAQmx_Val_FiniteSamps, self.nb_samps_per_chan)
        self.outputRate=1000
        self.numSamples = 2
        # daq.CfgSampClkTiming(self._ao_task,'', self.outputRate, daq.DAQmx_Val_Rising,
        #                      daq.DAQmx_Val_FiniteSamps, self.numSamples)

        self.data = np.ndarray((self.nb_chan+1, self.nb_samps_per_chan))
    def set_trigger(self, edge):
        """ H.Babashah - Define the edge of the external trigger. """

        if edge == 'Rising':
            daq.CfgDigEdgeStartTrig(self._ai_task, self._trigger_terminal, daq.DAQmx_Val_Rising)
        elif edge == 'Falling':
            daq.CfgDigEdgeStartTrig(self._ai_task, self._trigger_terminal, daq.DAQmx_Val_Falling)

    def set_pause_trigger(self, when):
        """ H.Babashah - it stop acquiring the data while triggered. """

        daq.SetPauseTrigType(self._ai_task,
            daq.DAQmx_Val_DigLvl)  # Pause the measurement or generation while a digital signal is at either a high or low state.
        daq.SetDigLvlPauseTrigSrc(self._ai_task,
            self._trigger_terminal)  # Specifies the name of a terminal where there is a digital signal to use as the source of the Pause Trigger.
        if when == 'High':
            daq.SetDigLvlPauseTrigWhen(self._ai_task,
                daq.DAQmx_Val_High)  # Specifies whether the task pauses while the signal is high or low
        elif when == 'Low':
            daq.SetDigLvlPauseTrigWhen(self._ai_task,
                daq.DAQmx_Val_Low)  # Specifies whether the task pauses while the signal is high or low



    def set_refrence_trigger(self, edge,pretriggerSamples):
        """ H.Babashah - It acquire the data before the trigger """
        if edge == 'Rising':
            daq.CfgDigEdgeRefTrig(self._ai_task,self._trigger_terminal, daq.DAQmx_Val_Rising, pretriggerSamples)  # C channel DDG
        elif edge == 'Falling':
            daq.CfgDigEdgeRefTrig(self._ai_task,self._trigger_terminal, daq.DAQmx_Val_Falling, pretriggerSamples)  # C channel DDG

    def start_acquisition(self):
        """ H.Babashah - Start the acquisition task.
        It seems that using the start task generates an error when trying to read data several times for "continuous acquisition".
        Only calling read several times seems fine. """
        pass #daq.DAQmxStartTask(self._ai_task)

    def stop_acquisition(self):
        daq.DAQmxStopTask(self._ai_task)

    def read_data(self):
        time_data = np.linspace(0, self._acquisition_time, int(self.nb_samps_per_chan))
        t0 = time.time()
        daq.ReadAnalogF64(self._ai_task, self.nb_samps_per_chan, 50, daq.DAQmx_Val_GroupByChannel, self.raw_data, self._buffer_size, ctypes.byref(self.read), None)
        t1 = time.time()
        print(t1-t0)
        self.data[0] = time_data
        for i in range(self.nb_chan):
            self.data[i+1] = np.split(self.raw_data, self.nb_chan)[i]
        return self.data

    # def write_ao(self,ao_value):
    #     self._ao_value=ao_value
    #     time_data = np.linspace(0, self._acquisition_time, int(self.nb_samps_per_chan))
    #     daq.ReadAnalogF64(self._ai_task, self.nb_samps_per_chan, 50, daq.DAQmx_Val_GroupByChannel, self.raw_data, self._buffer_size, ctypes.byref(self.read), None)
    #     daq.WriteAnalogF64(self._ao_task,numSampsPerChan=self.numSamples, autoStart=True, timeout=1.0, dataLayout=daq.DAQmx_Val_GroupByChannel, writeArray=self._ao_value, reserved=None,
    #                                  sampsPerChanWritten=ctypes.byref(self.samplesWritten))

