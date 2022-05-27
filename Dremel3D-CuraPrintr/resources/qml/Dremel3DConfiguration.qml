import QtQuick 2.7
import QtQuick.Controls 2.3
import QtQuick.Layouts 1.1
import QtQuick.Window 2.1

import UM 1.3 as UM
import Cura 1.1 as Cura


Cura.MachineAction
{
    id: base;

    property var finished: manager.finished
    onFinishedChanged: if(manager.finished) {completed()}

    function reset()
    {
        manager.reset()
    }

    anchors.fill: parent;
    property var selectedInstance: null

    property bool validUrl: true;
    property bool validTrans: true;

    Component.onCompleted: {
        actionDialog.minimumWidth = screenScaleFactor * 580;
        actionDialog.minimumHeight = screenScaleFactor * 370;
        actionDialog.maximumWidth = screenScaleFactor * 580;
        actionDialog.maximumHeight = screenScaleFactor * 370;
    }

    Column {
        anchors.fill: parent;

        Item { width: parent.width; }
        Label { text: catalog.i18nc("@label", "Dremel3D Address (URL)"); }
        TextField {
            id: urlField;
            text: manager.printerSettingUrl;
            maximumLength: 1024;
            anchors.left: parent.left;
            anchors.right: parent.right;
            onTextChanged: {
                base.validUrl = manager.validUrl(urlField.text);
            }
        }

        Item { width: parent.width; }
        Label {
            visible: !base.validUrl;
            text: catalog.i18nc("@error", "URL not valid. Example: http://192.168.1.2/");
            color: "red";
        }

        Item {
            width: saveButton.implicitWidth;
            height: saveButton.implicitHeight;
        }

        RowLayout {
            Button {
                id: saveButton;
                text: catalog.i18nc("@action:button", "Save Config");
                width: screenScaleFactor * 100;
                onClicked: {
                    manager.saveConfig(urlField.text);
                    actionDialog.reject();
                }
                enabled: base.validUrl & base.validTrans;
            }

            Button {
                id: deleteButton;
                text: catalog.i18nc("@action:button", "Remove Config");
                width: screenScaleFactor * 100;
                onClicked: {
                    manager.deleteConfig();
                    actionDialog.reject();
                }
            }
        }
    }
}
