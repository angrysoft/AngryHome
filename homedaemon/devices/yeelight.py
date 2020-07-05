from .base import Dummy
from pyiot.xiaomi.yeelight import DeskLamp, Bslamp1, Color, YeelightError

class Driver:
    def __new__(cls, model, sid, config, daemon):
        try:
            dev = {'color': Color,
                   'bslamp1': Bslamp1,
                   'desklamp': DeskLamp}.get(model, Dummy)(sid)
            daemon.bus.add_trigger(f'write.{dev.sid}.*.*', dev.write)
            dev.watcher.add_report_handler(daemon.bus.emit_cmd)
            return dev
        except YeelightError as err:
            daemon.logger.error(f'Error {err}')