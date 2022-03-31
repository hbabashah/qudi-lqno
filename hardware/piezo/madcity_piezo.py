import pyvisa
from interface.dummy_interface import dummy_interface

import os
import time
import numpy as np
import atexit

import scipy.interpolate
from fnmatch import fnmatch
from collections import OrderedDict
from abc import abstractmethod
import re
from ctypes import cdll, c_int, c_uint, c_double

from core.module import Base
from core.configoption import ConfigOption
from interface.pulser_interface import PulserInterface, PulserConstraints, SequenceOption
from core.util.modules import get_home_dir

class Mpiezo(Base, dummy_interface):
    """
    H.Babashah - Hardware code for Madcity piezo controlled used code from Madcitylab.
    """

    def __init__(self, config, **kwargs):
        super().__init__(config=config, **kwargs)

    def on_activate(self):
        """
        H.Babashah - Inspired from Qudi - Initialisation performed during activation of the module.
        """
        path_to_dll = 'Madlib.dll' # fix me hardware/piezo/
        #print('pathing to dll')
        self.madlib = cdll.LoadLibrary(path_to_dll)
        self.handler = self.mcl_start()
        atexit.register(self.mcl_close)

    def on_deactivate(self):
        """
        H.Babashah - Inspired from Qudi - Required tasks to be performed during deactivation of the module.
        """

        mcl_release_all = self.madlib['MCL_ReleaseAllHandles']
        mcl_release_all()
    def mcl_start(self):
        """
        Requests control of a single Mad City Labs Nano-Drive.

        Return Value:
            Returns a valid handle or returns 0 to indicate failure.
        """
        mcl_init_handle = self.madlib['MCL_InitHandle']

        mcl_init_handle.restype = c_int
        handler = mcl_init_handle()
        if (handler == 0):
            print("MCL init error")
            return -1
        return handler

    def mcl_read(self, axis_number):
        """
        Read the current position of the specified axis.

        Parameters:
            axis [IN] Which axis to move. (X=1,Y=2,Z=3,AUX=4)
            handle [IN] Specifies which Nano-Drive to communicate with.
        Return Value:
            Returns a position value or the appropriate error code.
        """
        mcl_single_read_n = self.madlib['MCL_SingleReadN']
        mcl_single_read_n.restype = c_double
        return mcl_single_read_n(c_uint(axis_number), c_int(self.handler))

    def mcl_write(self, position, axis_number):
        """
        Commands the Nano-Drive to move the specified axis to a position.

        Parameters:
            position [IN] Commanded position in microns.
            axis [IN] Which axis to move. (X=1,Y=2,Z=3,AUX=4)
            handle [IN] Specifies which Nano-Drive to communicate with.
        Return Value:
            Returns MCL_SUCCESS or the appropriate error code.
        """
        mcl_single_write_n = self.madlib['MCL_SingleWriteN']
        mcl_single_write_n.restype = c_int
        error_code = mcl_single_write_n(c_double(position), c_uint(axis_number), c_int(self.handler))

        if (error_code != 0):
            print("MCL write error = ", error_code)
        return error_code

    def gox(self, x_position):
        self.mcl_write(x_position, 1)
    def goy(self,y_position):
        self.mcl_write(y_position, 2)
    def goz(self, z_position):
        self.mcl_write(z_position, 3)
    def get_position(self):
        return self.mcl_read(1), self.mcl_read(2), self.mcl_read(3)

    def mcl_close(self):
        """
        Releases control of all Nano-Drives controlled by this instance of the DLL.
        """
        mcl_release_all = self.madlib['MCL_ReleaseAllHandles']
        mcl_release_all()