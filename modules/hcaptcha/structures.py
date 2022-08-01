import time
import math

class FakeTime:
    def __init__(self):
        self.delta = 0
        self.epoch = time.time()
    
    def sleep(self, s):
        self.delta += s
    
    def time(self):
        t = self.epoch # time.time()
        t += round(self.delta, 5)
        return t

    def ms_sleep(self, s):
        self.sleep(s / 1000)
    
    def ms_time(self):
        t = self.time()
        t = int(t * 1000)
        return t

# the class structures below are pretty much direct ports of hcaptcha objects
class Pe:
    def __init__(self, time):
        self._manifest = {}
        self._time = time
        self.state = {
            "time_buffers": {},
            "load_time": self._time.ms_time()
        }

    def time(self):
        return self.state["load_time"]
    
    def record(self):
        self._manifest["st"] = self._time.ms_time()

    def get_data(self):
        for key in self.state["time_buffers"]:
            self._manifest[key] = self.state["time_buffers"][key].get_data()
            self._manifest[key + "-mp"] = self.state["time_buffers"][key].get_mean_period()
        return self._manifest
    
    def set_data(self, key, value):
        self._manifest[key] = value

    def reset_data(self):
        self._manifest = {}
        self.state["time_buffers"] = {}

    def record_event(self, e, t):
        n = t[len(t) - 1]
        if not e in self.state["time_buffers"]:
            self.state["time_buffers"][e] = Ie(16, 15e3, self._time)
        self.state["time_buffers"][e].push(n, t)

    def circ_buff_push(self, e, t):
        self.record_event(e, t)

class Ie:
    def __init__(self, period, interval, time):
        self._period = period
        self._interval = interval
        self._date = []
        self._data = []
        self._prev_timestamp = 0
        self._mean_period = 0
        self._mean_counter = 0
        self._time = time

    def get_mean_period(self):
        return self._mean_period
    
    def get_data(self):
        self._clean_stale_data()
        return self._data
    
    def get_size(self):
        self._clean_stale_data()
        return len(self._data)
    
    def get_capacity(self):
        return self._interval if 0 == self._period \
               else math.ceil(self._interval / self._period)
    
    def push(self, e, t):
        self._clean_stale_data()
        n = 0 == len(self._data)

        if e - (self._date[len(self._date) - 1] if self._date else 0) >= self._period:
            self._date.append(e)
            self._data.append(t)
            if not n:
                i = e - self._prev_timestamp
                self._mean_period = (self._mean_period * self._mean_counter + i) / (self._mean_counter + 1)
                self._mean_counter += 1
        self._prev_timestamp = e
    
    def _clean_stale_data(self):
        e = self._time.ms_time()
        t = len(self._date) - 1

        while t >= 0:
            if e - self._date[t] >= self._interval:
                self._date = self._date[:t + 1]
                self._data = self._data[:t + 1]
                break
            t -= 1