from datetime import datetime
from enum import Enum
import sys
from PyQt6 import QtWidgets

from packet_protocol import PacketParser, PacketStream, PacketType
from serial_manager import SerialConfig, SerialManager
from ui.main import Ui_MainWindow
from input import Axes, Buttons, ControllerThread
import config

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

        # Controller values
        self.left_x = 0.0
        self.left_y = 0.0
        self.right_x = 0.0
        self.right_y = 0.0
        self.left_trigger = 0.0
        self.right_trigger = 0.0

        # Set up controller communication
        self.controller_thread = ControllerThread(poll_rate=config.CONTROLLER_POLL_RATE)
        self.controller_thread.button_pressed.connect(self.on_button_pressed)
        self.controller_thread.button_released.connect(self.on_button_released)
        self.controller_thread.axis_motion.connect(self.on_axis_motion)

        _ = self.constollerStatusBtn.clicked.connect(self.controller_connect_btn)

    def mcu_connect_btn(self):
        if self.serial_mgr.is_connected():
            self.serial_mgr.disconnect()
            self.mcuStatusInfo.setText("Disconnected")
            self.mcuStatusInfo.setStyleSheet(" QLineEdit { color: red; } ")

        else:
            success = self.serial_mgr.connect(self.mcuStatusCombo.currentText(), SerialConfig(baud_rate=config.MCU_BAUD_RATE))
            if not success:
                self.on_error("Failed to connect to MCU")
                return

            self.mcuStatusInfo.setText("Connected")
            self.mcuStatusInfo.setStyleSheet(" QLineEdit { color: green; } ")

    def controller_connect_btn(self)
        if self.controller_thread.is_running():
            pass

        else:
            self.controller_thread.start()

    def on_packet_received(self, packet_type: PacketType, payload: bytes):
        """
        Run every time a packet is revievd from the MCU
        """

        # Update the serial text stream
        self.serialText.insertPlainText(f"[{datetime.now().strftime("%H:%M:%S.%f")}] {packet_type.name} - {payload.hex()}")

    def on_error(self, text: str):
        pass

    def on_button_pressed(self, button_id: int):
        pass

    def on_button_released(self, button_id: int):
        pass

    def on_axis_motion(self, axis_id: int, value: float):
        if abs(value) > config.TRIGGER_DEADZONE
            if axis_id == Axes.LEFT_TRIGGER:
                self.left_trigger = value

            elif axis_id == Axes.RIGHT_TRIGGER:
                self.right_trigger = value

        if abs(value) > config.JOYSTICK_DEADZONE:
            if axis_id == Axes.LEFT_X:
                self.left_x = value

            elif axis_id == Axes.LEFT_Y:
                self.left_y = value

            elif axis_id == Axes.RIGHT_X:
                self.right_x = value

            elif axis_id == Axes.RIGHT_Y:
                self.right_y = value

    def closeEvent(self, a0):
        """Clean up when window closes."""
        self.controller_thread.stop()
        self.controller_thread.wait()
        a0.accept()


def run():
    app = QtWidgets.QApplication(sys.argv)

    window = MainWindow()
    window.show()

    app.exec()
