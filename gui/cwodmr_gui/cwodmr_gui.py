import numpy as np
import os
import pyqtgraph as pg

from core.connector import Connector

from gui.guibase import GUIBase

from qtpy import QtCore, QtWidgets, uic

from qtpy import uic


class CWODMR_MainWindow(QtWidgets.QMainWindow):
    """
    H.Babashah - create the main window based on cwodmr ui file
    """
    def __init__(self):
        # Get the path to the *.ui file
        this_dir = os.path.dirname(__file__)
        ui_file = os.path.join(this_dir, 'cwodmr_gui.ui')

        # Load it
        super(CWODMR_MainWindow, self).__init__()
        uic.loadUi(ui_file, self)
        self.show()


class CWODMRGUI(GUIBase):
    """
    H.Babashah - CW ODMR GUI class to sweep microwave frequency and show the PL using non trigger hardwares
    """

    # declare connectors
    cwodmrlogic = Connector(interface='CWODMRlogic')
    savelogic = Connector(interface='SaveLogic')

    #Define Signals
    SigStartAcquisition = QtCore.Signal()
    SigStopAcquisition = QtCore.Signal(bool)
    SigPcwChanged = QtCore.Signal(float)
    SigSetODMRChanged = QtCore.Signal(float)
    SigScopeParamChanged = QtCore.Signal(float,float)
    SigFsweepChanged = QtCore.Signal(float,float,float)

    def __init__(self, config, **kwargs):
        super().__init__(config=config, **kwargs)


    def on_activate(self):
        """
         Definition, configuration and initialisation of the GUI.

        This init connects all the graphic modules, which were created in the
        *.ui file and configures the event handling between the modules.
        """

        self._cwodmrlogic = self.cwodmrlogic()

        # Use the inherited class 'ui' to create now the GUI element:
        self._mw = CWODMR_MainWindow()

        # Define data plots
        self.dummy_image = pg.PlotDataItem()
        # Add the display item to the xy and xz ViewWidget, which was defined in the UI file.
        self._mw.dummy_graph.addItem(self.dummy_image)
        self._mw.dummy_graph.setLabel(axis='left', text='Amplitude', units='Volts')
        self._mw.dummy_graph.setLabel(axis='bottom', text='Frequency', units='Hz')
        self._mw.dummy_graph.showGrid(x=True, y=True, alpha=0.8)

        ########################################################################
        #                       Connect signals                                #
        ########################################################################
        # Internal user input changed signals
        self._mw.actionStart.triggered.connect(self.start_data_acquisition)
        self._mw.actionStop.triggered.connect(self.stop_data_acquisition)
        self._mw.pcw_doubleSpinBox.editingFinished.connect(self.change_pcw)
        self._mw.stime_doubleSpinBox.editingFinished.connect(self.change_set_ODMR)
        self._mw.navg_doubleSpinBox.editingFinished.connect(self.change_scope_param)
        self._mw.npts_doubleSpinBox.editingFinished.connect(self.change_scope_param)

        self._mw.fmin_doubleSpinBox.editingFinished.connect(self.change_sweep_param)
        self._mw.fmax_doubleSpinBox.editingFinished.connect(self.change_sweep_param)
        self._mw.fstep_doubleSpinBox.editingFinished.connect(self.change_sweep_param)


        # Connections to logic
        self.SigStartAcquisition.connect(self._cwodmrlogic.start_data_acquisition)
        self.SigStopAcquisition.connect(self._cwodmrlogic.stop_data_acquisition)
        self.SigPcwChanged.connect(self._cwodmrlogic.set_pcw, QtCore.Qt.QueuedConnection)
        self._mw.pcw_doubleSpinBox.setValue(self._cwodmrlogic.pcw) # Status var
        self._mw.npts_doubleSpinBox.setValue(self._cwodmrlogic.npts) # Status var
        self._mw.navg_doubleSpinBox.setValue(self._cwodmrlogic.navg) # Status var
        self.SigSetODMRChanged.connect(self._cwodmrlogic.set_ODMR, QtCore.Qt.QueuedConnection)
        self.SigScopeParamChanged.connect(self._cwodmrlogic.set_scope_param, QtCore.Qt.QueuedConnection)
        self._mw.stime_doubleSpinBox.setValue(self._cwodmrlogic.stime) # Status var
        self.SigFsweepChanged.connect(self._cwodmrlogic.set_sweep_param, QtCore.Qt.QueuedConnection)
        self._mw.fmax_doubleSpinBox.setValue(self._cwodmrlogic.fmax) # Status var
        self._mw.fmin_doubleSpinBox.setValue(self._cwodmrlogic.fmin) # Status var
        self._mw.fstep_doubleSpinBox.setValue(self._cwodmrlogic.fstep) # Status var

        # Update connections from logic
        self._cwodmrlogic.SigDataUpdated.connect(self.update_plot, QtCore.Qt.QueuedConnection)
        self._cwodmrlogic.SigToggleAction.connect(self.Toggle_actionstart, QtCore.Qt.QueuedConnection)



        # Show the Main CWODMR GUI:
        self.show()


    def on_deactivate(self):
        """
        H.Babashah - Reverse steps of activation and also close the main window and do whatever when a module is closed using closed btn in task manager

        @return int: error code (0:OK, -1:error)
        """
        # Disconnect signals

        self._mw.pcw_doubleSpinBox.editingFinished.disconnect()
        self.SigPcwChanged.disconnect()
        self._mw.stime_doubleSpinBox.editingFinished.disconnect()
        self.SigSetODMRChanged.disconnect()
        self._mw.navg_doubleSpinBox.editingFinished.disconnect()
        self.SigScopeParamChanged.disconnect()
        self._mw.fmin_doubleSpinBox.editingFinished.disconnect()
        self.SigFsweepChanged.disconnect()
        self._mw.fmax_doubleSpinBox.editingFinished.disconnect()
        self._mw.fstep_doubleSpinBox.editingFinished.disconnect()
        self._mw.close()
        return 0


    def start_data_acquisition(self):
        """
        H.Babashah - Send user order to start acquisition to the logic.
        """
        self._mw.actionStart.setEnabled(False)
        self._cwodmrlogic.stop_acq=False
        self.SigStartAcquisition.emit()
    def Toggle_actionstart(self):
        """
        H.Babashah - toggle between strat and stop buttons.
        """
        self._mw.actionStart.setEnabled(True)

    def stop_data_acquisition(self):
        """
        H.Babashah - stop the ODMR
        """
        self.SigStopAcquisition.emit(True)
    def change_pcw(self):
        """
        H.Babashah - set the microwave CW power
        """

        pcw = self._mw.pcw_doubleSpinBox.value()
        self.SigPcwChanged.emit(pcw)


    def change_set_ODMR(self):
        """
        H.Babashah - update ODMR parameters
        """
        # sert step time for the sweep
        stime = self._mw.stime_doubleSpinBox.value()
        self.SigSetODMRChanged.emit(stime)
    def change_scope_param(self):
        """
        H.Babashah - scope parameters
        """
        # number of averages
        navg = self._mw.navg_doubleSpinBox.value()
        #number of points
        npts = self._mw.npts_doubleSpinBox.value()
        self.SigScopeParamChanged.emit(navg,npts)
    def change_sweep_param(self):
        """
        H.Babashah - update microwave frequency sweep parameters
        """
        # frequency sweep paramters in Hz
        fmin = self._mw.fmin_doubleSpinBox.value()
        fmax = self._mw.fmax_doubleSpinBox.value()
        fstep = self._mw.fstep_doubleSpinBox.value()

        self.SigFsweepChanged.emit(fmin,fmax,fstep)
    def update_plot(self, xdata, ydata):
        """
        H.Babashah - Updates the plot.
        @param array xdata: frequency axis of the ODMR plot
        @param array ydata: PL axis of the ODMR plot
        """

        self.dummy_image.setData(xdata, ydata)

    def show(self):
        """
        H. Babashah - Taken from Qudi - Make window visible and put it above all other windows.
        """
        self._mw.show()
        self._mw.activateWindow()
        self._mw.raise_()
