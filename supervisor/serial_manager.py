from PyQt6.QtSerialPort import QSerialPort, QSerialPortInfo
from PyQt6.QtCore import QObject, QIODevice, pyqtSignal, pyqtSlot
from typing import List, Tuple, Optional
from enum import Enum


class SerialError(Enum):
    """Serial port error types"""
    NO_ERROR = 0
    DEVICE_NOT_FOUND = 1
    PERMISSION_DENIED = 2
    OPEN_ERROR = 3
    WRITE_ERROR = 4
    READ_ERROR = 5
    RESOURCE_ERROR = 6
    UNSUPPORTED_OPERATION = 7
    TIMEOUT = 8


class SerialConfig:
    """Configuration settings for serial communication"""
    
    def __init__(self, 
                 baud_rate: int = 9600,
                 data_bits: QSerialPort.DataBits = QSerialPort.DataBits.Data8,
                 parity: QSerialPort.Parity = QSerialPort.Parity.NoParity,
                 stop_bits: QSerialPort.StopBits = QSerialPort.StopBits.OneStop,
                 flow_control: QSerialPort.FlowControl = QSerialPort.FlowControl.NoFlowControl):
        self.baud_rate = baud_rate
        self.data_bits = data_bits
        self.parity = parity
        self.stop_bits = stop_bits
        self.flow_control = flow_control


