"""
AT Protocol implementation for Metratec RFID readers

This module implements the low-level AT protocol communication layer
used by all current Metratec RFID readers (2023+). The protocol follows
standard AT command conventions similar to LTE modems.

Author: neumann@metratec.com
"""

from time import ticks_ms  # type: ignore  # ignore  pylint: disable=import-error,unused-import,no-name-in-module
from machine import UART  # type: ignore  # ignore  pylint: disable=import-error,unused-import

from .base import RfidReaderException


class RfidReaderAt():
    """Base implementation of AT protocol for Metratec RFID readers
    
    This class implements the core AT protocol communication layer that follows
    standard AT command conventions similar to LTE modems. All Metratec RFID
    products from 2023 onwards use this human-readable ASCII protocol.
    
    Protocol Format:
    - Commands end with Carriage Return (CR, 0x0D)
    - Responses are framed by CR+LF (0x0D+0x0A)
    - Multi-line responses use prefixes like +INV:, +PWR:, etc.
    - Status codes: OK (success) or ERROR (failure)
    - Error messages in format: <Error Message>
    """

    def __init__(self, uart: UART):
        """Initialize AT protocol reader with UART interface
        
        Args:
            uart (UART): Configured UART interface for communication
        """
        self._uart = uart
        self._config: dict = {}  # Cache for reader configuration
        self._initialise()

    def _prepare_command(self, command: str, *parameters) -> str:
        """Format AT command with parameters according to protocol
        
        Converts command and parameters into AT protocol format.
        Example: AT+PWR + (9,) -> "AT+PWR=9"
        
        Args:
            command (str): AT command (e.g., "AT+PWR")
            *parameters: Command parameters (filtered for None values)
            
        Returns:
            str: Formatted AT command string
        """
        if not parameters:
            return command
        return command + "=" + ",".join(str(x) for x in parameters if x is not None)

    def _send_command(self, command: str, *parameters, timeout: int = 2000) -> list[str]:
        """Send AT command and parse response according to protocol
        
        Implements the complete AT protocol communication cycle:
        1. Format and send command with CR terminator
        2. Read response lines until OK/ERROR status
        3. Parse and return data lines or raise exception on error
        
        Args:
            command (str): AT command to send
            *parameters: Command parameters
            timeout (int): Communication timeout in milliseconds (default: 2000)
            
        Returns:
            list[str]: Response data lines (without status codes)
            
        Raises:
            RfidReaderException: On communication timeout or command error
        """
        send_command = self._prepare_command(command, *parameters)
        
        # Send command with CR terminator as per AT protocol
        self._uart.write((send_command + '\r').encode())
        max_time = ticks_ms() + timeout
        response: str = ""
        
        # Read response lines until status code received
        while True:
            resp = self._uart.readline()
            
            # Handle timeout case
            if resp is None:
                if max_time <= ticks_ms():
                    break
                else:
                    continue
                    
            # Remove CR+LF terminator (last 2 bytes)
            resp = resp[:-2]
            if not resp:
                continue
                
            resp = resp.decode()
            
            # Check for status codes
            if resp == 'OK':
                # Return parsed response lines (split by CR)
                return response.split("\r") if response else [""]
            if resp == 'ERROR':
                # Extract error message from <Error Message> format
                try:
                    msg = response[response.rindex("<")+1:response.rindex(">")]
                except ValueError:
                    msg = response
                raise RfidReaderException(str(msg))
                
            # Accumulate response data
            response = resp

        if not response:
            raise RfidReaderException(f"no reader response for command {send_command}")
        raise RfidReaderException(f"wrong response for command {send_command} - {str(response)}")

    def _initialise(self):
        """Initialize and prepare the reader for communication
        
        Sets up UART parameters and disables command echo for clean communication.
        """
        self._uart.init(baudrate=115200, bits=8, parity=None, stop=1, timeout=500)
        self._send_command('ATE0')  # Disable command echo

    def get_reader_info(self) -> dict[str, str]:
        """Get reader hardware and firmware information
        
        Queries the reader for its identification information and validates
        it against expected values if the reader class has expected info.

        Raises:
            RfidReaderException: If reader error occurs or info doesn't match expected values

        Returns:
            dict: Reader information with keys:
                - 'firmware': Firmware name
                - 'firmware_version': Firmware version 
                - 'hardware': Hardware name
                - 'hardware_version': Hardware version
                - 'serial_number': Device serial number
        """
        command: str = "ATI"
        response: list[str] = self._send_command(command)
        
        # Example response:
        # +SW: PULSAR_LR 0100
        # +HW: PULSAR_LR 0100  
        # +SERIAL: 2020090817420000
        try:
            firmware: list[str] = response[0].split(" ")
            hardware: list[str] = response[1].split(" ")
            serial: list[str] = response[2].split(" ")
            
            info: dict[str, str] = {
                'firmware': firmware[1],
                'firmware_version': firmware[2],
                'hardware': hardware[1],
                'hardware_version': hardware[2],
                'serial_number': serial[1]
            }
            
            # Validate against expected reader info if available
            expected = getattr(self, "_expected_reader", {})
            if info['hardware'] != expected.get('hardware_name', 'unknown'):
                raise RfidReaderException(
                    f"Wrong reader type! {expected.get('hardware_name','unknown')} expected, {info['hardware']} found")
            if info['firmware'] != expected.get('firmware_name', 'unknown'):
                raise RfidReaderException(f"Wrong reader firmware! {expected.get('firmware_name','unknown')} expected" +
                                          f", {info['firmware']} found")
            
            # Check minimum firmware version
            firmware_version = float(f"{info['firmware_version'][0:2]}.{info['firmware_version'][2:4]}")
            if firmware_version < expected.get('min_firmware', 1.0):
                raise RfidReaderException("Reader firmware too low, please update! " +
                                          f"Minimum {expected.get('min_firmware')} expected, {firmware_version} found")
            return info
            
        except IndexError as err:
            raise RfidReaderException(
                f"Wrong reader - Not expected info response - {response}") from err