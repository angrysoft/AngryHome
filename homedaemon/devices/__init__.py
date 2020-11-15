from __future__ import annotations
import importlib
from os import DirEntry, scandir
from homedaemon.config import Config
from homedaemon.logger import Logger
from homedaemon.bus import Bus
import json
from typing import Iterator, List, Dict, Any, Optional

class DriverInterface:
    pass

class Drivers:
    def __init__(self) -> None:
        self.drivers_modules: Dict[str, object] = {}
    
    def is_module_loaded(self, driver_module:str) -> bool:
        return driver_module in self.drivers_modules

    def get_driver(self, driver_module:str, driver_class:str):
        if not hasattr(self.drivers_modules[driver_module], driver_class):
            print(f'class not found {driver_class}')
        return getattr(self.drivers_modules[driver_module], driver_class)

    def load_driver_module(self, driver_module:str) -> None:
        # try:
        drv_mod = importlib.import_module(driver_module)
        self.drivers_modules[driver_module] = drv_mod
        # except ModuleNotFoundError as err:
        #     print(f'module not fond {err}')
        
        
class Devices:
    _instance = object = None
    
    def __new__(cls):
        if Devices._instance is None:
            cls.drivers: Drivers = Drivers()
            cls._devices: Dict[str, Drivers] = {}
            cls._gateways: Dict[str, Drivers] = {}
            cls._devices_info_list: Dict[str,Dict[str,Any]] = {}
            cls._scenes_info_list: Dict[str,Dict[str,Any]] = {}
            cls.config = Config()
            cls.logger = Logger()
            cls.bus = Bus()
            
            if cls.config['scenes']:
                importlib.sys.path.append(cls.config['scenes']['path'])
            
            Devices._instance = object.__new__(cls)
        return cls._instance
    
    def register_devices(self) -> None:
        self.load_devices_info()
        while self._devices_info_list:
            sid, device_info = self._devices_info_list.popitem()
            self.logger.debug(f"Loading..{len(self._devices_info_list)}..{sid} : {device_info.get('name')} from {device_info.get('place')}")
            self.register_dev(sid, device_info)
        
        while self._scenes_info_list:
            sid, device_info = self._scenes_info_list.popitem()
            self.logger.debug(f"Loading..{len(self._scenes_info_list)}..{sid} : {device_info.get('name')} from {device_info.get('place')}")
            self.register_scene(sid, device_info)
        
    def load_devices_info(self) -> None:
        try:
            _dir: Iterator[DirEntry[str]] = scandir(path=self.config.get('devices_dir'))
            for _file in _dir:
                if _file.is_file and _file.name.endswith('.json'):
                    with open(_file.path) as dev_file:
                        device_info = json.load(dev_file)
                        if self._check_device_info(device_info):
                            self._devices_info_list[device_info['sid']] = device_info
                        elif device_info.get('type', '') == 'scene':
                            self._scenes_info_list[device_info['sid']] = device_info     
        except FileNotFoundError as fnf:
            self.logger.error(f'Get devices list {fnf}')
        except NotADirectoryError as nd:
            self.logger.error(f'Get devices list {nd}')
        
    def register_dev(self, sid:str, device_info: Dict[str, Any]):
            
            driver_info: Dict[str,str] = device_info['driver']
            if not self.drivers.is_module_loaded(driver_info['module']):
                self.drivers.load_driver_module(driver_info['module'])
            
            device_info['args']['sid'] = sid
            
            if 'gateway' in driver_info:
                if driver_info['gateway'] not in self._gateways:
                    _gateway_info = self._devices_info_list.pop(driver_info['gateway'])
                    self.register_dev(driver_info['gateway'], _gateway_info)
                device_info['args']['gateway'] = self._gateways[driver_info['gateway']]
            
            driver = self.drivers.get_driver(driver_info['module'], driver_info['class'])
            
            dev = driver(**device_info['args'])
            
            if device_info.get('type') == 'gateway':
                self._gateways[sid] = dev
                return
            
            dev.status.name = device_info['name']
            dev.status.place = device_info['place']
            dev.watcher.add_report_handler(self.bus.emit_cmd)
            self.bus.add_trigger(f'execute.{sid}.*.*', dev.execute)
            self._devices[sid] = dev
    
    def register_scene(self, sid:str, device_info: Dict[str, Any]):
        try:
            _scene_module = importlib.import_module(sid)
            _scene = _scene_module.Scene(sid)
            self._devices[sid] = _scene
        except ModuleNotFoundError as err:
            self.logger.error(str(err))
    
    def _check_device_info(self, device_info: Dict[str,str]) -> bool:
        # TODO: check value is not empty
        return {'sid', 'driver', 'name', 'place', 'args'}.issubset(device_info)      
    
    def get(self, key:str, ret: Optional[Any]=None):
        try:
            return self._devices[key]
        except KeyError:
            return ret
    
    def get_devices_info_list(self) -> List[Dict[str,str]]:
        ret: List[Dict[str,str]] = list()
        for devitem in self._devices:
            dev = self.get(devitem)
            ret.append(dev.device_status())
        return ret
    
    def __contains__(self, key: str):
        return key in self._devices
    
    def __getitem__(self, key: str):
        return self._devices[key]


