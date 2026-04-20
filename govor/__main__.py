import sys

from PySide6.QtCore import Property, QObject, QThread, QUrl, Signal, Slot
from PySide6.QtGui import QGuiApplication
from PySide6.QtQml import QQmlApplicationEngine
from PySide6.QtWidgets import QMessageBox

import onnx_asr


class RecognitionWorker(QObject):
    finished = Signal(str)
    failed = Signal(str)

    def __init__(self):
        super().__init__()
        self.model = None

    @Slot(str)
    def recognize(self, file_path: str):
        try:
            if self.model == None:
                self.model = onnx_asr.load_model(
                    "gigaam-v3-e2e-ctc",
                    path="models/gigaam"
                )

            result = self.model.recognize(file_path, channel='mean')
            self.finished.emit(result)
        except Exception as ex:
            self.failed.emit(str(ex))


class Bridge(QObject):
    busy_changed = Signal()
    file_path_changed = Signal()
    text_changed = Signal()

    request_recognition = Signal(str)
    error = Signal(str)

    def __init__(self):
        super().__init__()
        self._is_busy = False
        self._selected_file = ""
        self._result_text = ""

        self._thread = QThread(self)
        self._worker = RecognitionWorker()
        self._worker.moveToThread(self._thread)
        self.request_recognition.connect(self._worker.recognize)
        self._worker.finished.connect(self._on_finished)
        self._worker.failed.connect(self._on_error)
        self._thread.start()

    @Property(bool, notify=busy_changed)
    def isBusy(self): return self._is_busy

    @Property(str, notify=text_changed)
    def resultText(self): return self._result_text

    @Property(str, notify=file_path_changed)
    def selectedFile(self): return self._selected_file

    @Slot(str)
    def selectFile(self, file_url):
        self._selected_file = QUrl(file_url).toLocalFile()
        self.file_path_changed.emit()

    @Slot()
    def startRecognition(self):
        if not self._selected_file:
            self._on_error("Выберите файл")
            return

        self._is_busy = True
        self.busy_changed.emit()
        self.request_recognition.emit(self._selected_file)

    @Slot(str)
    def _on_finished(self, text: str):
        self._is_busy = False
        self._result_text = text
        self.busy_changed.emit()
        self.text_changed.emit()

    @Slot(str)
    def _on_error(self, text: str):
        self._is_busy = False
        self.busy_changed.emit()
        self.error.emit(text)

    @Slot()
    def onAppClose(self):
        self._thread.quit()
        self._thread.wait()


def main():
    app = QGuiApplication(sys.argv)
    engine = QQmlApplicationEngine()

    bridge = Bridge()
    engine.rootContext().setContextProperty("backend", bridge)

    engine.load('qml/main.qml')
    if not engine.rootObjects():
        sys.exit(-1)
    sys.exit(app.exec())


if __name__ == '__main__':
    main()
