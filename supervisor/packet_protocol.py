import struct
from enum import IntEnum
from typing import Any
from PyQt6.QtCore import QObject, pyqtSignal

from serial_manager import SerialManager


class PacketType(IntEnum):
    """Packet type identifiers"""

    # Bidirectional packets
    PING = 0x01  # Ping (Do you hear me?)
    PONG = 0x02  # Pong (I hear you!)
    ACK = 0x03  # Acknowledge (Understood)
    NACK = 0x03  # Negative Acknowledge (I don't understand)

    # Supervisor -> Executor (Commands)
    CMD_SET_MODE = 0x10  # Set operating mode
    CMD_SET_PARAM = 0x11  # Set a parameter
    CMD_START = 0x12
    CMD_STOP = 0x13
    CMD_RESET = 0x14
    CMD_READ_SENSOR = 0x15  # Request sensor data

    # Executor -> Supervisor (Data/Status)
    STATUS_UPDATE = 0x20  # Status update
    SENSOR_DATA = 0x21  # Sensor data response
    ERROR_REPORT = 0x22  # Error report
    DEBUG_MESSAGE = 0x23  # Debug message


class PacketProtocol:
    """
    Binary packet protocol with the following structure:

    [START_BYTE] [TYPE] [LENGTH] [PAYLOAD...] [CHECKSUM]

    - START_BYTE: 0xAA (1 byte) - packet delimiter
    - TYPE: PacketType (1 byte) - packet identifier
    - LENGTH: payload length (1 byte) - 0-255 bytes
    - PAYLOAD: variable length data
    - CHECKSUM: XOR of all bytes except START_BYTE (1 byte)
    """

    START_BYTE: int = 0xAA
    MIN_PACKET_SIZE: int = 4  # START + TYPE + LENGTH + CHECKSUM
    MAX_PAYLOAD_SIZE: int = 255

    @staticmethod
    def create_packet(packet_type: PacketType, payload: bytes = b"") -> bytes:
        """
        Create a packet from type and payload.

        Args:
            packet_type: Type of packet
            payload: Payload data (max 255 bytes)

        Returns:
            Complete packet as bytes
        """
        if len(payload) > PacketProtocol.MAX_PAYLOAD_SIZE:
            raise ValueError(
                f"Payload too large: {len(payload)} > {PacketProtocol.MAX_PAYLOAD_SIZE}"
            )

        # Build packet
        packet = bytearray()
        packet.append(PacketProtocol.START_BYTE)
        packet.append(packet_type)
        packet.append(len(payload))
        packet.extend(payload)

        # Calculate checksum (XOR of TYPE + LENGTH + PAYLOAD)
        checksum = 0
        for byte in packet[1:]:  # Skip START_BYTE
            checksum ^= byte
        packet.append(checksum)

        return bytes(packet)

    @staticmethod
    def validate_packet(packet: bytes) -> bool:
        """
        Validate packet structure and checksum.

        Args:
            packet: Complete packet bytes

        Returns:
            True if valid, False otherwise
        """
        if len(packet) < PacketProtocol.MIN_PACKET_SIZE:
            return False

        if packet[0] != PacketProtocol.START_BYTE:
            return False

        payload_length = packet[2]
        expected_length = PacketProtocol.MIN_PACKET_SIZE + payload_length

        if len(packet) != expected_length:
            return False

        # Verify checksum
        checksum = 0
        for byte in packet[1:-1]:  # Skip START_BYTE and CHECKSUM
            checksum ^= byte

        return checksum == packet[-1]

    @staticmethod
    def parse_packet(packet: bytes) -> tuple[PacketType, bytes] | None:
        """
        Parse a validated packet.

        Args:
            packet: Complete packet bytes

        Returns:
            Tuple of (packet_type, payload) or None if invalid
        """
        if not PacketProtocol.validate_packet(packet):
            return None

        packet_type = PacketType(packet[1])
        payload_length = packet[2]

        if payload_length > 0:
            payload = packet[3 : 3 + payload_length]
        else:
            payload = b""

        return (packet_type, payload)


class PacketBuilder:
    """Helper class to build common packet types"""

    @staticmethod
    def ping() -> bytes:
        """Create a PING packet"""
        return PacketProtocol.create_packet(PacketType.PING)

    @staticmethod
    def pong() -> bytes:
        """Create a PONG packet"""
        return PacketProtocol.create_packet(PacketType.PONG)

    @staticmethod
    def ack(sequence_num: int = 0) -> bytes:
        """Create an ACK packet with optional sequence number"""
        payload = struct.pack("B", sequence_num)
        return PacketProtocol.create_packet(PacketType.ACK, payload)

    @staticmethod
    def nack(error_code: int = 0) -> bytes:
        """Create a NACK packet with error code"""
        payload = struct.pack("B", error_code)
        return PacketProtocol.create_packet(PacketType.NACK, payload)

    @staticmethod
    def set_mode(mode: int) -> bytes:
        """Set operating mode (0-255)"""
        payload = struct.pack("B", mode)
        return PacketProtocol.create_packet(PacketType.CMD_SET_MODE, payload)

    @staticmethod
    def set_param(param_id: int, value: int) -> bytes:
        """Set a parameter (param_id: 0-255, value: 32-bit int)"""
        payload = struct.pack("Bi", param_id, value)
        return PacketProtocol.create_packet(PacketType.CMD_SET_PARAM, payload)

    @staticmethod
    def set_param_float(param_id: int, value: float) -> bytes:
        """Set a parameter with float value"""
        payload = struct.pack("Bf", param_id, value)
        return PacketProtocol.create_packet(PacketType.CMD_SET_PARAM, payload)

    @staticmethod
    def start() -> bytes:
        """Create START command"""
        return PacketProtocol.create_packet(PacketType.CMD_START)

    @staticmethod
    def stop() -> bytes:
        """Create STOP command"""
        return PacketProtocol.create_packet(PacketType.CMD_STOP)

    @staticmethod
    def reset() -> bytes:
        """Create RESET command"""
        return PacketProtocol.create_packet(PacketType.CMD_RESET)

    @staticmethod
    def read_sensor(sensor_id: int) -> bytes:
        """Request sensor reading"""
        payload = struct.pack("B", sensor_id)
        return PacketProtocol.create_packet(PacketType.CMD_READ_SENSOR, payload)


