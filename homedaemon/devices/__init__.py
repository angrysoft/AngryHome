from threading import RLock, Thread
import json


class Device:
    def __new__(cls, data, daemon):
        model = data.get('model')
        if model == 'ctrl_neutral1':
            from .aqaradevices import CtrlNeutral
            return CtrlNeutral(data, daemon)
        elif model == 'ctrl_neutral2':
            from .aqaradevices import CtrlNeutral2
            return CtrlNeutral2(data, daemon)
        elif model == '86sw1':
            return BaseDevice(data, daemon)
        elif model == '86sw2':
            return BaseDevice(data, daemon)
        elif model == 'sensor_ht':
            return BaseDevice(data, daemon)
        elif model == 'weather.v1':
            return BaseDevice(data, daemon)
        elif model == 'rgbw_light':
            return BaseDevice(data, daemon)
        elif model == 'magnet':
            return BaseDevice(data, daemon)
        elif model == 'motion':
            return BaseDevice(data, daemon)
        elif model == 'sensor_motion.aq2':
            from .aqaradevices import SensorMotionAq2
            return SensorMotionAq2(data, daemon)
        elif model == 'sensor_switch.aq2':
            from .aqaradevices import SensorSwitchAq2
            return SensorSwitchAq2(data, daemon)
        elif model == 'plug':
            from .aqaradevices import Plug
            return Plug(data, daemon)
        elif model == 'switch':
            return BaseDevice(data, daemon)
        elif model == 'gateway':
            from .aqaradevices import AqaraGateway
            return AqaraGateway(data, daemon)
        elif model == 'dallastemp':
            return BaseDevice(data, daemon)
        elif model == 'rgbstrip':
            from .rgbstrip import RgbStrip
            return RgbStrip(data, daemon)
        elif model == 'bravia':
            from .tv import BraviaTv
            return BraviaTv(data, daemon)
        elif model in ['color', 'bslamp1']:
            from .yeelightdevices import YeeligthDevice
            return YeeligthDevice(data, daemon)
        elif model == 'computer':
            from .computer import Computer
        elif model == 'timer':
            return TimerDev(data, daemon)
        else:
            raise ValueError(f'unrecognized device {model}')


class BaseDevice:
    def __init__(self, data, daemon):
        self.daemon = daemon
        self.model = data.get('model')
        self.name = data.get('name')
        self.sid = data.get('sid')
        self.device_data = daemon.device_data[self.sid]
        self.lock = RLock()
        self.cmds = {'write': self.write,
                     'report': self._report,
                     'heartbeat': self.heartbeat}
        

    def do(self, data):
        if 'data' in data:
            self.cmds.get(data.get('cmd'), self._unknown_cmd)(data)
        else:
            self.cmds.get(data.get('cmd'), self._unknown_cmd)()

    def _unknown_cmd(self, data):
        self.daemon.logger.error(f'Unknown command:  {data}')

    def write(self, data):
        pass

    def heartbeat(self, data):
        pass
    
    def _report(self, data):
        self.daemon.notify_clients(json.dumps(data))
        self.report(data)
        
    def report(self, data):
        self.update_dev_data(data.get('data'))

    def update_dev_data(self, data):
        with self.lock:
            self.daemon.device_data[self.sid] = data
    
    def get_value(self, value):
        if value in self.daemon.device_data[self.sid]:    
            return self.daemon.device_data[self.sid][value]
        else:
            return None


class ButtonOnOff:
    def __init__(self, name, write):
        self.name = name
        self.write = write

    def on(self):
        self.write({'data': {self.name: 'on'}})

    def off(self):
        self.write({'data': {self.name: 'off'}})
    
    def toggle(self):
        self.write({'data': {self.name: 'toggle'}})


class ButtonToggleOnOff(ButtonOnOff):

    def toggle(self):
        self.write({'data': {self.name: 'toggle'}})

class TimerDev(BaseDevice):
    def do(self, data):
        pass
    
    
    