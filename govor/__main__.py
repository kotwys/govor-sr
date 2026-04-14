import sys
from pathlib import Path

import onnx_asr
from PyQt6.QtCore import QObject, QThread, pyqtSignal, pyqtSlot
from PyQt6.QtGui import QFont
from PyQt6.QtWidgets import (
    QApplication,
    QCheckBox,
    QFileDialog,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMainWindow,
    QMessageBox,
    QPushButton,
    QProgressBar,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)


class RecognitionWorker(QObject):
    recognized = pyqtSignal(str)
    failed = pyqtSignal(str)
    finished = pyqtSignal()

    def __init__(self):
        super().__init__()
        self._models = {}

    @pyqtSlot(str, bool)
    def recognize(self, file_path: str, use_normalized_model: bool):
        try:
            model_name = "gigaam-v3-e2e-ctc" if use_normalized_model else "gigaam-v3-ctc"
            if model_name not in self._models:
                self._models[model_name] = onnx_asr.load_model(model_name, path="models")
            result = self._models[model_name].recognize(file_path, channel="mean")
            self.recognized.emit(result)
        except Exception as exc:
            self.failed.emit(str(exc))
        finally:
            self.finished.emit()


class MainWindow(QMainWindow):
    requestRecognition = pyqtSignal(str, bool)

    def __init__(self):
        super().__init__()
        self._selected_file = ""
        self._build_ui()
        self._setup_worker()

    def _build_ui(self):
        self.setWindowTitle("Говор SR")
        self.resize(760, 560)

        central = QWidget(self)
        self.setCentralWidget(central)

        root = QVBoxLayout(central)
        root.setContentsMargins(16, 16, 16, 16)
        root.setSpacing(12)

        title = QLabel("Распознавание диалектной речи")
        title_font = QFont(title.font())
        title_font.setPointSize(title_font.pointSize() + 4)
        title_font.setBold(True)
        title.setFont(title_font)
        root.addWidget(title)

        file_row = QHBoxLayout()
        file_row.setSpacing(12)
        root.addLayout(file_row)

        self.path_field = QLineEdit()
        self.path_field.setReadOnly(True)
        self.path_field.setPlaceholderText("Путь к WAV-файлу аудиозаписи")
        file_row.addWidget(self.path_field)

        self.choose_button = QPushButton("Выбрать...")
        self.choose_button.clicked.connect(self.choose_file)
        file_row.addWidget(self.choose_button)

        self.normalization_checkbox = QCheckBox("Использовать модель с нормализацией текста")
        self.normalization_checkbox.setChecked(False)
        root.addWidget(self.normalization_checkbox)

        action_row = QHBoxLayout()
        action_row.setSpacing(12)
        root.addLayout(action_row)

        self.recognize_button = QPushButton("Распознать")
        self.recognize_button.setEnabled(False)
        self.recognize_button.clicked.connect(self.start_recognition)
        action_row.addWidget(self.recognize_button)

        self.progress = QProgressBar()
        self.progress.setRange(0, 0)
        self.progress.setVisible(False)
        action_row.addWidget(self.progress)

        self.result_text = QTextEdit()
        root.addWidget(self.result_text, 1)

    def _setup_worker(self):
        self._thread = QThread(self)
        self._worker = RecognitionWorker()
        self._worker.moveToThread(self._thread)
        self.requestRecognition.connect(self._worker.recognize)
        self._worker.recognized.connect(self._handle_result)
        self._worker.failed.connect(self._handle_error)
        self._worker.finished.connect(self._handle_finished)
        self._thread.start()

    @pyqtSlot()
    def choose_file(self):
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "Выберите WAV-файл",
            self._selected_file or str(Path.cwd()),
            "WAV файлы (*.wav)",
        )
        if not file_path:
            return

        self._selected_file = file_path
        self.path_field.setText(file_path)
        self.recognize_button.setEnabled(True)

    @pyqtSlot()
    def start_recognition(self):
        if not self._selected_file:
            self._handle_error("Не выбран файл.")
            return

        self.choose_button.setEnabled(False)
        self.normalization_checkbox.setEnabled(False)
        self.recognize_button.setVisible(False)
        self.progress.setVisible(True)
        self.requestRecognition.emit(
            self._selected_file,
            self.normalization_checkbox.isChecked(),
        )

    @pyqtSlot(str)
    def _handle_result(self, text: str):
        self.result_text.setPlainText(text)

    @pyqtSlot(str)
    def _handle_error(self, error: str):
        QMessageBox.critical(self, "Ошибка", error)

    @pyqtSlot()
    def _handle_finished(self):
        self.choose_button.setEnabled(True)
        self.normalization_checkbox.setEnabled(True)
        self.progress.setVisible(False)
        self.recognize_button.setVisible(True)
        self.recognize_button.setEnabled(bool(self._selected_file))

    def closeEvent(self, event):
        self._thread.quit()
        self._thread.wait()
        super().closeEvent(event)


def main():
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
