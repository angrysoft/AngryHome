from aquara import GatewayWatcher
from homedaemon.inputs import BaseInput


class Input(BaseInput):
    def __init__(self, queue):
        super(Input, self).__init__()
        self.name = 'AquaraGateway'
        self.gw = GatewayWatcher(queue, loop=self.loop)
        self.loop.run_until_complete(self.gw.listen())

    def stop(self):
        pass
        # self.loop.stop()
        # print('stop loop')
        # self.gw.transport.close()
        # print('transport close')
        # self.loop.close()
        # print(f'{self.name} stops')

