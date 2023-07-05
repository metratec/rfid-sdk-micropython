"""
metratec rfid reader base class
"""

from time import ticks_ms  # type: ignore  # ignore  pylint: disable=import-error,unused-import,no-name-in-module
from machine import UART, Pin  # type: ignore  # ignore  pylint: disable=import-error,unused-import


class RfidReaderException(Exception):
    """
    Exception class for the metratec rfid reader
    """

    def __init__(self, message) -> None:
        # disable 'Useless super delegation' warning - pylint: disable=W0235
        super().__init__(message)


class ExpectedReaderInfo():
    """Expected reader info decorator
    """
    # disable Too few public methods warning - pylint: disable=R0903

    def __init__(self, firmware_name: str, hardware_name: str, min_firmware: float) -> None:
        """_summary_

        Args:
            firmware_name (str): firmware name
            hardware_name (str): hardware name
            min_firmware (str): minimum required firmware version
        """
        self._firmware_name = firmware_name
        self._hardware_name = hardware_name
        self._min_firmware = min_firmware

    def __call__(self, clazz):
        """
        Adds the property to the class properties field.
        Creates the field if needed.

        :param clazz: The class to decorate
        :return: The decorated class
        """
        properties = getattr(clazz, "_expected_reader", None)
        if not properties:
            properties = {}
            setattr(clazz, "_expected_reader", properties)
        properties["firmware_name"] = self._firmware_name
        properties["hardware_name"] = self._hardware_name
        properties["min_firmware"] = self._min_firmware
        return clazz


class RfidReaderGen2():
    """The base implementation of a rfid reader
    """

    def __init__(self, uart: UART):
        self._uart = uart
        self._initialise()

    def _prepare_command(self, command: str, *parameters) -> str:
        # prepare the command with the AT protocol style
        if not parameters:
            return command
        return command + "=" + ",".join(str(x) for x in parameters if x is not None)

    def _send_command(self, command: str, *parameters, timeout: int = 2000) -> list[str]:
        send_command = self._prepare_command(command, *parameters)
        self._uart.write(send_command + '\r')
        max_time = ticks_ms() + timeout
        response: str = ""
        while True:
            resp = self._uart.readline()
            if resp is None:
                break
            resp = resp.decode()
            print(f"recv: {resp}")
            if resp == 'OK\r\n':
                return response.split("\r") if response else [""]
            if resp == 'ERROR\r\n':
                try:
                    msg = response[response.rindex(
                        "<")+1:response.rindex(">")]
                except ValueError:
                    msg = response
                raise RfidReaderException(str(msg))
            response = resp
            if max_time <= ticks_ms():
                break
        if not response:
            raise RfidReaderException(f"no reader response for command {send_command}")
        raise RfidReaderException(f"wrong response for command {send_command} - {str(response)}")

    def _initialise(self):
        """Initialise and prepare the reader
        """

    def get_reader_info(self) -> dict[str, str]:
        """Returns the reader information

        Raises:
            RfidReaderException: if an reader error occurs

        Returns:
            dict: With the 'firmware', 'firmware_version', 'hardware', 'hardware_version'
                  and 'serial_number' information
        """
        command: str = "ATI"
        response: list[str] = self._send_command(command)
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
                'serial_number': serial[1]}
            expected = getattr(self, "_expected_reader", {})
            if info['hardware'] != expected.get('hardware_name', 'unknown'):
                raise RfidReaderException(
                    f"Wrong reader type! {expected.get('hardware_name','unknown')} expected, {info['hardware']} found")
            if info['firmware'] != expected.get('firmware_name', 'unknown'):
                raise RfidReaderException(f"Wrong reader firmware! {expected.get('firmware_name','unknown')} expected" +
                                          f", {info['firmware']} found")
            firmware_version = float(f"{info['firmware_version'][0:2]}.{info['firmware_version'][2:4]}")
            if firmware_version > expected.get('min_firmware', 1.0):
                raise RfidReaderException("Reader firmware too low, please update! " +
                                          f"Minimum {expected.get('min_firmware')} expected, {firmware_version} found")
            return info
        except IndexError as exc:
            raise RfidReaderException(
                f"Wrong reader - Not expected info response - {response}") from exc


class HfReaderGen2(RfidReaderGen2):
    """The implementation of the uhf gen2 reader with the **AT-protocol.**
    """

    def __init__(self, uart: UART):
        super().__init__(uart)

    def _initialise(self):
        self._send_command('ATE0')
        try:
            self._send_command('AT+BINV')
        except RfidReaderException:
            pass
        try:
            self._send_command('AT+BINVR')
        except RfidReaderException:
            pass
        return super()._initialise()


@ExpectedReaderInfo("QRG2", "QRG2", 1.3)
class QRG2(HfReaderGen2):
    """The QRG2 is the first UHF RFID module that integrates all necessary components (read/write and antenna)
    into a single product. Just place the module in your machine and start using UHF RFID. This gives you the
    advantage of cheaper UHF transponders and longer read ranges at a price comparable to HF RFID systems.
    """

    def __init__(self, uart: UART):
        super().__init__(uart)


uart0 = UART(0, baudrate=115200, tx=Pin(16), rx=Pin(17), bits=8, parity=None, stop=1, timeout=1000)
reader = QRG2(uart0)

try:
    print("Get Reader Info: ")
    print(reader.get_reader_info())
except RfidReaderException as err:
    print(f"Error: {err}")
