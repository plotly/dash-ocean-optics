import seabreeze.spectrometers as sb
from threading import Lock
import random
import numpy


class DashOceanOpticsSpectrometer:

    def __init__(self, specLock, commLock):
        self.spec = None
        self.specmodel = ''
        self.lightSources = []
        self.spectralData = [[], []]
        self.controlFunctions = {}
        self.int_time_max = 650000000
        self.int_time_min = 1000
        self.comm_lock = commLock
        self.spec_lock = specLock
        
    def get_spectrum(self):
        return [[], []]

    def assign_spec(self):
        return
    

class PhysicalSpectrometer(DashOceanOpticsSpectrometer):
    
    def __init__(self, specLock, commLock):
        super().__init__(specLock, commLock)
        self.assign_spec()
        self.controlFunctions = {
            'int_time': "spec.spec.integration_time_micros",
            'nscans_avg': "spec.spec.scans_to_average",
            'strobe_enable': "spec.spec.continuous_strobe_set_enable",
            'strobe_period': "spec.spec.continuous_strobe_set_period_micros",
            'light_sources': "empty_control_demo"
        }
        
    def get_spectrum(self):
        if self.spec is None:
            try:
                self.spec_lock.acquire()
                self.assign_spec()
            except Exception:
                pass
            finally:
                self.spec_lock.release()
        try:
            self.comm_lock.acquire()
            self.spectralData = self.spec.spectrum(correct_dark_counts=True,
                                                   correct_nonlinearity=True)
        except Exception:
            pass
        finally:
            self.comm_lock.release()

        return self.spectralData
            
    def assign_spec(self):
        try:
            self.comm_lock.acquire()
            devices = sb.list_devices()
            self.spec = sb.Spectrometer(devices[0])
            self.specmodel = self.spec.model
            self.lightSources = [{'label': ls.__repr__(), 'value': ls}
                                 for ls in list(self.spec.light_sources)]
            self.int_time_min = self.spec.minimum_integration_time_micros()
        except Exception:
            pass
        finally:
            self.comm_lock.release()
        

class DemoSpectrometer(DashOceanOpticsSpectrometer):

    def __init__(self, specLock, commLock):
        super().__init__(specLock, commLock)
        self.assign_spec()
        self.int_time_demo_lock = Lock()
        self.controlFunctions = {
            'int_time': "spec.integration_time_demo",
            'nscans_avg': "spec.empty_control_demo",
            'strobe_enable': "spec.empty_control_demo",
            'strobe_period': "spec.empty_control_demo",
            'light_sources': "spec.exception_demo"
        }

    def get_spectrum(self, int_time_demo_val=1000):
        self.spectralData[0] = numpy.linspace(400, 900, 5000)
        scale = self.int_time_min
        try:
            self.int_time_demo_lock.acquire()
            scale = int_time_demo_val
        except Exception:
            pass
        finally:
            self.int_time_demo_lock.release()
        self.spectralData[1] = [self.sample_spectrum(wl, scale)
                                for wl in self.spectralData[0]]

        return self.spectralData
        
    def assign_spec(self):
        self.specmodel = "USB2000+"
        self.lightSources = [{'label': 'Lamp 1 at 127.0.0.1', 'value': 'l1'},
                             {'label': 'Lamp 2 at 127.0.0.1', 'value': 'l2'}]
        
    def sample_spectrum(self, x, a):
        return (a * (numpy.e**(-1 * ((x-500) / 5)**2) +
                     0.01 * random.random()))

    # demo functions
    def integration_time_demo(self, x):
        return
        
    def empty_control_demo(self, _):
        return

    def exception_demo(self, x):
        if(x == "l1"):
            raise Exception("Lamp not found.")
        else:
            return
