import sys
from datetime import datetime
from enum import Enum

from PyQt6 import QtWidgets
from PyQt6.QtCore import QTimer
from PyQt6.QtGui import QKeySequence, QShortcut

from generated_ui.main import Ui_MainWindow
from src import config
from src.control import cartesian_to_polar, controller_to_spool, controller_to_tendon
from src.input import Axes, Buttons, ControllerThread
from src.packet_protocol import PacketBuilder, PacketParser, PacketStream, PacketType
from src.serial_manager import SerialConfig, SerialManager
from src.steering_widget import RobotSteeringWidget


class ControllerStatus(str, Enum):
    DISCONNECTED = "disconnected"
    CONNECTED = "connected"


class McuConnectionStatus(str, Enum):
    DISCONNECTED = "disconnected"
    CONNECTING = "connecting"
    CONNECTED = "connected"


class ActivationStatus(str, Enum):
    DISABLED = "disabled"
    ENABLED = "enabled"


class MainWindow(QtWidgets.QMainWindow, Ui_MainWindow):
    def __init__(self, *args, obj=None, **kwargs):
        super().__init__(*args, **kwargs)
        # Load the generated UI
        self.setupUi(self)
        self.setWindowTitle("Vine Robot Supervisor")

        # Set up MCU communication
        self.serial_mgr = SerialManager(auto_decode=False, add_newline=False)
        self.serial_mgr.error_occurred.connect(self.on_error)
        self.packet_stream = PacketStream(self.serial_mgr)

        # Connect MCU communication signals
        self.packet_stream.packet_received.connect(self.on_packet_received)
        self.packet_stream.packet_sent.connect(self.on_packet_sent)
        self.packet_stream.error_occurred.connect(self.on_error)
        self.mcuStatusBtn.clicked.connect(self.mcu_connect_btn)
        self.mcuSearchBtn.clicked.connect(self.mcu_search)

        self.mcu_search()

        # Set up status bar
        self.statusbar_activation = QtWidgets.QLabel()
        self.statusbar_mcu_connection = QtWidgets.QLabel()
        self.statusbar_controller_connection = QtWidgets.QLabel()

        self.statusbar.addPermanentWidget(self.statusbar_activation)
        self.statusbar.addPermanentWidget(self.statusbar_mcu_connection)
        self.statusbar.addPermanentWidget(self.statusbar_controller_connection)

        # Init MCU stats
        self.mcu_connection_status = McuConnectionStatus.DISCONNECTED
        self._set_mcu_status(McuConnectionStatus.DISCONNECTED, True)

        self.mcu_connect_timer = QTimer(self)
        self.mcu_connect_timer.timeout.connect(self.mcu_connection_attempt)
        self.mcu_connection_attempts = 10

        self.mcu_mode = 0
        self.mcu_state = 0
        self.mcu_activation_status = ActivationStatus.DISABLED
        self._set_activation_status(ActivationStatus.DISABLED, True)

        self.activationButton.clicked.connect(self.toggle_activation_btn)
        self.activation_shortcut = QShortcut(QKeySequence(" "), self)
        self.activation_shortcut.setAutoRepeat(False)
        self.activation_shortcut.activated.connect(self.toggle_activation_btn)
        self.activationButton.setStyleSheet(
            " QPushButton { background-color: red; color: white; } "
        )

        self.tendon1Progress.setMaximum(int(config.MAX_TENDON_VALUE * 100))
        self.tendon1Progress.setMinimum(int(config.MAX_TENDON_VALUE * -100))
        self.tendon2Progress.setMaximum(int(config.MAX_TENDON_VALUE * 100))
        self.tendon2Progress.setMinimum(int(config.MAX_TENDON_VALUE * -100))
        self.tendon3Progress.setMaximum(int(config.MAX_TENDON_VALUE * 100))
        self.tendon3Progress.setMinimum(int(config.MAX_TENDON_VALUE * -100))

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

        self.controller_status = ControllerStatus.DISCONNECTED
        self._set_controller_status(ControllerStatus.DISCONNECTED, True)

        self.controllerStatusBtn.clicked.connect(self.controller_connect_btn)

        # Connect settings
        self.spoolSpeedModifier = 0
        self.spoolSpeedSettingSlider.setMinimum(0)
        self.spoolSpeedSettingSlider.setMaximum(int(config.MAX_SPOOL_SPEED * 100))
        self.spoolSpeedSettingSlider.sliderMoved.connect(
            self.on_spool_speed_slider_update
        )

        self.spoolSpeedProgress.setMinimum(0)
        self.spoolSpeedProgress.setMaximum(int(config.MAX_SPOOL_SPEED * 100))

        # Set up custom widgets
        self.steering_widget = RobotSteeringWidget()
        self.tendonInfoLayout.addChildWidget(self.steering_widget)
        self.steering_widget.setMaximumSize(400, 400)

    def mcu_connect_btn(self):
        if self.serial_mgr.is_connected():
            self._set_mcu_status(McuConnectionStatus.DISCONNECTED)

        else:
            self._set_mcu_status(McuConnectionStatus.CONNECTING)

    def mcu_connection_attempt(self):
        if self.mcu_connection_attempts <= 0:
            self.mcu_connect_timer.stop()
            self.on_error("Failed to connect to MCU")
            return

        self.packet_stream.send_packet(PacketType.PING, PacketBuilder.ping(), False)
        self.mcu_connection_attempts -= 1

    def on_spool_speed_slider_update(self):
        self.spoolSpeedModifier = float(self.spoolSpeedSettingSlider.value()) / 100

    def controller_connect_btn(self):
        if self.controller_thread.isRunning():
            self._set_controller_status(ControllerStatus.DISCONNECTED)

        else:
            self._set_controller_status(ControllerStatus.CONNECTED)

    def mcu_search(self):
        ports = SerialManager.find_arduino_ports()
        for i in range(self.mcuStatusCombo.count()):
            self.mcuStatusCombo.removeItem(i)

        self.mcuStatusCombo.insertItems(0, ports)

    def toggle_activation_btn(self):
        if self.mcu_activation_status == ActivationStatus.ENABLED:
            self._set_activation_status(ActivationStatus.DISABLED)

        elif self.mcu_activation_status == ActivationStatus.DISABLED:
            self._set_activation_status(ActivationStatus.ENABLED)

    def on_packet_sent(self, packet_type: PacketType, payload: bytes):
        cursor = self.serialText.textCursor()
        cursor.movePosition(cursor.MoveOperation.End)
        self.serialText.setTextCursor(cursor)

        # Update the serial text stream
        self.serialText.insertPlainText(
            f"[{datetime.now().strftime('%H:%M:%S.%f')}] -> {PacketType(packet_type).name} {payload.hex(' ')}\n"
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
            f"[{datetime.now().strftime('%H:%M:%S.%f')}] <- {PacketType(packet_type).name} {payload.hex(' ')}\n"
        )

        # Handle the packet
        if (
            self.mcu_connection_status == McuConnectionStatus.CONNECTING
            and packet_type == PacketType.PONG
        ):
            self._set_mcu_status(McuConnectionStatus.CONNECTED)
            return

        elif packet_type == PacketType.PONG:
            return

        elif packet_type == PacketType.ACK:
            return

        elif packet_type == PacketType.PING:
            self.packet_stream.send_packet(PacketType.PONG)

        elif packet_type == PacketType.STATUS_UPDATE:
            status = PacketParser.parse_status_update(payload)
            if status is not None:
                self.mcu_mode = status.mode
                self.mcu_state = status.state

        else:
            self.packet_stream.send_packet(PacketType.NACK, PacketBuilder.nack(0xFF))

    def on_error(self, text: str):
        msgBox = QtWidgets.QMessageBox()
        msgBox.setText(text)
        msgBox.exec()

    def on_button_pressed(self, button_id: int):
        if button_id == Buttons.LOGO:
            self.toggle_activation_btn()

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

        if (
            self.mcu_connection_status == McuConnectionStatus.CONNECTED
            and self.mcu_activation_status == ActivationStatus.ENABLED
        ):
            if axis_id == Axes.LEFT_X or axis_id == Axes.LEFT_Y:
                tendon_values = tuple(
                    float(i)
                    for i in controller_to_tendon(
                        round(self.left_x, 5), round(self.left_y, 5)
                    )
                )
                self.packet_stream.send_packet(
                    PacketType.CMD_SET_TENDONS,
                    PacketBuilder.set_tendons(*tendon_values),
                )
                self.steering_widget.setTendonValues(*tendon_values)
                self.steering_widget.setSteering(
                    *cartesian_to_polar(self.left_x, self.left_y)
                )

                self.tendon1Progress.setValue(int(tendon_values[0] * 100))
                self.tendon2Progress.setValue(int(tendon_values[1] * 100))
                self.tendon3Progress.setValue(int(tendon_values[2] * 100))

            elif axis_id == Axes.LEFT_TRIGGER or axis_id == Axes.RIGHT_TRIGGER:
                speed = controller_to_spool(
                    round(self.left_trigger, 2),
                    round(self.right_trigger, 2),
                    self.spoolSpeedModifier,
                )
                self.spoolSpeedProgress.setValue(int(abs(speed) * 100))
                self.spoolSpeedProgress.setFormat(f"{speed:.2f} rpm")
                self.packet_stream.send_packet(
                    PacketType.CMD_SET_SPOOL, PacketBuilder.set_spool_speed(speed)
                )

    def closeEvent(self, a0):
        """Clean up when window closes."""
        self.controller_thread.stop()
        self.controller_thread.wait()
        a0.accept()

    def _set_mcu_status(self, status: McuConnectionStatus, visual_only: bool = False):
        if status == McuConnectionStatus.DISCONNECTED:
            if not visual_only:
                self.packet_stream.send_packet(PacketType.CMD_STOP)
                self.serial_mgr.disconnect()
                self.mcu_connection_status = McuConnectionStatus.DISCONNECTED

            self.activationButton.setStyleSheet(
                " QPushButton { background-color: red; } "
            )
            self.activationButton.setText("Disabled")
            self.mcuStatusInfo.setText("Disconnected")
            self.mcuStatusInfo.setStyleSheet(" QLineEdit { color: red; } ")
            self.statusbar_mcu_connection.setText("MCU: Disconnected")
            self.statusbar_mcu_connection.setStyleSheet(" QLabel { color: red; } ")

        elif status == McuConnectionStatus.CONNECTING:
            if not visual_only:
                success = self.serial_mgr.connect(
                    self.mcuStatusCombo.currentText(),
                    SerialConfig(baud_rate=config.MCU_BAUD_RATE),
                )
                if not success:
                    self.on_error("Failed to connect to MCU")
                    return

                self.mcu_connection_attempt()
                self.mcu_connection_status = McuConnectionStatus.CONNECTING
                self.mcu_connection_attempts = 10
                self.mcu_connect_timer.start(1000)

            self.mcuStatusInfo.setText("Connecting")
            self.mcuStatusInfo.setStyleSheet(" QLineEdit { color: yellow; } ")

            self.statusbar_mcu_connection.setText("MCU: Connecting")
            self.statusbar_mcu_connection.setStyleSheet(" QLabel { color: yellow; } ")

        elif status == McuConnectionStatus.CONNECTED:
            if not visual_only:
                self.mcu_connection_status = McuConnectionStatus.CONNECTED
                self.mcu_connect_timer.stop()

            self.mcuStatusInfo.setText("Connected")
            self.mcuStatusInfo.setStyleSheet(" QLineEdit { color: green; } ")

            self.statusbar_mcu_connection.setText("MCU: Connected")
            self.statusbar_mcu_connection.setStyleSheet(" QLabel { color: green; } ")

    def _set_controller_status(
        self, status: ControllerStatus, visual_only: bool = False
    ):
        if status == ControllerStatus.DISCONNECTED:
            if not visual_only:
                if self.controller_thread.isRunning():
                    self.controller_thread.stop()

            self.controllerStatusBtn.setText("Connect")
            self.controllerStatusInfo.setText("Disconnected")
            self.controllerStatusInfo.setStyleSheet(" QLineEdit { color: red; } ")

            self.statusbar_controller_connection.setText("Controller: Disconnected")
            self.statusbar_controller_connection.setStyleSheet(
                " QLabel { color: red; } "
            )

        elif status == ControllerStatus.CONNECTED:
            if not visual_only:
                self.controller_thread.start()

            if self.controller_thread.isRunning():
                self.controllerStatusBtn.setText("Disconnect")
                self.controllerStatusInfo.setText("Connected")
                self.controllerStatusInfo.setStyleSheet(" QLineEdit { color: green; } ")

                self.statusbar_controller_connection.setText("Controller: Connected")
                self.statusbar_controller_connection.setStyleSheet(
                    " QLabel { color: green; } "
                )

            else:
                if not visual_only:
                    self.controller_thread.stop()
                    self.on_error("Failed to connect to controller")

    def _set_activation_status(
        self, status: ActivationStatus, visual_only: bool = False
    ):
        if (
            not visual_only
            and self.mcu_connection_status != McuConnectionStatus.CONNECTED
        ):
            self.on_error("Failed to change activation state: MCU is not connected")

        if status == ActivationStatus.DISABLED:
            if not visual_only:
                self.mcu_activation_status = ActivationStatus.DISABLED
                self.packet_stream.send_packet(PacketType.CMD_STOP)

            self.activationButton.setStyleSheet(
                " QPushButton { background-color: red; } "
            )
            self.activationButton.setText("Disabled")

            self.statusbar_activation.setText("Disabled")
            self.statusbar_activation.setStyleSheet(
                " QLabel { color: red; font-weight: bold; font-style: italic; } "
            )

        elif status == ActivationStatus.ENABLED:
            if not visual_only:
                self.mcu_activation_status = ActivationStatus.ENABLED
                self.packet_stream.send_packet(PacketType.CMD_START)

            self.activationButton.setStyleSheet(
                " QPushButton { background-color: green; } "
            )
            self.activationButton.setText("Enabled")

            self.statusbar_activation.setText("Enabled")
            self.statusbar_activation.setStyleSheet(
                " QLabel { color: green; font-weight: bold; font-style: italic; } "
            )


def run():
    app = QtWidgets.QApplication(sys.argv)
    app.setApplicationName("Stem Reserch 2025-2026")

    window = MainWindow()
    window.show()

    app.exec()
