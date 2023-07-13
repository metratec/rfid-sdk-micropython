"""
Test class for the reader library

Copy the reader library to the device and then run the tests...
"""
import math

from reader import QRG2, RfidReaderException, UhfTag  # ignore  pylint: disable=import-error,unused-import
from machine import UART, Pin  # type: ignore  # ignore  pylint: disable=import-error,unused-import


class TestQRG2():
    """Test class for the qrg2
    """

    def __init__(self, uart: UART, power: int = 9, expected_tag_size: int = 64) -> None:
        """_summary_

        Args:
            uart (UART): reader communication interface
            power (int, optional): power value, defaults to 9.
            expected_tag_size (int, optional): expected tag size, defaults to 64.
        """
        self._reader = QRG2(uart)
        info = reader.get_reader_info()
        print(f"Connected Reader: {info['firmware']} V{info['firmware_version']}")
        self._power = power
        self._tag_size = expected_tag_size
        self._reader.set_power(self._power)
        self._reader.set_tag_size(self._tag_size)
        self._reader.reset_mask()

    def test_config(self):
        """Test the configuration parameter
        """
        for power in range(10):
            self._reader.set_power(power)
            tmp = self._reader.get_power()
            if tmp != power:
                raise RfidReaderException("Error set power")
        self._reader.set_region(self._reader.get_region())

        tag_size = self._reader.get_tag_size()
        self._reader.set_tag_size(tag_size)
        tag_size2 = self._reader.get_tag_size()
        if tag_size != tag_size2:
            raise RfidReaderException("Tag Size error")

    def test_inventory(self):
        """Print the current reader inventory

        Args:
            self._reader (UhfReaderGen2): the reader to use
        """
        print("Inventory Test")
        inv: list[UhfTag] = self._reader.get_inventory()
        if len(inv) == 0:
            print("Please put tags on the reader")
            while len(inv) == 0:
                inv = self._reader.get_inventory()
        print(f"Tags found: {len(inv)}")
        for tag in inv:
            print(f" {tag.get_epc()}")
        print("Test Mask")
        used_tag = inv[0]
        try:
            self._reader.set_mask(used_tag.get_epc())
            for _ in range(3):
                inv = self._reader.get_inventory()
                if len(inv) == 1 and inv[0].get_epc() == used_tag.get_epc():
                    break
            else:
                print("EPC mask error - Abort")
                return

            if len(used_tag.get_epc()) > 4:
                mask = used_tag.get_epc()[-4:]
                start = int(len(used_tag.get_epc()[:-4]) / 2)
            else:
                mask = used_tag.get_epc()
                start = 0
            self._reader.set_mask(mask, start)
            for _ in range(3):
                inv = self._reader.get_inventory()
                if len(inv) == 1 and inv[0].get_epc() == used_tag.get_epc():
                    break
            else:
                print("EPC mask error - Abort")
                return

            if len(used_tag.get_epc()) > 4:
                bit_mask = f"{int(used_tag.get_epc()[-4:],16):016b}"
                start = len(used_tag.get_epc()[:-4]) * 4
            else:
                bit_mask = f"{int(used_tag.get_epc(),16):b}"
                while len(bit_mask) < len(used_tag.get_epc()) * 4:
                    bit_mask = '0' + bit_mask
                start = 0

            self._reader.set_bit_mask(bit_mask, start)
            for _ in range(3):
                inv = self._reader.get_inventory()
                if len(inv) == 1 and inv[0].get_epc() == used_tag.get_epc():
                    break
            else:
                print("EPC bit mask error - Abort")
                return
        finally:
            reader.reset_mask()

    def test_inventory_report(self):
        """Print the current reader inventory

        Args:
            self._reader (UhfReaderGen2): the reader to use
        """
        print("Inventory Test")
        inv: list[UhfTag] = self._reader.get_inventory_report(500)
        if len(inv) == 0:
            print("Please put tags on the reader")
            while len(inv) == 0:
                inv = self._reader.get_inventory_report(500)
        print(f"Tags found: {len(inv)}")
        for tag in inv:
            print(f" {tag.get_epc()} Count: {tag.get_seen_count()}")

    def _wait_for_tag(self):
        inv = self._reader.get_inventory()
        if len(inv) == 0:
            print("Please put a tag on the reader")
            while len(inv) == 0:
                inv = self._reader.get_inventory()
        return inv[0]

    def test_read_write_data(self, hex_data: str):
        """Write and read the hex data to the tag

        Args:
            self._reader (UhfReaderGen2): reader
            hex_data (str): data as hex string
        """
        tag = self._wait_for_tag()
        for _ in range(3):
            inv = self._reader.write_tag_usr(hex_data, epc_mask=tag.get_epc())
            if len(inv) == 0:
                continue
            if inv[0].has_error():
                print(f"Error during write data: {inv[0].get_error_message()}")
                continue
            tag = inv[0]
            print("Data written!")
            break
        else:
            print("Error write data to the tag - abort")
            return

        for _ in range(3):
            inv = self._reader.read_tag_usr(length=math.ceil(len(hex_data)/2), epc_mask=tag.get_epc())
            if len(inv) == 0:
                continue
            if inv[0].has_error():
                print(f"Error during read data: {inv[0].get_error_message()}")
                continue
            tag = inv[0]
            print(f"Data read: {tag.get_data()}")
            break
        else:
            print("Error read data from the tag - abort")
            return

    def test_write_epc(self, new_epc: str):
        """Test the write epc method

        Args:
            new_epc (str): the new epc
        """
        used_tag = self._wait_for_tag()
        inv = self._reader.write_tag_epc(new_epc=new_epc, tid=used_tag.get_tid())
        for tag in inv:
            print(f"EPC written: {tag}")
        if len(inv) == 1:
            if inv[0].get_epc() == new_epc:
                print("New epc written")
            else:
                print(f"Error write epc: {inv[0].get_error_message()}")
        else:
            print("No tag epc written")

    def test_lock_tag(self, password: str):
        """Test the lock methods

        Args:
            passwort (str): the lock password
        """
        password_to_use = password
        if password_to_use == '00000000':
            password_to_use = '12345678'

        used_tag = self._wait_for_tag()
        if password_to_use != password:
            inv = self._reader.set_lock_password(password, password_to_use, epc_mask=used_tag.get_epc())
            if len(inv) == 0 or inv[0].has_error():
                print(f"Error update lock password: {inv[0].get_error_message()}")
                return
        for _ in range(3):
            inv = self._reader.lock_user_memory(password_to_use, epc_mask=used_tag.get_epc())
            if len(inv) == 0:
                continue
            if inv[0].has_error():
                print(f"Error during set lock: {inv[0].get_error_message()}")
                continue
            print("USR data locked")
            break
        else:
            print("Error set use lock - abort")
            return
        print("Try write usr data")
        for _ in range(3):
            inv = self._reader.write_tag_usr("0000", epc_mask=used_tag.get_epc())
            if len(inv) == 0:
                continue
            if inv[0].has_error():
                print(f"Data can not written: {inv[0].get_error_message()} - Lock OK")
            else:
                print("Data are written! Lock not working!")
                return
            break
        else:
            print("Error write data - abort")
            return
        print("Unlock tag....")
        for _ in range(3):
            inv = self._reader.unlock_user_memory(password_to_use, epc_mask=used_tag.get_epc())
            if len(inv) == 0:
                continue
            if inv[0].has_error():
                print(f"Error during unlock: {inv[0].get_error_message()}")
                continue
            print("USR data unlocked")
            break
        else:
            print("Error unlock usr data - abort")
            return
        if password_to_use != password:
            inv = self._reader.set_lock_password(password_to_use, password, epc_mask=used_tag.get_epc())
            if len(inv) == 0 or inv[0].has_error():
                print(f"Error reset lock password: {inv[0].get_error_message()}")
                return


uart0 = UART(0, baudrate=115200, tx=Pin(16), rx=Pin(17), bits=8, parity=None, stop=1, timeout=1000)
reader = QRG2(uart0)

try:
    test = TestQRG2(uart0)
    # test.test_config()
    # test.test_inventory()
    # test.test_inventory_report()
    # test.test_read_write_data("ABCD0123")
    # test.test_write_epc("ABCD12345678")
    test.test_lock_tag('00000000')

except RfidReaderException as exc:
    print(f"Error: {exc}")
