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

class FFTLogic(GenericLogic):

    # Connectors
    fftanalyzer = Connector(interface='FFTInterface')
    savelogic = Connector(interface='SaveLogic')
    taskrunner = Connector(interface='TaskRunner')

    resolution = StatusVar('resolution', 100)
    span_list = ConfigOption(name='span_list', default=list(), missing='info')

    # Update signals
    SigDataUpdated = QtCore.Signal(np.ndarray, np.ndarray)

    def __init__(self, config, **kwargs):
        super().__init__(config=config, **kwargs)
        self.threadlock = Mutex()

    def on_activate(self):

        # Get connectors
        self._fft_device = self.fftanalyzer()
        self._save_logic = self.savelogic()
        self._taskrunner = self.taskrunner()

        """ Needs to be implemented
        # Get hardware constraints
        limits = self.get_hw_constraints()
        """

        self.data_freq = np.array([])
        self.data_spectrum = np.array([])
        self.RBW = np.array([])

        self.project = 'Select'
        self.module_name = None

    def on_deactivate(self):
        """
        Deinitialisation performed during deactivation of the module.
        """
        # Disconnect signals
        self.sigDataUpdated.disconnect()

        self._mw.fft_window_comboBox.currentTextChanged.connect(self._fft_logic.set_fft_window)
        self._mw.acquire_data_pushButton.clicked.connect(self._fft_logic.start_data_acquisition)


    def set_fft_resolution(self, resolution):
        self._fft_device.set_resolution(resolution)
        self.resolution = resolution


    def set_fft_window(self, window):
        self._fft_device.set_window(window)


    def set_fft_unit(self, unit):
        self._fft_device.set_unit(unit)


    def start_data_acquisition(self, multi_span):
        if multi_span is False:
            self.data_freq, self.data_spectrum = self._fft_device.get_acquisition()
            self.RBW = self._fft_device.get_rbw()
            self.SigDataUpdated.emit(self.data_freq, self.data_spectrum)
        else:
            self.data_freq = np.array([])
            self.data_spectrum = np.array([])
            self.RBW = np.array([])
            for span in self.span_list:
                self._fft_device.set_span(span)
                self.new_data_freq, self.new_data_spectrum = self._fft_device.get_acquisition()
                first_index = 0

                if len(self.data_freq) != 0:
                    last_freq = self.data_freq[-1]
                    continue_freq_index = True
                    while continue_freq_index:
                        if self.new_data_freq[first_index] <= last_freq:
                            first_index += 1
                        else:
                            continue_freq_index = False

                self.data_freq = np.append(self.data_freq, self.new_data_freq[first_index:])
                self.data_spectrum = np.append(self.data_spectrum, self.new_data_spectrum[first_index:])
                self.RBW = np.append(self.RBW, self._fft_device.get_rbw())
                self.SigDataUpdated.emit(self.data_freq, self.data_spectrum)


    def save_fft_data(self, project, module_name, tag=None, colorscale_range=None, percentile_range=None):
        """
        H. Babashah - Inspired from Qudi - Saves the current fft spectrum data to a file.
        """

        if project != 'Select':
            timestamp = datetime.datetime.now()
            filepath = self._save_logic.get_path_for_module(project=project, module_name = module_name)
            print(filepath)

            if tag is None:
                filelabel_raw = None
            else:
                filelabel_raw = tag


            data = OrderedDict()
            data['Frequency (Hz)'] = self.data_freq
            data['Spectrum (to define)'] = self.data_spectrum
            parameters = OrderedDict()
            parameters['RBW'] = self.RBW

            self._save_logic.save_data(data,
                                       filepath=filepath,
                                       parameters=parameters,
                                       filelabel=filelabel_raw,
                                       fmt='%.6e',
                                       delimiter='\t',
                                       timestamp=timestamp)

            """
            Need to add the graphical save
            """

            self.log.info('FFT spectrum data saved to:\n{0}'.format(filepath))

        else:
            self.log.warn('No project selected to save the data of FFT spectrum.')

        return