import sys

from PyQt6.QtCore import QSize, Qt
from PyQt6.QtGui import QColor, QPalette
from PyQt6.QtWidgets import (
    QApplication,
    QHBoxLayout,
    QMainWindow,
    QPushButton,
    QVBoxLayout,
    QWidget,
)


class VideoStream(QWidget):
    def __init__(self, color):
        super().__init__()
        self.setAutoFillBackground(True)

        palette = self.palette()
        palette.setColor(QPalette.ColorRole.Window, QColor(color))
        self.setPalette(palette)


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Vine Robot Supervisor")

        main_layout = QHBoxLayout()
        side_layout = QVBoxLayout()

        side_layout.addWidget(VideoStream("red"))
        side_layout.addWidget(VideoStream("yellow"))
        side_layout.addWidget(VideoStream("purple"))

        main_layout.addWidget(VideoStream("green"))
        main_layout.addLayout(side_layout)

        central_widget = QWidget()
        central_widget.setLayout(main_layout)
        self.setCentralWidget(central_widget)


def run():
    app = QApplication(sys.argv)

    window = MainWindow()
    window.show()

    app.exec()
