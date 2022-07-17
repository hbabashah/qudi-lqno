import numpy as np
import os
import pyqtgraph as pg

from core.connector import Connector

from gui.guibase import GUIBase

from qtpy import QtCore, QtWidgets, uic

from qtpy import uic


class PULSE_MainWindow(QtWidgets.QMainWindow):
    """
    H.Babashah - Create the main window based on pulse ui file
    """
    def __init__(self):
        # Get the path to the *.ui file
        this_dir = os.path.dirname(__file__)
        ui_file = os.path.join(this_dir, 'pulse_gui.ui')

        # Load it
        super(PULSE_MainWindow, self).__init__()
        uic.loadUi(ui_file, self)
        self.show()


class PULSEGUI(GUIBase):
    """
    H.Babashah - This is the GUI Class for pulse measurement using scope or non triggered measurement and generation instruments.

    """

    # declare connectors
    pulselogic = Connector(interface='PULSElogic')
    savelogic = Connector(interface='SaveLogic')

    #Define Signals
    SigStopAcquisition = QtCore.Signal(bool)
    SigStartAcquisition = QtCore.Signal()
    SigPcwChanged = QtCore.Signal(float)
    SigNavgChanged = QtCore.Signal(float)
    SigSetPulseChanged = QtCore.Signal(float,float,float,float)
    SigPulseAnalysisChanged = QtCore.Signal(float,float,float,float,float)
    SigFcwChanged = QtCore.Signal(float)



    def __init__(self, config, **kwargs):
        super().__init__(config=config, **kwargs)


    def on_activate(self):
        """
        Definition, configuration and initialisation of the GUI.

        This init connects all the graphic modules, which were created in the
        *.ui file and configures the event handling between the modules.
        """

        self._pulselogic = self.pulselogic()

        # Use the inherited class 'ui' to create now the GUI element:
        self._mw = PULSE_MainWindow()

        # Define data plots
        self.pulse_exp_image = pg.PlotDataItem()
        # Add the display item to the xy and xz ViewWidget, which was defined in the UI file.
        self._mw.pulse_exp_graph.addItem(self.pulse_exp_image)
        self._mw.pulse_exp_graph.setLabel(axis='left', text='Amplitude', units='a.u.')
        self._mw.pulse_exp_graph.setLabel(axis='bottom', text='Time', units='s')
        self._mw.pulse_exp_graph.showGrid(x=True, y=True, alpha=0.8)
        # Define data plots
        self.pulse_exp_image_pulse = pg.PlotDataItem()
        # Add the display item to the xy and xz ViewWidget, which was defined in the UI file.
        self._mw.pulse_exp_graph_pulse.addItem(self.pulse_exp_image_pulse)
        self._mw.pulse_exp_graph_pulse.setLabel(axis='left', text='Amplitude', units='a.u.')
        self._mw.pulse_exp_graph_pulse.setLabel(axis='bottom', text='Time', units='s')
        self._mw.pulse_exp_graph_pulse.showGrid(x=True, y=True, alpha=0.8)

        ########################################################################
        #                       Connect signals                                #
        ########################################################################
        # Internal user input changed signals
        self._mw.actionStart.triggered.connect(self.start_data_acquisition)
        self._mw.actionStop.triggered.connect(self.stop_data_acquisition)
        self._mw.pcw_doubleSpinBox.editingFinished.connect(self.change_pcw)
        self._mw.navg_doubleSpinBox.editingFinished.connect(self.change_navg)
        self._mw.fcw_doubleSpinBox.editingFinished.connect(self.change_fcw)
        self._mw.time_stop_doubleSpinBox.editingFinished.connect(self.set_pulse)
        self._mw.npts_doubleSpinBox.editingFinished.connect(self.set_pulse)
        self._mw.time_start_doubleSpinBox.editingFinished.connect(self.set_pulse)
        self._mw.rabi_period_doubleSpinBox.editingFinished.connect(self.set_pulse)


        self._mw.threshold_doubleSpinBox.editingFinished.connect(self.change_pulse_analysis_param)
        self._mw.time_reference_doubleSpinBox.editingFinished.connect(self.change_pulse_analysis_param)
        self._mw.time_signal_doubleSpinBox.editingFinished.connect(self.change_pulse_analysis_param)
        self._mw.time_reference_start_doubleSpinBox.editingFinished.connect(self.change_pulse_analysis_param)
        self._mw.time_signal_start_doubleSpinBox.editingFinished.connect(self.change_pulse_analysis_param)

        # Connections to logic
        self._mw.fft_window_comboBox.currentTextChanged.connect(self._pulselogic.set_pulse_type)
        self.SigStartAcquisition.connect(self._pulselogic.start_data_acquisition)
        self.SigStopAcquisition.connect(self._pulselogic.stop_data_acquisition)
        self._mw.time_start_doubleSpinBox.setValue(self._pulselogic.time_start) # Status var
        self._mw.rabi_period_doubleSpinBox.setValue(self._pulselogic.rabi_period) # Status var

        self.SigPcwChanged.connect(self._pulselogic.set_pcw, QtCore.Qt.QueuedConnection)
        self.SigNavgChanged.connect(self._pulselogic.set_navg, QtCore.Qt.QueuedConnection)
        self.SigFcwChanged.connect(self._pulselogic.set_fcw, QtCore.Qt.QueuedConnection)
        self._mw.fcw_doubleSpinBox.setValue(self._pulselogic.fcw) # Status var
        self._mw.pcw_doubleSpinBox.setValue(self._pulselogic.pcw) # Status var
        self._mw.navg_doubleSpinBox.setValue(self._pulselogic.navg) # Status var
        self._mw.npts_doubleSpinBox.setValue(self._pulselogic.npts) # Status var
        self.SigSetPulseChanged.connect(self._pulselogic.set_pulse, QtCore.Qt.QueuedConnection)
        self._mw.time_stop_doubleSpinBox.setValue(self._pulselogic.time_stop) # Status var
        self.SigPulseAnalysisChanged.connect(self._pulselogic.set_pulse_analysi_param, QtCore.Qt.QueuedConnection)
        self._mw.threshold_doubleSpinBox.setValue(self._pulselogic.threshold) # Status var
        self._mw.time_reference_doubleSpinBox.setValue(self._pulselogic.time_reference) # Status var
        self._mw.time_signal_doubleSpinBox.setValue(self._pulselogic.time_signal) # Status var
        self._mw.time_reference_start_doubleSpinBox.setValue(self._pulselogic.time_reference_start) # Status var
        self._mw.time_signal_start_doubleSpinBox.setValue(self._pulselogic.time_signal_start) # Status var
        # Update connections from logic
        self._pulselogic.SigDataUpdated.connect(self.update_plot, QtCore.Qt.QueuedConnection)
        self._pulselogic.SigToggleAction.connect(self.Toggle_actionstart, QtCore.Qt.QueuedConnection)

        self._pulselogic.SigDataPulseUpdated.connect(self.update_plot_pulse, QtCore.Qt.QueuedConnection)

        # Show the Main GUI:
        self.show()


    def on_deactivate(self):
        """
        Reverse steps of activation and also close the main window and do whatever when a module is closed using closed btn in task manager

        @return int: error code (0:OK, -1:error)
        """
        # Disconnect signals
        self._mw.fft_window_comboBox.currentTextChanged.disconnect()
        self._mw.time_start_doubleSpinBox.editingFinished.disconnect()
        self._mw.rabi_period_doubleSpinBox.editingFinished.disconnect()

        self._mw.pcw_doubleSpinBox.editingFinished.disconnect()
        self._mw.navg_doubleSpinBox.editingFinished.disconnect()
        self.SigPcwChanged.disconnect()
        self.SigNavgChanged.disconnect()
        self._mw.npts_doubleSpinBox.editingFinished.disconnect()
        self._mw.time_stop_doubleSpinBox.editingFinished.disconnect()
        self._mw.threshold_doubleSpinBox.editingFinished.disconnect()
        self._mw.time_reference_doubleSpinBox.editingFinished.disconnect()
        self._mw.time_signal_doubleSpinBox.editingFinished.disconnect()
        self._mw.time_reference_start_doubleSpinBox.editingFinished.disconnect()
        self._mw.time_signal_start_doubleSpinBox.editingFinished.disconnect()
        self._mw.fcw_doubleSpinBox.editingFinished.disconnect()
        self.SigFcwChanged.disconnect()
        self._mw.close()
        return 0

    def start_data_acquisition(self):
        """
        Send user order to start acquisition to the logic.
        """
        #self._mw.actionStart.setEnabled(False)
        #self._mw.actionStop.setEnabled(True)
        self._mw.actionStart.setEnabled(False)
        self._pulselogic.stop_acq=False
        self.SigStartAcquisition.emit()#self._mw.multi_span_checkBox.isChecked()

    def stop_data_acquisition(self):
        """
        stop the confocal scan and get the data
        """

        self.SigStopAcquisition.emit(True)
    def Toggle_actionstart(self):
        """
        toggle between strat and stop buttons.
        """
        self._mw.actionStart.setEnabled(True)
    def change_pcw(self):
        """
        Change microwave CW power in Hz
        """
        pcw = self._mw.pcw_doubleSpinBox.value()
        self.SigPcwChanged.emit(pcw)
    def change_navg(self):
        """
        Change number of averages
        """

        navg = self._mw.navg_doubleSpinBox.value()
        self.SigNavgChanged.emit(navg)

    def set_pulse(self):
        """
        set the pulse generator paramters
        """
        time_start = self._mw.time_start_doubleSpinBox.value()
        time_stop = self._mw.time_stop_doubleSpinBox.value()
        # number of points
        npts = self._mw.npts_doubleSpinBox.value()
        rabi_period = self._mw.rabi_period_doubleSpinBox.value()
        self.SigSetPulseChanged.emit(time_start,time_stop,npts,rabi_period)
    def change_pulse_analysis_param(self):
        """
        change pulse analysis paramters
        """

        threshold = self._mw.threshold_doubleSpinBox.value()
        time_reference = self._mw.time_reference_doubleSpinBox.value()
        time_reference_start = self._mw.time_reference_start_doubleSpinBox.value()
        time_signal = self._mw.time_signal_doubleSpinBox.value()
        time_signal_start = self._mw.time_signal_start_doubleSpinBox.value()

        self.SigPulseAnalysisChanged.emit(threshold,time_reference,time_signal,time_reference_start,time_signal_start)
    def update_plot(self, xdata, ydata):
        """
        Updates the plot for measurement result
        @param array xdata: time axis data in s
        @param array ydata: pulse measurement result in a.u.
        """

        self.pulse_exp_image.setData(xdata, ydata)
    def update_plot_pulse(self, xdata, ydata):
        """
        Updates the plot for pulse result
        @param array xdata: time axis data in s
        @param array ydata: single averaged pulse amplitude.
        """

        self.pulse_exp_image_pulse.setData(xdata, ydata)

    def change_fcw(self):
        """
        Change the microwave frequency
        """

        fcw = self._mw.fcw_doubleSpinBox.value()
        self.SigFcwChanged.emit(fcw)
    def show(self):
        """
        Taken from Qudi - Make window visible and put it above all other windows.
        """
        self._mw.show()
        self._mw.activateWindow()
        self._mw.raise_()
