from datetime import datetime
from enum import Enum
from pickletools import stackslice
import sys
from PyQt6 import QtWidgets, QThreadPool
from PyQt6.QtGui import QTextCursor

from serial_manager import search_ports
from ui.main import Ui_MainWindow


class ControllerStatus(Enum):
    disconnected = "Disconnected"
    failed = "Failed"
    connected = "Connected"


class MCUStatus(Enum):
    disconnected = "Disconnected"
    failed = "Failed"
    connected = "Connected"


class MainWindow(QtWidgets.QMainWindow, Ui_MainWindow):
    controller_status: ControllerStatus = ControllerStatus.disconnected
    mcu_status: MCUStatus = MCUStatus.disconnected
    threadpool = QThreadPool()

    def __init__(self, *args, obj=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.setupUi(self)
        self.setWindowTitle("Vine Robot Supervisor")

        _ = self.controllerSearchBtn.clicked.connect(self.update_port_lists)
        _ = self.mcuSearchBtn.clicked.connect(self.update_port_lists)

        self.update_controller_status(ControllerStatus.disconnected)
        self.update_mcu_status(MCUStatus.disconnected)

        self.update_port_lists()

    def update_controller_status(self, status: ControllerStatus):
        controller_status = status
        self.controllerStatusLabel.setText(status.value)
        if status is ControllerStatus.connected:
            self.controllerStatusInfo.setStyleSheet(" QLineEdit { color: green; } ")

        if status is ControllerStatus.disconnected or status is ControllerStatus.failed:
            self.controllerStatusInfo.setStyleSheet(" QLineEdit { color: red; } ")

    def update_mcu_status(self, status: MCUStatus):
        mcu_status = status
        self.mcuStatusInfo.setText(status.value)
        if status is MCUStatus.connected:
            self.mcuStatusInfo.setStyleSheet(" QLineEdit { color: green; } ")

        if status is MCUStatus.disconnected or status is MCUStatus.failed:
            self.mcuStatusInfo.setStyleSheet(" QLineEdit { color: red; } ")

    def update_port_lists(self):
        ports = search_ports()

        for i in range(self.mcuStatusCombo.count()):
            self.mcuStatusCombo.removeItem(i)

        for i in range(self.controllerStatusCombo.count()):
            self.controllerStatusCombo.removeItem(i)

        for port in ports:
            text = f"{port.name} - {port.product}"
            self.controllerStatusCombo.addItem(text)
            self.mcuStatusCombo.addItem(text)

    def update_serial_logs(self, line: str, timestamp: datetime):
        self.serialText.insertPlainText(f"[{timestamp}] {line}\n")


app = QtWidgets.QApplication(sys.argv)

window = MainWindow()
window.show()

for i in range(0, 500):
    window.update_serial_logs(str(i), datetime.now())

app.exec()
