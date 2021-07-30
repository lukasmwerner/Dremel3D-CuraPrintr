import base64
import json
import os.path
import urllib
from enum import Enum
from io import BytesIO, StringIO
from typing import cast

from cura.CuraApplication import CuraApplication

from PyQt5.QtCore import QByteArray, QObject, QUrl, QVariant
from PyQt5.QtGui import QDesktopServices
from PyQt5.QtNetwork import QHttpMultiPart, QHttpPart, QNetworkReply, QNetworkRequest

from UM.Application import Application
from UM.i18n import i18nCatalog
from UM.Logger import Logger
from UM.Mesh.MeshWriter import MeshWriter
from UM.Message import Message
from UM.OutputDevice import OutputDeviceError
from UM.OutputDevice.OutputDevice import OutputDevice
from UM.PluginRegistry import PluginRegistry

catalog = i18nCatalog("cura")


class OutputStage(Enum):
    ready = 0
    writing = 1


class Dremel3DConfigureOutputDevice(OutputDevice):
    def __init__(self) -> None:
        super().__init__("dremel3d-configure")
        self.setShortDescription("Dremel3D Plugin")
        self.setDescription("Configure Dremel3D...")
        self.setPriority(0)

    def requestWrite(self, node, fileName=None, *args, **kwargs):
        message = Message(
            "To configure your Dremel3D printer go to:\n→ Settings\n  → Printer\n    → Manage Printers\n     → select your printer\n    → click on 'Connect Dremel'",
            lifetime=0,
            title="Configure Dremel3D in Preferences!",
        )
        message.show()
        self.writeSuccess.emit(self)


