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

        # Connect to serial port
        serial_mgr.connect("COM3", SerialConfig(baud_rate=115200))

        # Send packets
        packet_stream.send_packet(PacketType.PING)
        packet_stream.send_packet(PacketType.CMD_SET_MODE, struct.pack("B", 1))
        packet_stream.send_packet(PacketType.CMD_START)

    def mcu_connect_btn(self):
        pass

    def on_packet_received(self, packet_type: PacketType, payload: bytes):
        """
        Run every time a packet is revievd from the MCU
        """
        print(f"Received packet type {packet_type}: {payload.hex()}")

        if packet_type == PacketType.SENSOR_DATA:
            data = PacketParser.parse_sensor_data(payload)
            print(f"Sensor {data['sensor_id']}: {data['value']}")

        elif packet_type == PacketType.PONG:
            print("PONG received!")


app = QtWidgets.QApplication(sys.argv)

window = MainWindow()
window.show()

app.exec()
