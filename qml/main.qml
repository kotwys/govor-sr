import QtQuick
import QtQuick.Controls
import QtQuick.Layouts
import QtQuick.Dialogs
import QtMultimedia

ApplicationWindow {
    visible: true
    width: 760
    height: 560
    minimumWidth: 400
    minimumHeight: 300
    title: "Говор"

    onClosing: (close) => {
        backend.onAppClose();
    }

    FileDialog {
        id: fileDialog
        title: "Выберите WAV-файл"
        nameFilters: ["WAV-файлы (*.wav)"]
        onAccepted: {
            backend.selectFile(selectedFile)
        }
    }

    MediaPlayer {
        id: player
        audioOutput: AudioOutput {}
        source: backend.selectedFile
            ? "file://" + backend.selectedFile
            : ""
    }

    MessageDialog {
        id: errorDialog
        buttons: MessageDialog.Ok
        title: "Ошибка"
    }

    Connections {
        target: backend
        function onError(msg) {
            errorDialog.text = msg;
            errorDialog.open();
        }
    }

    ColumnLayout {
        anchors.fill: parent
        anchors.margins: 16
        spacing: 12

        Label {
            text: "Распознавание диалектной речи"
            font.bold: true
            font.pointSize: 15
        }

        RowLayout {
            Layout.fillWidth: true
            spacing: 8

            TextField {
                Layout.fillWidth: true
                readOnly: true
                text: backend.selectedFile
                placeholderText: "Выберите файл аудиозаписи"
            }

            Button {
                text: "Выбрать..."
                onClicked: fileDialog.open()
            }
        }

        RowLayout {
            enabled: backend.selectedFile !== ""
            spacing: 10

            Button {
                icon.name: player.playbackState === MediaPlayer.PlayingState
                           ? "media-playback-pause"
                           : "media-playback-start"
                onClicked: {
                    if (player.playbackState === MediaPlayer.PlayingState) {
                        player.pause();
                    } else {
                        player.play();
                    }
                }
            }

            Slider {
                Layout.fillWidth: true
                from: 0
                to: player.duration
                value: player.position
                onMoved: player.position = value
            }
        }

        Item {
            Layout.fillWidth: true
            Layout.preferredHeight: 32

            Button {
                anchors.fill: parent
                text: "Распознать"
                enabled: backend.selectedFile !== "" && !backend.isBusy
                visible: !backend.isBusy
                onClicked: backend.startRecognition()
            }

            ProgressBar {
                anchors.fill: parent
                indeterminate: true
                visible: backend.isBusy
            }
        }

        TextArea {
            Layout.fillWidth: true
            Layout.fillHeight: true
            wrapMode: TextArea.Wrap
            readOnly: backend.isBusy
            text: backend.resultText
        }
    }
}
