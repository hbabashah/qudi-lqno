# Test class using pytest

import os, sys

p = os.path.abspath('.')
sys.path.insert(1, p)

from hardware.simple_data_dummy import SimpleDummy
class TestSimpleDummy:
    """
    Main class to test simple dummy data generator
    """
    Channel=3

    def test_value_channel(self):
        '''
        Test if the channel number is correct
        '''
        assert self.Channel == SimpleDummy.getChannels(())

