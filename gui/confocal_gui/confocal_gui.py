import numpy as np
import os
import pyqtgraph as pg

from core.connector import Connector

from gui.guibase import GUIBase
from gui.guiutils import ColorBar
from gui.colordefs import ColorScaleInferno

from qtpy import QtCore, QtWidgets, uic
from qtwidgets.scan_plotwidget import ScanImageItem

from qtpy import uic


class Confocal_MainWindow(QtWidgets.QMainWindow):
    """
    H.Babashah - class for using dummy_gui
    """
    def __init__(self):
        # Get the path to the *.ui file
        this_dir = os.path.dirname(__file__)
        ui_file = os.path.join(this_dir, 'confocal_gui.ui')

        # Load it
        super(Confocal_MainWindow, self).__init__()
        uic.loadUi(ui_file, self)
        self.show()


class ConfocalGUI(GUIBase):
    """
    H.Babashah - This is the GUI Class for confocal scan
    """

    # declare connectors
    confocallogic = Connector(interface='Confocallogic')
    savelogic = Connector(interface='SaveLogic')

    #Define Signals
    SigStartAcquisition = QtCore.Signal()
    SigStopAcquisition = QtCore.Signal(bool)
    SigFcwChanged = QtCore.Signal(float)
    SigPcwChanged = QtCore.Signal(float)
    SigSetODMRChanged = QtCore.Signal(float,float)
    SigFsweepChanged = QtCore.Signal(float,float,float)
    SigCordinateChanged  = QtCore.Signal(float, float)
    SigScopeParamChanged = QtCore.Signal(float,float)
    def __init__(self, config, **kwargs):
        super().__init__(config=config, **kwargs)


    def on_activate(self):
        """
        Definition, configuration and initialisation of the FFT GUI.

        This init connects all the graphic modules, which were created in the
        *.ui file and configures the event handling between the modules.
        """

        self._confocallogic = self.confocallogic()

        # Use the inherited class 'Ui_ODMRGuiUI' to create now the GUI element:
        self._mw = Confocal_MainWindow()

        # Define data plots
        self.dummy_image = pg.PlotDataItem()
        # Add the display item to the xy and xz ViewWidget, which was defined in the UI file.
        self._mw.dummy_graph.addItem(self.dummy_image)
        self._mw.dummy_graph.setLabel(axis='left', text='Amplitude', units='V')
        self._mw.dummy_graph.setLabel(axis='bottom', text='Time', units='s')
        self._mw.dummy_graph.showGrid(x=True, y=True, alpha=0.8)

        # Add the display item to the xy and depth ViewWidget, which was defined
        # in the UI file:

        raw_data_xy=np.zeros((5,5))
        self.xy_image = ScanImageItem(image=raw_data_xy, axisOrder='row-major')

        #################################################################
        #           Connect the colorbar and their actions              #
        #################################################################
        # Get the colorscale and set the LUTs
        self.my_colors = ColorScaleInferno()
        self.xy_image.setLookupTable(self.my_colors.lut)


        # Label the axes:
        self._mw.xy_ViewWidget.setLabel('bottom', 'X position', units='m')
        self._mw.xy_ViewWidget.setLabel('left', 'Y position', units='m')
        self.xy_cb = ColorBar(self.my_colors.cmap_normed, width=100, cb_min=0, cb_max=100)
        self._mw.xy_cb_ViewWidget.addItem(self.xy_cb)
        self._mw.xy_cb_ViewWidget.hideAxis('bottom')
        self._mw.xy_cb_ViewWidget.setLabel('left', 'Fluorescence', units='V')
        self._mw.xy_cb_ViewWidget.setMouseEnabled(x=False, y=False)
        self._mw.xy_ViewWidget.addItem(self.xy_image)

        ########################################################################
        #                       Connect signals                                #
        ########################################################################
        # Internal user input changed signals
        self._mw.actionStart.triggered.connect(self.start_data_acquisition)
        self._mw.fcw_doubleSpinBox.editingFinished.connect(self.change_fcw)
        self._mw.pcw_doubleSpinBox.editingFinished.connect(self.change_pcw)
        self._mw.stime_doubleSpinBox.editingFinished.connect(self.change_set_ODMR)
        self._mw.npts_doubleSpinBox.editingFinished.connect(self.change_set_ODMR)
        self._mw.int_time_doubleSpinBox.editingFinished.connect(self.change_scope_param)
        self._mw.navg_doubleSpinBox.editingFinished.connect(self.change_scope_param)

        self._mw.fmin_doubleSpinBox.editingFinished.connect(self.change_sweep_param)
        self._mw.fmax_doubleSpinBox.editingFinished.connect(self.change_sweep_param)
        self._mw.fstep_doubleSpinBox.editingFinished.connect(self.change_sweep_param)

        self._mw.xmin_doubleSpinBox.editingFinished.connect(self.change_cordinate_sparam)
        self._mw.xmax_doubleSpinBox.editingFinished.connect(self.change_cordinate_sparam)
        self._mw.xnpts_doubleSpinBox.editingFinished.connect(self.change_cordinate_sparam)
        self._mw.ymin_doubleSpinBox.editingFinished.connect(self.change_cordinate_sparam)
        self._mw.ymax_doubleSpinBox.editingFinished.connect(self.change_cordinate_sparam)
        self._mw.ynpts_doubleSpinBox.editingFinished.connect(self.change_cordinate_sparam)


        # Connections to logic
        self._mw.actionStop.triggered.connect(self.stop_data_acquisition)
        self._mw.int_time_doubleSpinBox.setValue(self._confocallogic.int_time) # Status var
        self._mw.movetoxy_btn.clicked.connect(self._confocallogic.move_to_position)
        self.SigStartAcquisition.connect(self._confocallogic.start_data_acquisition)
        self.SigStopAcquisition.connect(self._confocallogic.stop_data_acquisition)

        self.SigFcwChanged.connect(self._confocallogic.set_fcw, QtCore.Qt.QueuedConnection)
        self._mw.fcw_doubleSpinBox.setValue(self._confocallogic.fcw) # Status var
        self.SigPcwChanged.connect(self._confocallogic.set_pcw, QtCore.Qt.QueuedConnection)

        self._mw.pcw_doubleSpinBox.setValue(self._confocallogic.pcw) # Status var
        self._mw.npts_doubleSpinBox.setValue(self._confocallogic.npts) # Status var
        self.SigSetODMRChanged.connect(self._confocallogic.set_ODMR, QtCore.Qt.QueuedConnection)
        self._mw.stime_doubleSpinBox.setValue(self._confocallogic.stime) # Status var
        self.SigFsweepChanged.connect(self._confocallogic.set_sweep_param, QtCore.Qt.QueuedConnection)
        self.SigCordinateSparamChanged.connect(self._confocallogic.set_cordinate_sparam, QtCore.Qt.QueuedConnection)
        self.SigCordinateChanged.connect(self._confocallogic.set_move_to_position, QtCore.Qt.QueuedConnection)
        self.SigScopeParamChanged.connect(self._confocallogic.set_scope_param, QtCore.Qt.QueuedConnection)


        self._mw.fmax_doubleSpinBox.setValue(self._confocallogic.fmax) # Status var
        self._mw.fmin_doubleSpinBox.setValue(self._confocallogic.fmin) # Status var
        self._mw.fstep_doubleSpinBox.setValue(self._confocallogic.fstep) # Status var
        # Update connections from logic
        self._confocallogic.SigDataUpdated.connect(self.update_plot, QtCore.Qt.QueuedConnection)
        self._confocallogic.SigConfocalDataUpdated.connect(self.update_confocal_plot, QtCore.Qt.QueuedConnection)
        self._confocallogic.SigToggleAction.connect(self.Toggle_actionstart, QtCore.Qt.QueuedConnection)


        # Show the Main FFT GUI:
        self.show()


    def on_deactivate(self):
        """
        H.Babashah Reverse steps of activation and also close the main window and do whatever when a module is closed using closed btn in task manager

        @return int: error code (0:OK, -1:error)
        """
        # Disconnect signals
        self._mw.fcw_doubleSpinBox.editingFinished.disconnect()
        self.SigFcwChanged.disconnect()
        self._mw.pcw_doubleSpinBox.editingFinished.disconnect()
        self.SigPcwChanged.disconnect()
        self._mw.npts_doubleSpinBox.editingFinished.disconnect()
        self._mw.stime_doubleSpinBox.editingFinished.disconnect()
        self.SigSetODMRChanged.disconnect()
        self._mw.fmin_doubleSpinBox.editingFinished.disconnect()
        self.SigFsweepChanged.disconnect()
        self._mw.fmax_doubleSpinBox.editingFinished.disconnect()
        self._mw.fstep_doubleSpinBox.editingFinished.disconnect()
        self.SigCordinateSparamChanged.disconnect()
        self._mw.xmin_doubleSpinBox.editingFinished.disconnect()
        self._mw.xmax_doubleSpinBox.editingFinished.disconnect()
        self._mw.xnpts_doubleSpinBox.editingFinished.disconnect()
        self._mw.ymin_doubleSpinBox.editingFinished.disconnect()
        self._mw.ymax_doubleSpinBox.editingFinished.disconnect()
        self._mw.ynpts_doubleSpinBox.editingFinished.disconnect()
        self._mw.int_time_doubleSpinBox.editingFinished.disconnect()
        self.SigScopeParamChanged.disconnect()
        self._mw.navg_doubleSpinBox.editingFinished.disconnect()



        self._mw.close()
        return 0


    def start_data_acquisition(self):
        """
        start the confocal scan and get the data
        """

        self._mw.actionStart.setEnabled(False)
        self._confocallogic.stop_acq=False
        self.SigStartAcquisition.emit()#self._mw.multi_span_checkBox.isChecked()


    def stop_data_acquisition(self):
        """
        H.Babashah - stop the confocal scan and get the data
        """

        self.SigStopAcquisition.emit(True)
    def Toggle_actionstart(self):
		"""
        Toggle between start and stop
		make the button enabled
        """
        self._mw.actionStart.setEnabled(True)

    def change_fcw(self):
		"""
        set microwave CW frequency
		@param float fcw : microwave frequency in Hz
        """

        fcw = self._mw.fcw_doubleSpinBox.value()
        self.SigFcwChanged.emit(fcw)
    def change_pcw(self):
		"""
        change microwave CW power
		@param float pcw : microwave power in dBm
        """

        pcw = self._mw.pcw_doubleSpinBox.value()
        self.SigPcwChanged.emit(pcw)


    def change_set_ODMR(self):


        stime = self._mw.stime_doubleSpinBox.value()
        npts = self._mw.npts_doubleSpinBox.value()
        self.SigSetODMRChanged.emit(stime,npts)
    def change_sweep_param(self):


        fmin = self._mw.fmin_doubleSpinBox.value()
        fmax = self._mw.fmax_doubleSpinBox.value()
        fstep = self._mw.fstep_doubleSpinBox.value()

        self.SigFsweepChanged.emit(fmin,fmax,fstep)

    def update_plot(self, xdata, ydata):
        """
        Updates the plot.
        """
        self.dummy_image.setData(xdata, ydata)
    def update_confocal_plot(self, xy_image_data):
        """
		Updates the plot.
        """
        minval = np.min(xy_image_data[np.nonzero(xy_image_data)])
        maxval = np.max(xy_image_data[np.nonzero(xy_image_data)])
        self.put_cursor_in_xy_scan()

        xy_viewbox.updateAutoRange()
        xy_viewbox.updateViewRange()

    def change_scope_param(self):
        """
        H. Babashah- Change the scope parameters
        """

        int_time = self._mw.int_time_doubleSpinBox.value()
        navg = self._mw.navg_doubleSpinBox.value()
        self.SigScopeParamChanged.emit(int_time,navg)


    def show(self):
        """
        Taken from Qudi - Make window visible and put it above all other windows.
        """
        self._mw.show()
        self._mw.activateWindow()
        self._mw.raise_()


