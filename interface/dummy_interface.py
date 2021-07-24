from core.interface import abstract_interface_method
from core.meta import InterfaceMetaclass


class dummy_interface(metaclass=InterfaceMetaclass):
    """
    H.Babashah - This is the Interface class for dummy hardware. All the functions here must be defined in the hardware
    """
    pass
