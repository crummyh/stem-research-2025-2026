from datetime import datetime
from enum import Enum
import sys
from PyQt6 import QtWidgets

from packet_protocol import PacketParser, PacketStream, PacketType
from serial_manager import SerialConfig, SerialManager
from ui.main import Ui_MainWindow


class ControllerStatus(Enum):
    disconnected = "Disconnected"
    failed = "Failed"
    connected = "Connected"


class MainWindow(QtWidgets.QMainWindow, Ui_MainWindow):
    def __init__(self, *args, obj=None, **kwargs):
        super().__init__(*args, **kwargs)
        # Load the generated UI
        self.setupUi(self)
        self.setWindowTitle("Vine Robot Supervisor")

        # Set up MCU communication
        self.serial_mgr = SerialManager(auto_decode=False, add_newline=False)
        self.packet_stream = PacketStream(self.serial_mgr)

        # Connect MCU communication signals
        _ = self.packet_stream.packet_received.connect(self.on_packet_received)
        _ = self.mcuStatusBtn.clicked.connect(self.mcu_connect_btn)

    def mcu_connect_btn(self):
        if self.serial_mgr.is_connected():
            self.serial_mgr.disconnect()
            self.mcuStatusInfo.setText("Disconnected")
            self.mcuStatusInfo.setStyleSheet(" QLineEdit { color: red; } ")

        else:
            success = self.serial_mgr.connect(self.mcuStatusCombo.currentText(), SerialConfig(baud_rate=115200))
            if not success:
                self.on_error("Failed to connect to MCU")
                return

            self.mcuStatusInfo.setText("Connected")
            self.mcuStatusInfo.setStyleSheet(" QLineEdit { color: green; } ")

    def on_packet_received(self, packet_type: PacketType, payload: bytes):
        """
        Run every time a packet is revievd from the MCU
        """

        # Update the serial text stream
        self.serialText.insertPlainText(f"[{datetime.now().strftime("%H:%M:%S.%f")}] {packet_type.name} - {payload.hex()}")

    def on_error(self, text: str):
        pass


app = QtWidgets.QApplication(sys.argv)

window = MainWindow()
window.show()

app.exec()
