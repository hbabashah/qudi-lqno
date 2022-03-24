import numpy as np
import os
import pyqtgraph as pg

from core.connector import Connector

from gui.guibase import GUIBase

from qtpy import QtCore, QtWidgets, uic

from qtpy import uic


class fft_spectrum_MainWindow(QtWidgets.QMainWindow):
    """
    H. Babashah - class for using fft_spectrum gui
    """
    def __init__(self):
        # Get the path to the *.ui file
        this_dir = os.path.dirname(__file__)
        ui_file = os.path.join(this_dir, 'fft_spectrum.ui')

        # Load it
        super(fft_spectrum_MainWindow, self).__init__()
        uic.loadUi(ui_file, self)
        self.show()


class FFTGui(GUIBase):
    """
    H. Babashah - This is the GUI Class for FFT measurements.
    """

    # declare connectors
    fftlogic = Connector(interface='FFTLogic')
    savelogic = Connector(interface='SaveLogic')

    #Define Signals
    SigStartAcquisition = QtCore.Signal(bool)
    SigResolutionChanged = QtCore.Signal(float)
    SigSaveData = QtCore.Signal(str, str, str)

    def __init__(self, config, **kwargs):
        super().__init__(config=config, **kwargs)


    def on_activate(self):
        """
        H. Babashah - Definition, configuration and initialisation of the FFT GUI.

        This init connects all the graphic modules, which were created in the
        *.ui file and configures the event handling between the modules.
        """

        self._fft_logic = self.fftlogic()

        # Use the inherited class 'Ui_ODMRGuiUI' to create now the GUI element:
        self._mw = fft_spectrum_MainWindow()

        # Define data plots
        self.fft_image = pg.PlotDataItem()
        # Add the display item to the xy and xz ViewWidget, which was defined in the UI file.
        self._mw.fft_graph.addItem(self.fft_image)
        self._mw.fft_graph.setLabel(axis='left', text='FFT', units='V/rtHz')
        self._mw.fft_graph.setLabel(axis='bottom', text='Frequency', units='Hz')
        self._mw.fft_graph.showGrid(x=True, y=True, alpha=0.8)

        ########################################################################
        #                       Connect signals                                #
        ########################################################################
        # Internal user input changed signals
        self._mw.actionStart.triggered.connect(self.start_data_acquisition)
        self._mw.resolution_doubleSpinBox.editingFinished.connect(self.change_fft_resolution)
        self._mw.actionSave.triggered.connect(self.save_fft_data)
        self._mw.x_axis_comboBox.currentIndexChanged.connect(self.graph_scale)
        self._mw.y_axis_comboBox.currentIndexChanged.connect(self.graph_scale)


        # Connections to logic
        self._mw.fft_window_comboBox.currentTextChanged.connect(self._fft_logic.set_fft_window)
        self._mw.y_unit_comboBox.currentTextChanged.connect(self._fft_logic.set_fft_unit)
        self.SigStartAcquisition.connect(self._fft_logic.start_data_acquisition)
        self.SigResolutionChanged.connect(self._fft_logic.set_fft_resolution, QtCore.Qt.QueuedConnection)
        self._mw.resolution_doubleSpinBox.setValue(self._fft_logic.resolution)
        self.SigSaveData.connect(self._fft_logic.save_fft_data)

        # Update connections from logic
        self._fft_logic.SigDataUpdated.connect(self.update_plot, QtCore.Qt.QueuedConnection)



        # Show the Main FFT GUI:
        self.show()


    def on_deactivate(self):
        """
        H. Babashah - Reverse steps of activation

        @return int: error code (0:OK, -1:error)
        """
        # Disconnect signals
        self._mw.resolution_doubleSpinBox.editingFinished.disconnect()
        self._mw.fft_window_comboBox.currentTextChanged.disconnect()
        self.SigResolutionChanged.disconnect()
        self._mw.close()
        return 0


    def change_fft_resolution(self):
        """
        H. Babashah - Send the new resolution command to the logic.
        """
        resolution = self._mw.resolution_doubleSpinBox.value()
        self.SigResolutionChanged.emit(resolution)

    def start_data_acquisition(self):
        """
        H. Babashah - Send user order to start acquisition to the logic.
        """
        self.SigStartAcquisition.emit(self._mw.multi_span_checkBox.isChecked())

    def update_plot(self, xdata, ydata):
        """
        H. Babashah - Updates the plot.
        """

        self.fft_image.setData(xdata, ydata)

    def show(self):
        """
        H. Babashah - Taken from Qudi - Make window visible and put it above all other windows.
        """
        self._mw.show()
        self._mw.activateWindow()
        self._mw.raise_()

    def save_fft_data(self):
        self.project = self._mw.save_project_comboBox.currentText()
        self.module_name = self._mw.module_name_textEdit.toPlainText()
        self.file_tag = self._mw.file_tag_textEdit.toPlainText()
        self.description = self._mw.description_textEdit.toPlainText()

        self.SigSaveData.emit(self.project, self.module_name, self.file_tag)

    def graph_scale(self):
        
        self._mw.fft_graph.setLogMode(self._mw.x_axis_comboBox.currentIndex(), self._mw.y_axis_comboBox.currentIndex())
        
