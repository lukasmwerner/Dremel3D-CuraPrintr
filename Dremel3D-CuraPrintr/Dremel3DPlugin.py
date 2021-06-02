from cura.CuraApplication import CuraApplication

from UM.Logger import Logger
from UM.Extension import Extension
from UM.OutputDevice.OutputDevicePlugin import OutputDevicePlugin

from .Dremel3DOutputDevice import Dremel3DConfigureOutputDevice, Dremel3DOutputDevice
from .Dremel3DSettings import get_config, init_config, DREMEL3D_SETTINGS


class Dremel3DPlugin(Extension, OutputDevicePlugin):
    def __init__(self):
        super().__init__()
        self._application = CuraApplication.getInstance()
        self._application.globalContainerStackChanged.connect(
            self._checkDremel3DOutputDevices
        )
        init_config()

    def _checkDremel3DOutputDevices(self):
        global_container_stack = self._application.getGlobalContainerStack()
        if not global_container_stack:
            return

        manager = self.getOutputDeviceManager()
        # remove all Dremel3D output devices - the new stack might not need them or have a different config
        manager.removeOutputDevice("dremel3d-configure")
        manager.removeOutputDevice("dremel3d-upload")

        # check and load new output devices
        config = get_config()
        if config:
            Logger.log(
                "d",
                "Dremel3D is active for printer: id:{}, name:{}".format(
                    global_container_stack.getId(), global_container_stack.getName()
                ),
            )
            manager.addOutputDevice(Dremel3DOutputDevice(config))
        else:
            manager.addOutputDevice(Dremel3DConfigureOutputDevice())
            Logger.log(
                "d",
                "Dremel3D is not available for printer: id:{}, name:{}".format(
                    global_container_stack.getId(), global_container_stack.getName()
                ),
            )
