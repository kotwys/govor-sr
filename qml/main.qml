import QtQuick
import QtQuick.Controls
import QtQuick.Layouts
import QtQuick.Dialogs
import QtMultimedia

ApplicationWindow {
    visible: true
    width: 760
    height: 560
    minimumWidth: 500
    minimumHeight: 500
    title: "Говор"

    property url audio

    function displayLength(ms) {
        const sec = Math.floor(ms / 1000);
        const min = Math.floor(sec / 60);
        return min + ":" + (sec % 60).toFixed(0).padStart(2, '0');
    }

    function updatePhonetic() {
        if (orthography.text !== "") {
            phonetic.text = backend.phonemize(orthography.text);
        } else {
            phonetic.text = "";
        }
    }

    onClosing: (close) => {
        backend.onAppClose();
    }

    FileDialog {
        id: fileDialog
        title: "Выберите WAV-файл"
        nameFilters: ["WAV-файлы (*.wav)"]
        onAccepted: {
            audio = selectedFile;
        }
    }

    MediaPlayer {
        id: player
        audioOutput: AudioOutput {}
        source: audio
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
        function onResult(msg) {
            orthography.text = msg;
        }
    }

    ColumnLayout {
        anchors.fill: parent
        anchors.margins: 16
        spacing: 12

        Label {
            text: "Транскрибирование диалектной речи"
            font.bold: true
            font.pointSize: 15
        }

        RowLayout {
            Layout.fillWidth: true
            spacing: 8

            TextField {
                Layout.fillWidth: true
                readOnly: true
                text: audio != "" ? new URL(audio).pathname : ""
                placeholderText: "Выберите файл аудиозаписи"
            }

            Button {
                text: "Выбрать..."
                onClicked: fileDialog.open()
            }
        }

        RowLayout {
            enabled: audio != ""
            spacing: 10

            Button {
                icon.name: player.playbackState === MediaPlayer.PlayingState
                           ? "media-playback-pause"
                           : "media-playback-start"
                ToolTip.visible: hovered
                ToolTip.text: player.playbackState === MediaPlayer.PlayingState
                              ? "Пауза" : "Воспроизвести"
                ToolTip.delay: Qt.styleHints.mousePressAndHoldInterval
                onClicked: {
                    if (player.playbackState === MediaPlayer.PlayingState) {
                        player.pause();
                    } else {
                        player.play();
                    }
                }
            }

            Label {
                Layout.preferredWidth: 30
                text: audio != "" ? displayLength(player.position) : "--:--"
            }

            Slider {
                Layout.fillWidth: true
                from: 0
                to: player.duration
                value: player.position
                onMoved: player.position = value
            }

            Label {
                Layout.preferredWidth: 30
                text: audio != "" ? displayLength(player.duration) : "--:--"
            }
        }

        Item {
            Layout.fillWidth: true
            Layout.preferredHeight: 32

            Button {
                anchors.fill: parent
                text: "Распознать"
                enabled: audio != "" && !backend.isBusy
                visible: !backend.isBusy
                onClicked: backend.startRecognition(audio, true)
            }

            ProgressBar {
                anchors.fill: parent
                indeterminate: true
                visible: backend.isBusy
            }
        }

        ColumnLayout {
            spacing: 16

            ColumnLayout {
                Label {
                    text: "Орфографическая запись"
                }

                RowLayout {
                    CyrText {
                        id: orthography
                        readOnly: backend.isBusy
                        onTextChanged: updatePhonetic()
                    }

                    ColumnLayout {
                        Layout.alignment: Qt.AlignTop

                        Button {
                            icon.name: "edit-copy"
                            ToolTip.visible: hovered
                            ToolTip.text: "Скопировать орфографическую запись"
                            ToolTip.delay: Qt.styleHints.mousePressAndHoldInterval
                            onClicked: {
                                orthography.selectAll();
                                orthography.copy();
                            }
                        }

                        Button {
                            Layout.preferredWidth: 32
                            text: "á"
                            ToolTip.visible: hovered
                            ToolTip.text: "Поставить ударение перед курсором"
                            ToolTip.delay: Qt.styleHints.mousePressAndHoldInterval
                            onClicked: () => {
                                const pos = orthography.cursorPosition;
                                const txt = orthography.text
                                if (txt.length == 0 || pos == 0)
                                    return;
                                if (txt.charCodeAt(pos-1) === 0x301)
                                    return;
                                orthography.text = txt.slice(0, pos) + "\u0301" + txt.slice(pos);
                                orthography.forceActiveFocus();
                                orthography.cursorPosition = pos + 1;
                            }
                        }
                    }
                }
            }

            ColumnLayout {
                Label {
                    text: "Фонетическая запись"
                }

                RowLayout {
                    CyrText {
                        id: phonetic
                        readOnly: true
                    }

                    ColumnLayout {
                        Layout.alignment: Qt.AlignTop

                        Button {
                            icon.name: "edit-copy"
                            ToolTip.visible: hovered
                            ToolTip.text: "Скопировать фонетическую запись"
                            ToolTip.delay: Qt.styleHints.mousePressAndHoldInterval
                            onClicked: {
                                phonetic.selectAll();
                                phonetic.copy();
                            }
                        }

                        Button {
                            icon.name: "view-refresh"
                            ToolTip.visible: hovered
                            ToolTip.text: "Обновить список правил"
                            ToolTip.delay: Qt.styleHints.mousePressAndHoldInterval
                            onClicked: {
                                backend.reloadRules();
                                updatePhonetic();
                            }
                        }
                    }
                }
            }
        }
    }
}
