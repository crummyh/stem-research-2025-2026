from datetime import datetime
from enum import Enum
import sys
from PyQt6 import QtWidgets

from serial_manager import SerialConfig, SerialManager
from ui.main import Ui_MainWindow


class ControllerStatus(Enum):
    disconnected = "Disconnected"
    failed = "Failed"
    connected = "Connected"


class MainWindow(QtWidgets.QMainWindow, Ui_MainWindow):
    controller_status: ControllerStatus = ControllerStatus.disconnected

    def __init__(self, *args, obj=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.setupUi(self)
        self.setWindowTitle("Vine Robot Supervisor")

        self.update_controller_status(ControllerStatus.disconnected)
        self.update_mcu_status(False)

        self.serial = SerialManager(auto_decode=True, add_newline=True)

        _ = self.serial.data_received.connect(self.on_serial_data)
        _ = self.serial.connection_changed.connect(self.update_mcu_status)
        # _ = self.serial.error_occurred.connect(self.on_error)

        _ = self.mcuSearchBtn.clicked.connect(self.refresh_port_list)

        config = SerialConfig(baud_rate=9600)
        _ = self.serial.connect("COM3", config)

        self.refresh_port_list()

    def toggle_mcu_connection(self):
        if self.serial.is_connected():
            self.serial.disconnect()
            self.update_mcu_status(False)
        else:
            port = self.mcuStatusCombo.currentText().split(" - ")[0]
            self.serial.connect(port)
            self.update_mcu_status(True)

    def update_controller_status(self, status: ControllerStatus):
        self.controller_status = status
        self.controllerStatusLabel.setText(status.value)
        if status is ControllerStatus.connected:
            self.controllerStatusInfo.setStyleSheet(" QLineEdit { color: green; } ")

        if status is ControllerStatus.disconnected or status is ControllerStatus.failed:
            self.controllerStatusInfo.setStyleSheet(" QLineEdit { color: red; } ")

    def update_mcu_status(self, status: bool):
        if status is True:
            self.mcuStatusInfo.setText("Connected")
        else:
            self.mcuStatusInfo.setText("Disconnected")

        if status is True:
            self.mcuStatusInfo.setStyleSheet(" QLineEdit { color: green; } ")

        if status is False:
            self.mcuStatusInfo.setStyleSheet(" QLineEdit { color: red; } ")

    def refresh_port_list(self):
        ports = SerialManager.find_arduino_ports()

        for i in range(self.mcuStatusCombo.count()):
            self.mcuStatusCombo.removeItem(i)

        if len(ports) == 0:
            self.mcuStatusCombo.addItem("No device found")

        for port in ports:
            text = f"{port[0]} - {port[1]}"
            self.mcuStatusCombo.addItem(text)

    def on_serial_data(self, text: str):
        timestamp = datetime.now()
        self.serialText.insertPlainText(f"[{timestamp}] {text}\n")


app = QtWidgets.QApplication(sys.argv)

window = MainWindow()
window.show()

app.exec()