class PacketParser:
    """Helper class to parse common packet payloads"""

    @staticmethod
    def parse_status_update(payload: bytes) -> dict[str, Any]:
        """Parse status update payload (example: mode, state, uptime)"""
        if len(payload) >= 6:
            mode, state, uptime = struct.unpack("BBI", payload[:6])
            return {"mode": mode, "state": state, "uptime_ms": uptime}
        return {}

    @staticmethod
    def parse_sensor_data(payload: bytes) -> dict[str, Any]:
        """Parse sensor data (example: sensor_id, value as float)"""
        if len(payload) >= 5:
            sensor_id, value = struct.unpack("Bf", payload[:5])
            return {"sensor_id": sensor_id, "value": value}
        return {}

    @staticmethod
    def parse_error_report(payload: bytes) -> dict[str, Any]:
        """Parse error report (error code and optional data)"""
        if len(payload) >= 1:
            error_code = struct.unpack("B", payload[:1])[0]
            error_data = payload[1:] if len(payload) > 1 else b""
            return {"error_code": error_code, "error_data": error_data}
        return {}

    @staticmethod
    def parse_ack(payload: bytes) -> int:
        """Parse ACK sequence number"""
        if len(payload) >= 1:
            return struct.unpack("B", payload[:1])[0]
        return 0


class PacketStream(QObject):
    """
    Handles packet streaming over serial connection.
    Assembles incoming bytes into complete packets.
    """

    # Signals
    packet_received: pyqtSignal = pyqtSignal(int, bytes)  # (packet_type, payload)
    packet_sent: pyqtSignal = pyqtSignal(int)  # (packet_type)
    error_occurred: pyqtSignal = pyqtSignal(str)  # (error_message)

    def __init__(self, serial_manager: SerialManager):
        super().__init__()
        self.serial_mgr: SerialManager = serial_manager
        self.buffer: bytearray = bytearray()

        # Connect to raw data signal
        _ = self.serial_mgr.data_received_raw.connect(self.on_data_received)

        # Statistics
        self.packets_sent: int = 0
        self.packets_received: int = 0
        self.packets_invalid: int = 0

    def on_data_received(self, data: bytes):
        """Process incoming raw data and extract packets"""
        self.buffer.extend(data)
        self._process_buffer()

    def _process_buffer(self):
        """Extract complete packets from buffer"""
        while len(self.buffer) >= PacketProtocol.MIN_PACKET_SIZE:
            # Find start byte
            start_idx = self.buffer.find(PacketProtocol.START_BYTE)

            if start_idx == -1:
                # No start byte found, clear buffer
                self.buffer.clear()
                return

            if start_idx > 0:
                # Remove data before start byte
                self.buffer = self.buffer[start_idx:]

            # Check if we have enough data for header
            if len(self.buffer) < 3:
                return  # Wait for more data

            # Get payload length
            payload_length = self.buffer[2]
            packet_length = PacketProtocol.MIN_PACKET_SIZE + payload_length

            # Check if complete packet is available
            if len(self.buffer) < packet_length:
                return  # Wait for more data

            # Extract packet
            packet = bytes(self.buffer[:packet_length])
            self.buffer = self.buffer[packet_length:]

            # Parse and emit
            result = PacketProtocol.parse_packet(packet)
            if result:
                packet_type, payload = result
                self.packets_received += 1
                self.packet_received.emit(packet_type, payload)
            else:
                self.packets_invalid += 1
                self.error_occurred.emit(f"Invalid packet received: {packet.hex()}")

    def send_packet(self, packet_type: PacketType, payload: bytes = b"") -> bool:
        """Send a packet"""
        try:
            packet = PacketProtocol.create_packet(packet_type, payload)
            success = self.serial_mgr.send_bytes(packet)
            if success:
                self.packets_sent += 1
                self.packet_sent.emit(packet_type)
            return success
        except Exception as e:
            self.error_occurred.emit(f"Failed to send packet: {str(e)}")
            return False

    def get_statistics(self) -> dict[str, int]:
        """Get packet statistics"""
        return {
            "sent": self.packets_sent,
            "received": self.packets_received,
            "invalid": self.packets_invalid,
        }

    def clear_buffer(self):
        """Clear the receive buffer"""
        self.buffer.clear()
