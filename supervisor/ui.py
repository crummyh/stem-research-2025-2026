import sys
from datetime import datetime

from PyQt6 import QtWidgets

import config
from generated_ui.main import Ui_MainWindow
from input import Axes, Buttons, ControllerThread
from packet_protocol import PacketBuilder, PacketParser, PacketStream, PacketType
from serial_manager import SerialConfig, SerialManager


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
        _ = self.packet_stream.packet_sent.connect(self.on_packet_sent)
        _ = self.mcuStatusBtn.clicked.connect(self.mcu_connect_btn)
        _ = self.mcuSearchBtn.clicked.connect(self.mcu_search)

        self.mcu_search()

        # Init MCU stats
        self.mcu_connecting = False

        self.mcu_mode = 0
        self.mcu_state = 0

        # Controller values
        self.left_x = 0.0
        self.left_y = 0.0
        self.right_x = 0.0
        self.right_y = 0.0
        self.left_trigger = 0.0
        self.right_trigger = 0.0

        # Set up controller communication
        self.controller_thread = ControllerThread(poll_rate=config.CONTROLLER_POLL_RATE)
        _ = self.controller_thread.button_pressed.connect(self.on_button_pressed)
        _ = self.controller_thread.button_released.connect(self.on_button_released)
        _ = self.controller_thread.axis_motion.connect(self.on_axis_motion)

        _ = self.controllerStatusBtn.clicked.connect(self.controller_connect_btn)

        _ = self.testBtn.clicked.connect(self.test_ping)

    def test_ping(self):
        self.packet_stream.send_packet(PacketType.PING)

    def mcu_connect_btn(self):
        if self.serial_mgr.is_connected():
            self.serial_mgr.disconnect()
            self.mcuStatusInfo.setText("Disconnected")
            self.mcuStatusInfo.setStyleSheet(" QLineEdit { color: red; } ")

        else:
            success = self.serial_mgr.connect(
                self.mcuStatusCombo.currentText(),
                SerialConfig(baud_rate=config.MCU_BAUD_RATE),
            )
            if not success:
                self.on_error("Failed to connect to MCU")
                return

            self.mcuStatusInfo.setText("Connecting")
            self.mcuStatusInfo.setStyleSheet(" QLineEdit { color: yellow; } ")

            self.controller_thread.send_packet(PacketType.PING)
            self.mcu_connecting = True

    def controller_connect_btn(self):
        if self.controller_thread.isRunning():
            self.controller_thread.stop()
            self.controllerStatusBtn.setText("Connect")
            self.controllerStatusInfo.setText("Disconnected")
            self.controllerStatusInfo.setStyleSheet(" QLineEdit { color: red; } ")

        else:
            self.controller_thread.start()

            if self.controller_thread.isRunning():
                self.controllerStatusBtn.setText("Disconnect")
                self.controllerStatusInfo.setText("Connected")
                self.controllerStatusInfo.setStyleSheet(" QLineEdit { color: green; } ")

            else:
                self.controller_thread.stop()
                self.on_error("Failed to connect to controller")

    def mcu_search(self):
        ports = SerialManager.find_arduino_ports()
        for i in range(self.mcuStatusCombo.count()):
            self.mcuStatusCombo.removeItem(i)

        self.mcuStatusCombo.insertItems(0, ports)

    def on_packet_sent(self, packet_type: PacketType, payload: bytes):
        cursor = self.serialText.textCursor()
        cursor.movePosition(cursor.MoveOperation.End)
        self.serialText.setTextCursor(cursor)

        # Update the serial text stream
        self.serialText.insertPlainText(
            f"[{datetime.now().strftime('%H:%M:%S.%f')}] {PacketType(packet_type).name} {payload.hex()}\n"
        )

    def on_packet_received(self, packet_type: PacketType, payload: bytes):
        """
        Run every time a packet is retrieved from the MCU
        """

        cursor = self.serialText.textCursor()
        cursor.movePosition(cursor.MoveOperation.End)
        self.serialText.setTextCursor(cursor)

        # Update the serial text stream
        self.serialText.insertPlainText(
            f"[{datetime.now().strftime('%H:%M:%S.%f')}] {PacketType(packet_type).name} {payload.hex()}\n"
        )

        # Handle the packet
        if self.mcu_connecting and packet_type == PacketType.PONG:
            self.mcu_connecting = False
            self.controllerStatusInfo.setText("Connected")
            self.controllerStatusInfo.setStyleSheet(" QLineEdit { color: green; } ")
            return
        
        elif packet_type == PacketType.PING:
            self.packet_stream.send_packet(PacketType.PONG)

        elif packet_type == PacketType.STATUS_UPDATE:
            status = PacketParser.parse_status_update(payload)
            self.mcu_mode = status.mode
            self.mcu_state = status.state

        else:
            self.packet_stream.send_packet(PacketBuilder.nack(0xff))

    def on_error(self, text: str):
        msgBox = QMessageBox()
        msgBox.setText(text)
        msgBox.exec()

    def on_button_pressed(self, button_id: int):
        pass

    def on_button_released(self, button_id: int):
        pass

    def on_axis_motion(self, axis_id: int, value: float):
        if abs(value) > (-1 + config.TRIGGER_DEADZONE):
            if axis_id == Axes.LEFT_TRIGGER:
                value = (0.5 * value) + 0.5
                self.left_trigger = value

            elif axis_id == Axes.RIGHT_TRIGGER:
                value = (0.5 * value) + 0.5
                self.right_trigger = value

        else:
            if axis_id == Axes.LEFT_TRIGGER:
                self.left_trigger = 0

            elif axis_id == Axes.RIGHT_TRIGGER:
                self.right_trigger = 0

        if abs(value) > config.JOYSTICK_DEADZONE:
            if axis_id == Axes.LEFT_X:
                self.left_x = value

            elif axis_id == Axes.LEFT_Y:
                self.left_y = value * -1  # Invert the y direction

            elif axis_id == Axes.RIGHT_X:
                self.right_x = value

            elif axis_id == Axes.RIGHT_Y:
                self.right_y = value * -1  # Invert the y direction

        else:
            if axis_id == Axes.LEFT_X:
                self.left_x = 0

            elif axis_id == Axes.LEFT_Y:
                self.left_y = 0

            elif axis_id == Axes.RIGHT_X:
                self.right_x = 0

            elif axis_id == Axes.RIGHT_Y:
                self.right_y = 0

        self.tempControllerText.setText(f"""
            LT: {self.left_trigger}
            RT: {self.right_trigger}
            L: {self.left_x}, {self.left_y}
            R: {self.right_x}, {self.right_y}
            """)

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
