import serial.tools.list_ports
from serial.tools.list_ports_common import ListPortInfo


def search_ports() -> list[ListPortInfo]:
    ports = [
        i
        for i in serial.tools.list_ports.comports()
        # if i.product != "n/a" and i.product is not None
    ]
    return ports