class Dremel3DOutputDevice(OutputDevice):
    def __init__(self, config):
        self._name_id = "dremel3d-upload"
        super().__init__(self._name_id)

        self._url = config.get("url", "")

        self.application = CuraApplication.getInstance()
        global_container_stack = self.application.getGlobalContainerStack()
        self._name = global_container_stack.getName()

        description = catalog.i18nc("@action:button", "Start on {0}").format(
            self._name
        )
        self.setShortDescription(description)
        self.setDescription(description)

        self._stage = OutputStage.ready
        self._stream = None
        self._message = None

        Logger.log(
            "d",
            "New Dremel3DOutputDevice '{}' created | URL: {} ".format(
                self._name_id, self._url
            ),
        )
        self._resetState()

    def requestWrite(self, node, fileName=None, *args, **kwargs):
        if self._stage != OutputStage.ready:
            raise OutputDeviceError.DeviceBusyError()

        # Make sure post-processing plugin are run on the gcode
        self.writeStarted.emit(self)

        # The presliced print should always be send using `GCodeWriter`
        print_info = CuraApplication.getInstance().getPrintInformation()
        self._output_format = "gcode"
        code_writer = cast(
            MeshWriter, PluginRegistry.getInstance().getPluginObject("GCodeWriter")
        )
        self._stream = StringIO()

        if not code_writer.write(self._stream, None):
            Logger.log("e", "MeshWriter failed: %s" % code_writer.getInformation())
            return

        # Prepare filename for upload
        if fileName:
            fileName = os.path.basename(fileName)
        else:
            fileName = "%s." % Application.getInstance().getPrintInformation().jobName

        self._fileName = fileName + "." + self._output_format

        # Display upload dialog
        #path = os.path.join(
        #    os.path.dirname(os.path.abspath(__file__)),
        #    "resources",
        #    "qml",
        #    "Dremel3DUpload.qml",
        #)
        #self._dialog = CuraApplication.getInstance().createQmlComponent(
        #    path, {"manager": self}
        #)
        #self._dialog.textChanged.connect(self.onFilenameChanged)
        #self._dialog.accepted.connect(self.onFilenameAccepted)
        #self._dialog.show()
        #self._dialog.findChild(QObject, "nameField").setProperty("text", self._fileName)
        #self._dialog.findChild(QObject, "nameField").select(
        #    0, len(self._fileName) - len(self._output_format) - 1
        #)
        #self._dialog.findChild(QObject, "nameField").setProperty("focus", True)

        ## TODO: just upload directly here
        self._startPrint = True
        startUploading()

    def onFilenameChanged(self):
        fileName = self._dialog.findChild(QObject, "nameField").property("text").strip()
        fileName = self._dialog.findChild(QObject, "nameField").property("text").strip()

        forbidden_characters = '\/:*?"<>|'
        for forbidden_character in forbidden_characters:
            if forbidden_character in fileName:
                self._dialog.setProperty("validName", False)
                self._dialog.setProperty(
                    "validationError", "*cannot contain {}".format(forbidden_characters)
                )
                return

        if fileName == "." or fileName == "..":
            self._dialog.setProperty("validName", False)
            self._dialog.setProperty("validationError", '*cannot be "." or ".."')
            return

        self._dialog.setProperty("validName", len(fileName) > 0)
        self._dialog.setProperty("validationError", "Filename too short")

    def startUploading(self):
        #self._fileName = (
        #    self._dialog.findChild(QObject, "nameField").property("text").strip()
        #)
        #if (
        #    not self._fileName.endswith("." + self._output_format)
        #    and "." not in self._fileName
        #):
        #    self._fileName += "." + self._output_format
        #Logger.log("d", "Filename set to: " + self._fileName)

        #self._startPrint = self._dialog.findChild(QObject, "printField").property(
        #    "checked"
        #)
        #Logger.log("d", "Print set to: " + str(self._startPrint))

        #self._dialog.deleteLater()
        self._stage = OutputStage.writing

        # show a progress message
        self._message = Message(
            catalog.i18nc("@info:progress", "Uploading to {}...").format(self._name),
            0,
            False,
            -1,
        )
        self._message.show()
        Logger.log("d", "Connecting to Dremel...")
        self._sendRequest("", on_success=self.onInstanceOnline)

    def onInstanceOnline(self, reply):
        if self._stage != OutputStage.writing:
            return
        if reply.error() != QNetworkReply.NoError:
            Logger.log("d", "Stopping due to reply error: " + reply.error())
            return

        Logger.log("d", "Uploading " + self._output_format + "...")
        self._stream.seek(0)
        self._postData = QByteArray()
        if isinstance(self._stream, BytesIO):
            self._postData.append(self._stream.getvalue())
        else:
            self._postData.append(self._stream.getvalue().encode())
        self._sendRequest(
            "print_file_uploads",
            name=self._fileName,
            data=self._postData,
            on_success=self.onCodeUploaded,
        )

    def onCodeUploaded(self, reply):
        if self._stage != OutputStage.writing:
            return
        if reply.error() != QNetworkReply.NoError:
            Logger.log("d", "Stopping due to reply error: " + reply.error())
            return

        Logger.log("d", "Upload completed")
        self._stream.close()
        self._stream = None

        if self._startPrint and self._startPrint == True:

            data = QByteArray()
            data.append("PRINT={}".format(self._fileName))

            headers = {
                "User-Agent": "Mozilla/5.0",
                "Connection": "Keep-Alive",
            }

            req = QNetworkRequest(QUrl())
            req.setHeader(
                QNetworkRequest.ContentTypeHeader, "application/x-www-form-urlencoded"
            )
            self.application.getHttpRequestManager().post(
                self._url + "command",
                headers,
                data,
                callback=None,
                error_callback=self._onNetworkError,
            )

            self.writeSuccess.emit(self)
            self._resetState()
        else:
            self.writeSuccess.emit(self)
            self._resetState()

    def _onProgress(self, progress):
        if self._message:
            self._message.setProgress(progress)
        self.writeProgress.emit(self, progress)

    def _resetState(self):
        Logger.log("d", "Reset state")
        if self._stream:
            self._stream.close()
        self._stream = None
        self._stage = OutputStage.ready
        self._fileName = None
        self._startPrint = None
        self._postData = None

    def _onMessageActionTriggered(self, message, action):
        if action == "open_browser":
            QDesktopServices.openUrl(QUrl(self._url))
            if self._message:
                self._message.hide()
                self._message = None

    def _onUploadProgress(self, bytesSent, bytesTotal):
        if bytesTotal > 0:
            self._onProgress(int(bytesSent * 100 / bytesTotal))

    def _onNetworkError(self, reply, error):
        Logger.log("e", repr(error))
        if self._message:
            self._message.hide()
            self._message = None

        errorString = ""
        if reply:
            errorString = reply.errorString()

        message = Message(
            catalog.i18nc("@info:status", "There was a network error: {} {}").format(
                error, errorString
            ),
            0,
            False,
        )
        message.show()

        self.writeError.emit(self)
        self._resetState()

    def _sendRequest(self, path, name=None, data=None, on_success=None, on_error=None):
        url = self._url + path

        headers = {
            "User-Agent": "Mozilla/5.0",
            "Connection": "Keep-Alive",
        }

        if data:
            # Create multi_part request
            parts = QHttpMultiPart(QHttpMultiPart.FormDataType)

            part_file = QHttpPart()
            part_file.setHeader(
                QNetworkRequest.ContentDispositionHeader,
                QVariant('form-data; name="print_file"; filename="' + name + '"'),
            )
            part_file.setBody(data)
            parts.append(part_file)

            headers["Content-Type"] = "multipart/form-data; boundary=" + str(
                parts.boundary().data(), encoding="utf-8"
            )

            self.application.getHttpRequestManager().post(
                url,
                headers,
                parts,
                callback=on_success,
                error_callback=on_error if on_error else self._onNetworkError,
                upload_progress_callback=self._onUploadProgress,
            )
        else:
            self.application.getHttpRequestManager().get(
                url,
                headers,
                callback=on_success,
                error_callback=on_error if on_error else self._onNetworkError,
            )