class SerialManager(QObject):
    """
    Manages serial port communication with Arduino-style devices.
    
    Signals:
        data_received(str): Emitted when text data is received
        data_received_raw(bytes): Emitted when raw bytes are received
        connection_changed(bool): Emitted when connection status changes
        error_occurred(str): Emitted when an error occurs
    """
    
    # Signals
    data_received = pyqtSignal(str)
    data_received_raw = pyqtSignal(bytes)
    connection_changed = pyqtSignal(bool)
    error_occurred = pyqtSignal(str)
    
    def __init__(self, auto_decode: bool = True, add_newline: bool = True):
        """
        Initialize the serial manager.
        
        Args:
            auto_decode: Automatically decode received data to UTF-8 string
            add_newline: Automatically add newline to sent data (Arduino compatible)
        """
        super().__init__()
        self.serial = QSerialPort()
        self.serial.readyRead.connect(self._on_ready_read)
        self.auto_decode = auto_decode
        self.add_newline = add_newline
        self._config = SerialConfig()
        
    @staticmethod
    def get_available_ports() -> List[Tuple[str, str, str]]:
        """
        Get list of available serial ports.
        
        Returns:
            List of tuples: (port_name, description, manufacturer)
        """
        ports = []
        for port in QSerialPortInfo.availablePorts():
            ports.append((
                port.portName(),
                port.description(),
                port.manufacturer()
            ))
        return ports
    
    @staticmethod
    def find_arduino_ports() -> List[Tuple[str, str]]:
        """
        Find ports that are likely Arduino devices.
        
        Returns:
            List of tuples: (port_name, description)
        """
        arduino_ports = []
        arduino_keywords = ['Arduino', 'CH340', 'CP210', 'FTDI', 'USB Serial']
        
        for port in QSerialPortInfo.availablePorts():
            desc = port.description()
            mfg = port.manufacturer()
            
            if any(keyword.lower() in desc.lower() or 
                   keyword.lower() in mfg.lower() 
                   for keyword in arduino_keywords):
                arduino_ports.append((port.portName(), desc))
                
        return arduino_ports
    
    def configure(self, config: SerialConfig) -> None:
        """
        Configure serial port settings.
        
        Args:
            config: SerialConfig object with desired settings
        """
        self._config = config
        
    def connect(self, port_name: str, config: Optional[SerialConfig] = None) -> bool:
        """
        Connect to a serial port.
        
        Args:
            port_name: Name of the port to connect to (e.g., 'COM3', '/dev/ttyUSB0')
            config: Optional SerialConfig object (uses existing config if None)
            
        Returns:
            True if connection successful, False otherwise
        """
        if self.is_connected():
            self.disconnect()
            
        if config:
            self._config = config
            
        self.serial.setPortName(port_name)
        self.serial.setBaudRate(self._config.baud_rate)
        self.serial.setDataBits(self._config.data_bits)
        self.serial.setParity(self._config.parity)
        self.serial.setStopBits(self._config.stop_bits)
        self.serial.setFlowControl(self._config.flow_control)
        
        if self.serial.open(QIODevice.OpenModeFlag.ReadWrite):
            self.connection_changed.emit(True)
            return True
        else:
            error_msg = f"Failed to open {port_name}: {self.serial.errorString()}"
            self.error_occurred.emit(error_msg)
            return False
    
    def disconnect(self) -> None:
        """Disconnect from the serial port."""
        if self.serial.isOpen():
            self.serial.close()
            self.connection_changed.emit(False)
    
    def is_connected(self) -> bool:
        """Check if connected to a serial port."""
        return self.serial.isOpen()
    
    def send(self, data: str) -> bool:
        """
        Send string data to the serial port.
        
        Args:
            data: String data to send
            
        Returns:
            True if successful, False otherwise
        """
        if not self.is_connected():
            self.error_occurred.emit("Not connected to any port")
            return False
            
        if self.add_newline and not data.endswith('\n'):
            data += '\n'
            
        bytes_written = self.serial.write(data.encode('utf-8'))
        
        if bytes_written == -1:
            self.error_occurred.emit("Failed to write data")
            return False
            
        return True
    
    def send_bytes(self, data: bytes) -> bool:
        """
        Send raw bytes to the serial port.
        
        Args:
            data: Raw bytes to send
            
        Returns:
            True if successful, False otherwise
        """
        if not self.is_connected():
            self.error_occurred.emit("Not connected to any port")
            return False
            
        bytes_written = self.serial.write(data)
        
        if bytes_written == -1:
            self.error_occurred.emit("Failed to write data")
            return False
            
        return True
    
    def read_line(self) -> Optional[str]:
        """
        Read a line from the serial port (blocking until newline).
        
        Returns:
            String data or None if error
        """
        if not self.is_connected():
            return None
            
        if self.serial.canReadLine():
            data = self.serial.readLine()
            try:
                return bytes(data).decode('utf-8').strip()
            except UnicodeDecodeError:
                self.error_occurred.emit("Failed to decode data")
                return None
        return None
    
    def read_all(self) -> Optional[bytes]:
        """
        Read all available data from the serial port.
        
        Returns:
            Raw bytes or None if no data
        """
        if not self.is_connected():
            return None
            
        data = self.serial.readAll()
        return bytes(data) if data else None
    
    @pyqtSlot()
    def _on_ready_read(self):
        """Internal handler for incoming data."""
        if self.serial.canReadLine():
            while self.serial.canReadLine():
                data = self.serial.readLine()
                raw_bytes = bytes(data)
                
                if self.auto_decode:
                    try:
                        text = raw_bytes.decode('utf-8').strip()
                        self.data_received.emit(text)
                    except UnicodeDecodeError:
                        self.data_received_raw.emit(raw_bytes)
                else:
                    self.data_received_raw.emit(raw_bytes)
        else:
            data = self.serial.readAll()
            if data:
                raw_bytes = bytes(data)
                
                if self.auto_decode:
                    try:
                        text = raw_bytes.decode('utf-8')
                        self.data_received.emit(text)
                    except UnicodeDecodeError:
                        self.data_received_raw.emit(raw_bytes)
                else:
                    self.data_received_raw.emit(raw_bytes)
    
    def get_port_name(self) -> str:
        """Get the name of the currently connected port."""
        return self.serial.portName()
    
    def get_baud_rate(self) -> int:
        """Get the current baud rate."""
        return self.serial.baudRate()
    
    def flush(self) -> bool:
        """Flush the serial port buffers."""
        return self.serial.flush()
    
    def clear(self, directions: QSerialPort.Direction = QSerialPort.Direction.AllDirections) -> bool:
        """
        Clear the serial port buffers.
        
        Args:
            directions: Which buffers to clear (Input, Output, or AllDirections)
        """
        return self.serial.clear(directions)