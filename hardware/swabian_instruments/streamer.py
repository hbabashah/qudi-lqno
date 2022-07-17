import pyvisa
from interface.dummy_interface import dummy_interface

import os
import time
import numpy as np
import scipy.interpolate
from fnmatch import fnmatch
from collections import OrderedDict
from abc import abstractmethod
import re
from pulsestreamer import Sequence, OutputState
from pulsestreamer import PulseStreamer
from pulsestreamer import TriggerStart, TriggerRearm

from core.module import Base
from core.configoption import ConfigOption
from interface.pulser_interface import PulserInterface, PulserConstraints, SequenceOption
from core.util.modules import get_home_dir

class Streamer(Base, dummy_interface):
    """
    H.Babashah - Hardware code for Swabian Pulse streamer.
    """
    _instrument_ip = ConfigOption(name='instrument_ip', default='192.168.2.153', missing='warn')
    _Laser_channel = ConfigOption(name='laser_channel', default='6', missing='info')
    _scope_channel = ConfigOption(name='scope_channel', default='0', missing='info')
    _MW_trigger_channel = ConfigOption(name='MW_trigger_channel', default='2', missing='info')
    _switch_channel = ConfigOption(name='switch_channel', default='1', missing='info')
    _analogx_channel = ConfigOption(name='analogx_channel', default='0', missing='info')
    _analogy_channel = ConfigOption(name='analogy_channel', default='1', missing='info')

    def __init__(self, config, **kwargs):
        super().__init__(config=config, **kwargs)

    def on_activate(self):
        """
        H.Babashah - Inspired from Qudi - Initialisation performed during activation of the module.
        """


        # import enum types

        # import class Sequence and OutputState for advanced sequence building
        self.pulser = PulseStreamer(self._instrument_ip)

    def on_deactivate(self):
        """
        H.Babashah - Inspired from Qudi - Required tasks to be performed during deactivation of the module.
        """


    def get_acquisition(self):
        """
        H. Babashah - get acquisition.
        """

        return np.linspace(1,100,300), np.random.rand(300)

    def set_ODMR(self,SweepStep,Npts):
        LaserCh = int(self._Laser_channel)
        OscopeCh = int(self._scope_channel)
        MWChTrig = int(self._MW_trigger_channel)
        SwitchCh = int(self._switch_channel)
        # MW channel is one
        # define digital levels
        HIGH = 1
        LOW = 0
        NumberOfrepeats = 3000
        SweepTime = Npts * SweepStep + 4 * SweepStep;
        Lowtime = 200e-6;  # Level sensitive
        LaserChseq = [(SweepTime * 1e9, HIGH)] * NumberOfrepeats  # 0
        OscopeTirgChseq = [((SweepTime - Lowtime) * 1e9, HIGH), (Lowtime * 1e9, LOW)] * NumberOfrepeats  # 0
        MWChTrigseq = [((SweepTime - Lowtime) * 1e9, HIGH), (Lowtime * 1e9, LOW)] * NumberOfrepeats  # 0
        SwitchChseq = [(SweepTime * 1e9, HIGH)] * NumberOfrepeats  #

        self.seq = Sequence()

        # set digital channels
        print(LaserCh,OscopeCh,MWChTrig,SwitchCh)
        self.seq.setDigital(LaserCh, LaserChseq)
        self.seq.setDigital(OscopeCh, OscopeTirgChseq)
        self.seq.setDigital(MWChTrig, MWChTrigseq)
        self.seq.setDigital(SwitchCh, SwitchChseq)




        # reset the device - all outputs 0V
        self.pulser.reset()

        # set constant state of the device
        self.pulser.constant(OutputState.ZERO())  # all outputs 0V

        # define the final state of the Pulsestreamer - the device will enter this state when the sequence is finished
        self.final = OutputState.ZERO()

        self.start = TriggerStart.IMMEDIATE
        self.rearm = TriggerRearm.MANUAL

        self.pulser.setTrigger(start=self.start, rearm=self.rearm)
        print('ODMR is set')


    def set_confocal(self,Xvalue,Yvalue):
        V2C_coef = 0.1 * 1e6  # It should be calibrated based on the acquired image
        LaserCh = int(self._Laser_channel)
        AnalogXCh = int(self.analogx_channel)
        AnalogYCh = int(self.analogy_channel)
        OscopeCh = int(self._scope_channel)

        HIGH = 1
        LOW = 0
        NumberOfrepeats = 100
        dtime = 1e-3;
        Lowtime = 200e-6;  # Level sensitive
        LaserChseq = [(dtime * 1e9, HIGH)] * NumberOfrepeats  # 0
        AnalogXChseq = [(dtime * 1e9, Xvalue*V2C_coef)] * NumberOfrepeats
        AnalogYChseq = [(dtime * 1e9, Yvalue*V2C_coef)] * NumberOfrepeats
        OscopeTirgChseq = [((dtime - Lowtime) * 1e9, HIGH), (Lowtime * 1e9, LOW)] * NumberOfrepeats  # 0
        self.seq = Sequence()

        # set digital channels
        self.seq.setDigital(LaserCh, LaserChseq)
        self.seq.setAnalog(AnalogXCh, AnalogXChseq)
        self.seq.setAnalog(AnalogYCh, AnalogYChseq)
        self.seq.setDigital(OscopeCh, OscopeTirgChseq)


        # reset the device - all outputs 0V
        self.pulser.reset()

        # set constant state of the device
        self.pulser.constant(OutputState.ZERO())  # all outputs 0V

        # define the final state of the Pulsestreamer - the device will enter this state when the sequence is finished
        self.final = OutputState.ZERO()

        self.start = TriggerStart.IMMEDIATE
        self.rearm = TriggerRearm.MANUAL

        self.pulser.setTrigger(start=self.start, rearm=self.rearm)

    def set_pulse_measurement(self,Laser_length, Variable,pulsetype,rabi_period):
        """ Set pulse measurement parameters
        :param float Laser_length: Length of Laser in s
        :param float Variable: Length of changing varibale
        :param string pulsetype: Type of pulse measurement
        :param float rabi_period: Rabi period in s
        :return:
        """
        wl = Laser_length  # LaserPulseWidth in second

        LaserCh = int(self._Laser_channel)
        OscopeCh = int(self._scope_channel)
        MWCh = int(self._switch_channel) # switch channel for MW
        # define digital levels
        HIGH = 1
        LOW = 0
        NumberOfrepeats = 3000
        # Set pulse measurement type
        if pulsetype == 'T1':
            LaserChseq = [(wl * 1e9, HIGH), (Variable * 1e9, LOW)] * NumberOfrepeats  # 0
            OscopeTirgChseq = [(wl * 1e9, HIGH), (Variable * 1e9, LOW)] * NumberOfrepeats  # 0
            print('T1')
            # MWChseq = [(wl*1e9+Variable*1e9, LOW)]*NumberOfrepeats #0

        self.seq = Sequence()

        if pulsetype == 'Rabi':
            tau = 100e-6
            LaserChseq = [(wl * 1e9, HIGH), (tau * 1e9, LOW)] * NumberOfrepeats  # 0
            OscopeTirgChseq = [(wl * 1e9, HIGH), (tau * 1e9, LOW)] * NumberOfrepeats  # 0
            MWChseq = [(wl * 1e9 + tau * 1e9 / 2 - Variable * 1e9 / 2, LOW), (Variable * 1e9, HIGH),
                       (tau * 1e9 / 2 - Variable * 1e9 / 2, LOW)] * NumberOfrepeats  #
            self.seq.setDigital(MWCh, MWChseq)

        if pulsetype == 'Ramsey':
            pihalf = rabi_period/4;
            tau = 100e-6
            LaserChseq = [(wl * 1e9, HIGH), (tau * 1e9, LOW)] * NumberOfrepeats  # 0
            OscopeTirgChseq = [(wl * 1e9, HIGH), (tau * 1e9, LOW)] * NumberOfrepeats  # 0
            MWChseq = [(wl * 1e9 + tau * 1e9 / 2 - Variable * 1e9 / 2 - pihalf * 1e9, LOW), (pihalf * 1e9, HIGH),
                       (Variable * 1e9, LOW), (pihalf * 1e9, HIGH),
                       (tau * 1e9 / 2 - Variable * 1e9 / 2 - pihalf*1e9, LOW)] * NumberOfrepeats  # 0
            self.seq.setDigital(MWCh, MWChseq)


        if pulsetype == 'Hahn_echo':
            piPulse = rabi_period/2;  # 235 orginal
            pihalf = rabi_period / 4;
            tau = 100e-6
            LaserChseq = [(wl * 1e9, HIGH), (tau * 1e9, LOW)] * NumberOfrepeats  # 0
            OscopeTirgChseq = [(wl * 1e9, HIGH), (tau * 1e9, LOW)] * NumberOfrepeats  # 0
            MWChseq = [(wl * 1e9 + tau * 1e9 / 2 - piPulse * 1e9 - Variable * 1e9 / 2, LOW), (pihalf * 1e9, HIGH),
                       (Variable * 1e9 / 2, LOW), (piPulse * 1e9, HIGH), (Variable * 1e9 / 2, LOW),
                       (pihalf * 1e9, HIGH),
                       (tau * 1e9 / 2 - 2 * Variable * 1e9 / 2 - 2 * piPulse * 1e9, LOW)] * NumberOfrepeats  # 0
            self.seq.setDigital(MWCh, MWChseq)

        # set digital channels
        self.seq.setDigital(LaserCh, LaserChseq)
        self.seq.setDigital(OscopeCh, OscopeTirgChseq)
        # reset the device - all outputs 0V
        self.pulser.reset()

        # set constant state of the device
        self.pulser.constant(OutputState.ZERO())  # all outputs 0V

        # define the final state of the Pulsestreamer - the device will enter this state when the sequence is finished
        self.final = OutputState.ZERO()

        self.start = TriggerStart.IMMEDIATE
        self.rearm = TriggerRearm.MANUAL

        self.pulser.setTrigger(start=self.start, rearm=self.rearm)
        self.log.info('Pulse streamer is prepared for\n{0}'.format(pulsetype))

    def start_stream(self):
        # run the sequence only once

        self.n_runs = 100000
        # n_runs = 'INFIITE' # repeat the sequence all the time
        # Start Streaming
        try:
            self.pulser.stream(self.seq, self.n_runs, self.final)
        except:
            print('Streaming failed Ip error.. tyring again :D')
            time.sleep(0.2)
            self.start_stream()
    def set_parameter(self,parameter):
        """
        H. Babashah - get acquisition.
        """
        print(parameter)