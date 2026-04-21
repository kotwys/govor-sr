import sys

from PySide6.QtCore import Property, QObject, QThread, QUrl, Signal, Slot
from PySide6.QtGui import QGuiApplication
from PySide6.QtQml import QQmlApplicationEngine

import onnx_asr

from .phonemizer import RussianPhonemizer
from .transcription import generate_transcription
from .transform import TransformationEngine


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

    request_recognition = Signal(str)
    error = Signal(str)
    result = Signal(str)

    def __init__(self):
        super().__init__()
        self._is_busy = False

        self._thread = QThread(self)
        self._worker = RecognitionWorker()
        self._worker.moveToThread(self._thread)
        self.request_recognition.connect(self._worker.recognize)
        self._worker.finished.connect(self._on_finished)
        self._worker.failed.connect(self._on_error)
        self._thread.start()

        self._phonemizer = RussianPhonemizer()
        self.reloadRules()

    @Property(bool, notify=busy_changed)
    def isBusy(self): return self._is_busy

    @Slot()
    def reloadRules(self):
        try:
            with open('rules.go') as f:
                data = f.read()
            self._engine = TransformationEngine(data)
        except Exception as ex:
            self._on_error(str(ex))

    @Slot(str, bool)
    def startRecognition(self, audio: str, normalized: bool):
        file_path = QUrl(audio).toLocalFile()
        self._is_busy = True
        self.busy_changed.emit()
        self.request_recognition.emit(file_path)

    @Slot(str, result=str)
    def phonemize(self, input: str) -> str:
        try:
            phonemes = self._phonemizer.phonemize(input)
            transformed = self._engine.run(phonemes)
            return generate_transcription(transformed)
        except Exception as ex:
            self._on_error(str(ex))
            return ""

    @Slot(str)
    def _on_finished(self, text: str):
        self._is_busy = False
        self.busy_changed.emit()
        self.result.emit(text)

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
