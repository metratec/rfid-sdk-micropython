"""
DwarfG2 series UHF RFID Reader implementations

The DwarfG2 series includes several variants with different power capabilities
and form factors, all with single external antenna operation.

Variants:
- DwarfG2_v2: Up to 21dBm, single external antenna
- DwarfG2_Mini_v2: Up to 9dBm, compact form factor, single external antenna
- DwarfG2_XR_v2: Up to 27dBm, extended range, single external antenna

Features:
- Single external antenna operation
- Digital I/O control
- High power output options
- Compact and extended range variants

Author: neumann@metratec.com
"""

from time import time  # type: ignore  # ignore  pylint: disable=import-error,unused-import,no-name-in-module
from machine import UART  # type: ignore  # ignore  pylint: disable=import-error,unused-import

from .base import RfidReaderException, UhfTag, ExpectedReaderInfo
from .uhf_reader import UhfAtReader


@ExpectedReaderInfo("DWARFG2_v2", "DWARFG2_v2", 1.0)
class DwarfG2_v2(UhfAtReader):
    """DwarfG2_v2 UHF RFID reader with single external antenna
    
    The DwarfG2_v2 is a versatile UHF RFID module supporting up to 21dBm output 
    power with a single external antenna. It includes digital I/O control for
    integration with external systems.
    
    Specifications:
    - Output power: 0-21 dBm  
    - Antennas: 1 external
    - Interface: UART (115200 baud)
    - I/O: 4 digital outputs
    - Protocol: UHF Gen2 (ISO 18000-6C)
    """


    def get_outputs(self) -> dict[int, bool]:
        """Get current digital output pin states

        Raises:
            RfidReaderException: If reader error occurs

        Returns:
            dict[int, bool]: Output pin states (pin number -> state)
        """
        response: list[str] = self._send_command("AT+OUT?")
        # +OUT: 1,LOW
        # +OUT: 2,HIGH
        values: dict[int, bool] = {}
        for msg in response:
            values[int(msg[6])] = "HIGH" in msg[8:]
        self._config['outputs'] = values
        return values

    def set_outputs(self, outputs: dict[int, bool]) -> None:
        """Set multiple digital output pin states

        Args:
            outputs (dict[int, bool]): Pin states to set (pin number -> state)

        Raises:
            RfidReaderException: If reader error occurs
        """
        self._send_command("AT+OUT",
                           ",".join("" if x not in outputs else "HIGH" if outputs[x] else "LOW"
                                    for x in range(1, 5)))
        self._config['outputs'] = outputs

    def set_output(self, pin: int, value: bool) -> None:
        """Set a single digital output pin state

        Args:
            pin (int): Pin number (1-4)
            value (bool): Pin state (True=HIGH, False=LOW)

        Raises:
            RfidReaderException: If reader error occurs
        """
        outputs = dict(self._config.get('outputs', self.get_outputs()))
        outputs[pin] = value
        self._send_command("AT+OUT",
                           ",".join("" if x != pin else "HIGH" if value else "LOW" for x in range(1, 5)))
        self._config['outputs'] = outputs

    def get_output(self, pin: int) -> bool:
        """Get current state of a digital output pin

        Args:
            pin (int): Pin number (1-4)

        Raises:
            RfidReaderException: If pin not available or reader error occurs

        Returns:
            bool: Current pin state (True=HIGH, False=LOW)
        """
        outputs: dict[int, bool] = self.get_outputs()
        if pin in outputs:
            return outputs[pin]
        raise RfidReaderException(f"Output pin {pin} not available")


@ExpectedReaderInfo("DWARFG2-MINI_v2", "DWARFG2-MINI_v2", 1.0)
class DwarfG2_Mini_v2(DwarfG2_v2):
    """DwarfG2_Mini_v2 compact UHF RFID reader
    
    The DwarfG2-Mini_v2 is a compact variant of the DwarfG2 series with 
    reduced power output and single external antenna.
    
    Specifications:
    - Output power: 0-9 dBm
    - Antennas: 1 external
    - Form factor: Compact
    - Interface: UART (115200 baud)
    - Protocol: UHF Gen2 (ISO 18000-6C)
    """
    pass


@ExpectedReaderInfo("DWARFG2-XR_v2", "DWARFG2-XR_v2", 1.0)
class DwarfG2_XR_v2(DwarfG2_v2):
    """DwarfG2_XR_v2 extended range UHF RFID reader
    
    The DwarfG2_XR_v2 is the high-power variant of the DwarfG2 series,
    offering maximum range and performance for demanding applications.
    
    Specifications:
    - Output power: 0-27 dBm (maximum range)
    - Antennas: 1 external
    - Range: Extended
    - Interface: UART (115200 baud)
    - Protocol: UHF Gen2 (ISO 18000-6C)
    """
    pass