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
        ui_file = os.path.join(this_dir, 'confocal_gui_complex.ui')

        # Load it
        super(Confocal_MainWindow, self).__init__()
        uic.loadUi(ui_file, self)
        self.show()


class ConfocalComplexGUI(GUIBase):
    """
    H.Babashah - This is the GUI Class for confocal scan
    """

    # declare connectors
    confocallogic = Connector(interface='Confocallogiccomplex')
    savelogic = Connector(interface='SaveLogic')

    #Define Signals
    SigStartAcquisition = QtCore.Signal()
    SigStopAcquisition = QtCore.Signal(bool)
    SigFcwChanged = QtCore.Signal(float)
    SigPcwChanged = QtCore.Signal(float)
    SigSetODMRChanged = QtCore.Signal(float,float)
    SigFsweepChanged = QtCore.Signal(float,float,float)
    SigCordinateSparamChanged = QtCore.Signal(float, float, float,float,float,float)
    SigCordinateChanged  = QtCore.Signal(float, float,float)
    SigScopeParamChanged = QtCore.Signal(float,float)
    SigSetPulseChanged = QtCore.Signal(float,float,float,float)
    SigPulseAnalysisChanged = QtCore.Signal(float,float,float,float,float)
    SigNavgChanged = QtCore.Signal(float)

    def __init__(self, config, **kwargs):
        super().__init__(config=config, **kwargs)


    def on_activate(self):
        """
        H.Babashah - Definition, configuration and initialisation of the FFT GUI.

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
        self.xy_image_arb = ScanImageItem(image=raw_data_xy, axisOrder='row-major')

        #################################################################
        #           Connect the colorbar and their actions              #
        #################################################################
        # Get the colorscale and set the LUTs
        self.my_colors = ColorScaleInferno()
        self.xy_image.setLookupTable(self.my_colors.lut)
        self.xy_image_arb.setLookupTable(self.my_colors.lut)


        # Label the axes:
        self._mw.xy_ViewWidget.setLabel('bottom', 'X position', units='m')
        self._mw.xy_ViewWidget.setLabel('left', 'Y position', units='m')
        self.xy_cb = ColorBar(self.my_colors.cmap_normed, width=100, cb_min=0, cb_max=100)
        self._mw.xy_cb_ViewWidget.addItem(self.xy_cb)
        self._mw.xy_cb_ViewWidget.hideAxis('bottom')
        self._mw.xy_cb_ViewWidget.setLabel('left', 'Fluorescence', units='mV')
        self._mw.xy_cb_ViewWidget.setMouseEnabled(x=False, y=False)
        self._mw.xy_ViewWidget.addItem(self.xy_image)

        self._mw.xy_ViewWidget_arb.setLabel('bottom', 'X position', units='m')
        self._mw.xy_ViewWidget_arb.setLabel('left', 'Y position', units='m')
        self.xy_cb_arb = ColorBar(self.my_colors.cmap_normed, width=100, cb_min=0, cb_max=100)
        self._mw.xy_cb_ViewWidget_arb.addItem(self.xy_cb_arb)
        self._mw.xy_cb_ViewWidget_arb.hideAxis('bottom')
        self._mw.xy_cb_ViewWidget_arb.setLabel('left', 'a.u.', units='x1e3')
        self._mw.xy_cb_ViewWidget_arb.setMouseEnabled(x=False, y=False)
        self._mw.xy_ViewWidget_arb.addItem(self.xy_image_arb)

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

        self._mw.time_stop_doubleSpinBox.editingFinished.connect(self.set_pulse)
        self._mw.npts_doubleSpinBox.editingFinished.connect(self.set_pulse)
        self._mw.time_start_doubleSpinBox.editingFinished.connect(self.set_pulse)
        self._mw.rabi_period_doubleSpinBox.editingFinished.connect(self.set_pulse)


        self._mw.threshold_doubleSpinBox.editingFinished.connect(self.change_pulse_analysis_param)
        self._mw.time_reference_doubleSpinBox.editingFinished.connect(self.change_pulse_analysis_param)
        self._mw.time_signal_doubleSpinBox.editingFinished.connect(self.change_pulse_analysis_param)
        self._mw.time_reference_start_doubleSpinBox.editingFinished.connect(self.change_pulse_analysis_param)
        self._mw.time_signal_start_doubleSpinBox.editingFinished.connect(self.change_pulse_analysis_param)


        self._mw.fmin_doubleSpinBox.editingFinished.connect(self.change_sweep_param)
        self._mw.fmax_doubleSpinBox.editingFinished.connect(self.change_sweep_param)
        self._mw.fstep_doubleSpinBox.editingFinished.connect(self.change_sweep_param)

        self._mw.xmin_doubleSpinBox.editingFinished.connect(self.change_cordinate_sparam)
        self._mw.xmax_doubleSpinBox.editingFinished.connect(self.change_cordinate_sparam)
        self._mw.xnpts_doubleSpinBox.editingFinished.connect(self.change_cordinate_sparam)
        self._mw.ymin_doubleSpinBox.editingFinished.connect(self.change_cordinate_sparam)
        self._mw.ymax_doubleSpinBox.editingFinished.connect(self.change_cordinate_sparam)
        self._mw.ynpts_doubleSpinBox.editingFinished.connect(self.change_cordinate_sparam)

        self._mw.xpos_doubleSpinBox.editingFinished.connect(self.change_cordinate)
        self._mw.ypos_doubleSpinBox.editingFinished.connect(self.change_cordinate)
        self._mw.zpos_doubleSpinBox.editingFinished.connect(self.change_cordinate)
        self._mw.actionStop.triggered.connect(self.stop_data_acquisition)

        # Connections to logic
        self._mw.mes_type_window_comboBox.currentTextChanged.connect(self._confocallogic.set_mes_type)
        self._mw.channel_window_comboBox.currentTextChanged.connect(self._confocallogic.set_channel)
        self._mw.int_time_doubleSpinBox.setValue(self._confocallogic.int_time) # Status var
        self._mw.movetoxy_btn.clicked.connect(self._confocallogic.move_to_position)
        self.SigStartAcquisition.connect(self._confocallogic.start_data_acquisition)
        self.SigStopAcquisition.connect(self._confocallogic.stop_data_acquisition)
        self.SigNavgChanged.connect(self._confocallogic.set_navg, QtCore.Qt.QueuedConnection)

        self._mw.time_start_doubleSpinBox.setValue(self._confocallogic.time_start) # Status var
        self._mw.rabi_period_doubleSpinBox.setValue(self._confocallogic.rabi_period) # Status var
        self._mw.navg_doubleSpinBox.setValue(self._confocallogic.navg) # Status var
        self._mw.npts_doubleSpinBox.setValue(self._confocallogic.npts) # Status var
        self.SigSetPulseChanged.connect(self._confocallogic.set_pulse, QtCore.Qt.QueuedConnection)
        self._mw.time_stop_doubleSpinBox.setValue(self._confocallogic.time_stop) # Status var
        self.SigPulseAnalysisChanged.connect(self._confocallogic.set_pulse_analysi_param, QtCore.Qt.QueuedConnection)
        self._mw.threshold_doubleSpinBox.setValue(self._confocallogic.threshold) # Status var
        self._mw.time_reference_doubleSpinBox.setValue(self._confocallogic.time_reference) # Status var
        self._mw.time_signal_doubleSpinBox.setValue(self._confocallogic.time_signal) # Status var
        self._mw.time_reference_start_doubleSpinBox.setValue(self._confocallogic.time_reference_start) # Status var
        self._mw.time_signal_start_doubleSpinBox.setValue(self._confocallogic.time_signal_start) # Status var


        self.SigFcwChanged.connect(self._confocallogic.set_fcw, QtCore.Qt.QueuedConnection)
        self._mw.fcw_doubleSpinBox.setValue(self._confocallogic.fcw) # Status var
        self.SigPcwChanged.connect(self._confocallogic.set_pcw, QtCore.Qt.QueuedConnection)

        self._mw.pcw_doubleSpinBox.setValue(self._confocallogic.pcw) # Status var
        self._mw.npts_ODMR_doubleSpinBox.setValue(self._confocallogic.npts) # Status var
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
        self._confocallogic.SigConfocalArbDataUpdated.connect(self.update_confocal_arb_plot, QtCore.Qt.QueuedConnection)
        self._confocallogic.SigToggleAction.connect(self.Toggle_actionstart, QtCore.Qt.QueuedConnection)


        # Show the Main FFT GUI:
        self.show()


    def on_deactivate(self):
        """
        H.Babashah & F. Baeto - Reverse steps of activation and also close the main window and do whatever when a module is closed using closed btn in task manager

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
        self._mw.time_start_doubleSpinBox.editingFinished.disconnect()
        self._mw.rabi_period_doubleSpinBox.editingFinished.disconnect()
        self._mw.navg_doubleSpinBox.editingFinished.disconnect()
        self.SigNavgChanged.disconnect()
        self._mw.close()
        return 0


    def start_data_acquisition(self):
        """
        H.Babashah - start the confocal scan and get the data
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
        self._mw.actionStart.setEnabled(True)

    def change_fcw(self):


        fcw = self._mw.fcw_doubleSpinBox.value()
        self.SigFcwChanged.emit(fcw)
    def change_pcw(self):


        pcw = self._mw.pcw_doubleSpinBox.value()
        self.SigPcwChanged.emit(pcw)


    def change_set_ODMR(self):


        stime = self._mw.stime_doubleSpinBox.value()
        nptsODMR = self._mw.npts_ODMR_doubleSpinBox.value()
        self.SigSetODMRChanged.emit(stime,nptsODMR)
    def change_sweep_param(self):


        fmin = self._mw.fmin_doubleSpinBox.value()
        fmax = self._mw.fmax_doubleSpinBox.value()
        fstep = self._mw.fstep_doubleSpinBox.value()

        self.SigFsweepChanged.emit(fmin,fmax,fstep)


    def change_cordinate_sparam(self):


        xmin = self._mw.xmin_doubleSpinBox.value()
        xmax = self._mw.xmax_doubleSpinBox.value()
        xnpts = self._mw.xnpts_doubleSpinBox.value()
        ymin = self._mw.ymin_doubleSpinBox.value()
        ymax = self._mw.ymax_doubleSpinBox.value()
        ynpts = self._mw.ynpts_doubleSpinBox.value()
        self.SigCordinateSparamChanged.emit(xmin,xmax,xnpts,ymin,ymax,ynpts)

    def change_cordinate(self):


        xpos = self._mw.xpos_doubleSpinBox.value()
        ypos = self._mw.ypos_doubleSpinBox.value()
        zpos = self._mw.zpos_doubleSpinBox.value()

        self._confocallogic.set_move_to_position(xpos,ypos,zpos)
    def update_plot(self, xdata, ydata):
        """
        H.Babashah - Updates the plot.
        """
        self.dummy_image.setData(xdata, ydata)
    def update_confocal_plot(self, xy_image_data):
        """
        H. Babashah - Updates the plot.
        #Fixme Pcolor map instead of having imagexy
        """
        minval = np.min(xy_image_data[np.nonzero(xy_image_data)])
        maxval = np.max(xy_image_data[np.nonzero(xy_image_data)])
        self.xy_image.setImage(image=xy_image_data,levels=(minval, maxval))
        print(minval)
        print(maxval)
        self.xy_cb.refresh_colorbar(minval*1e3, maxval*1e3)
        xMin=self._confocallogic.xmin
        xMax=self._confocallogic.xmax
        yMin=self._confocallogic.ymin
        yMax=self._confocallogic.ymax
        self.image_x_padding=0.1e-6
        self.image_y_padding = 0.1e-6

        xy_viewbox = self.xy_image.getViewBox()

        xy_viewbox.setLimits(xMin=xMin - (xMax - xMin) * self.image_x_padding,
                                 xMax=xMax + (xMax - xMin) * self.image_x_padding,
                                 yMin=yMin - (yMax - yMin) * self.image_y_padding,
                                 yMax=yMax + (yMax - yMin) * self.image_y_padding)
        self.xy_resolution=300
        px_size = ((xMax - xMin) / (self.xy_resolution - 1),
                   (yMax - yMin) / (self.xy_resolution - 1))
        self.xy_image.set_image_extent(((xMin - px_size[0] / 2, xMax + px_size[0] / 2),
                                        (yMin - px_size[1] / 2, yMax + px_size[1] / 2)))

        # self.put_cursor_in_xy_scan()

        xy_viewbox.updateAutoRange()
        xy_viewbox.updateViewRange()
    def update_confocal_arb_plot(self, xy_image_arb_data):
        """
        H. Babashah - Updates the plot.
        """
        minval = np.min(xy_image_arb_data[np.nonzero(xy_image_arb_data)])
        maxval = np.max(xy_image_arb_data[np.nonzero(xy_image_arb_data)])
        self.xy_image_arb.setImage(image=xy_image_arb_data,levels=(minval, maxval))
        self.xy_cb_arb.refresh_colorbar(minval*1e3, maxval*1e3)
        xMin=self._confocallogic.xmin
        xMax=self._confocallogic.xmax
        yMin=self._confocallogic.ymin
        yMax=self._confocallogic.ymax
        self.image_x_padding=0.1e-6
        self.image_y_padding = 0.1e-6

        xy_viewbox = self.xy_image_arb.getViewBox()

        xy_viewbox.setLimits(xMin=xMin - (xMax - xMin) * self.image_x_padding,
                                 xMax=xMax + (xMax - xMin) * self.image_x_padding,
                                 yMin=yMin - (yMax - yMin) * self.image_y_padding,
                                 yMax=yMax + (yMax - yMin) * self.image_y_padding)
        self.xy_resolution=300
        px_size = ((xMax - xMin) / (self.xy_resolution - 1),
                   (yMax - yMin) / (self.xy_resolution - 1))
        self.xy_image_arb.set_image_extent(((xMin - px_size[0] / 2, xMax + px_size[0] / 2),
                                        (yMin - px_size[1] / 2, yMax + px_size[1] / 2)))

        # self.put_cursor_in_xy_scan()

        xy_viewbox.updateAutoRange()
        xy_viewbox.updateViewRange()
    def change_scope_param(self):
        """
        H. Babashah- Change the scope parameters
        """

        int_time = self._mw.int_time_doubleSpinBox.value()
        navg = self._mw.navg_doubleSpinBox.value()
        self.SigScopeParamChanged.emit(int_time,navg)

    def set_pulse(self):
        time_start = self._mw.time_start_doubleSpinBox.value()
        time_stop = self._mw.time_stop_doubleSpinBox.value()
        npts = self._mw.npts_doubleSpinBox.value()
        rabi_period = self._mw.rabi_period_doubleSpinBox.value()
        self.SigSetPulseChanged.emit(time_start,time_stop,npts,rabi_period)
    def show(self):
        """
        H.Babashah - Taken from Qudi - Make window visible and put it above all other windows.
        """
        self._mw.show()
        self._mw.activateWindow()
        self._mw.raise_()

    def change_navg(self):
        """
        H.Babashah - change the number of averages
        """

        navg = self._mw.navg_doubleSpinBox.value()
        self.SigNavgChanged.emit(navg)

    def change_pulse_analysis_param(self):
        """
        H.Babashah - change  pulse analy sis param
        """

        threshold = self._mw.threshold_doubleSpinBox.value()
        time_reference = self._mw.time_reference_doubleSpinBox.value()
        time_reference_start = self._mw.time_reference_start_doubleSpinBox.value()
        time_signal = self._mw.time_signal_doubleSpinBox.value()
        time_signal_start = self._mw.time_signal_start_doubleSpinBox.value()
        self.SigPulseAnalysisChanged.emit(threshold,time_reference,time_signal,time_reference_start,time_signal_start)

