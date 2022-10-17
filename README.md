# qudi LQNO

This is the qudi LQNO based on ulm-qudi platform. It is mostly focused to perform ultrafast pulsed experiment using national instrument card. In addition to Qudi-ulm it consists the following features. 

## Added Features

  * Photodetector acquisition with oscilloscope
  * Faster analog and digital DAQ acquisition
  * Analog acquisition with DAQ for pulsed measurements
  * Digital acquisition with DAQ for pulsed measurements
  * Photon counting with DAQ
  * Pulse extraction improved
  * ODMR with arbitrary/random microwave sweep
  * ODMR acquisition with spectrometer
  * Lock-in detection
  * New pulse sequences introduced 
  
# Technical

Qudi is made of different modules that are loaded and connected together by a manager component. The modules responsible for experiment control are divided into three
categories: GUI (graphical user interface), logic, and hardware. To define an experiment all the set of modules should be defined and mention in the config file.
Detail technical description on the connectio and synchronization can be found in paper [Optically detected magnetic resonance with an open source platform](https://arxiv.org/pdf/2205.00005.pdf) 

## Citation

As a good scientific practice the two papers should be cited [Optically detected magnetic resonance with an open source platform](https://arxiv.org/pdf/2205.00005.pdf) 
, [Qudi: A modular python suite for experiment control and data processing](http://doi.org/10.1016/j.softx.2017.02.001) for this purpose.

## License

The licence related to the Qudi is GPLv3 and everything about their licence can be found in their main repository as qudi-ulm.

## Installation
Pycharm is used as the python IDE.

Use the yml file corresponding to your operating system inside the tools folder to install the dependencies. You can do it as follows when you are inside the folder:

```
conda env create -f conda-env-OS-xxbit.yml
```

or you can either use requirement.txt file to install dependencies.

'''
pip install requirements.txt
'''
