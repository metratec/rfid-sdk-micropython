"""_summary_
"""
import math
# type: ignore  # ignore  pylint: disable=import-error,unused-import
from reader import QRG2, RfidReaderException, UhfReaderGen2, UhfTag
from machine import UART, Pin  # type: ignore  # ignore  pylint: disable=import-error,unused-import


def config_reader(uhf_reader: UhfReaderGen2, power: int, expected_tag_size: int):
    """Print the current reader inventory

    Args:
        uhf_reader (UhfReaderGen2): the reader to use
    """
    uhf_reader.set_power(power)
    tmp = uhf_reader.get_power()
    if tmp != power:
        raise RfidReaderException("Error set power")
    uhf_reader.set_region(uhf_reader.get_region())
    value = uhf_reader.get_tag_size()
    uhf_reader.set_tag_size(value)
    value = uhf_reader.get_tag_size()
    uhf_reader.set_tag_size(expected_tag_size)


def inventory_test(uhf_reader: UhfReaderGen2):
    """Print the current reader inventory

    Args:
        uhf_reader (UhfReaderGen2): the reader to use
    """
    print("Inventory Test")
    inv: list[UhfTag] = uhf_reader.get_inventory()
    if len(inv) == 0:
        print("Please put tags on the reader")
        while len(inv) == 0:
            inv = uhf_reader.get_inventory()
    print(f"Tags found: {len(inv)}")
    for tag in inv:
        print(f" {tag.get_epc()}")


def inventory_report_test(uhf_reader: UhfReaderGen2):
    """Print the current reader inventory

    Args:
        uhf_reader (UhfReaderGen2): the reader to use
    """
    print("Inventory Test")
    inv: list[UhfTag] = uhf_reader.get_inventory_report(500)
    if len(inv) == 0:
        print("Please put tags on the reader")
        while len(inv) == 0:
            inv = uhf_reader.get_inventory_report(500)
    print(f"Tags found: {len(inv)}")
    for tag in inv:
        print(f" {tag.get_epc()} Count: {tag.get_seen_count()}")


def read_write_data(uhf_reader: UhfReaderGen2, hex_data: str):
    """Write and read the hex data to the tag

    Args:
        uhf_reader (UhfReaderGen2): reader
        hex_data (str): data as hex string
    """
    inv = uhf_reader.get_inventory()
    if len(inv) == 0:
        print("Please put a tag on the reader")
        while len(inv) == 0:
            inv = uhf_reader.get_inventory()
    tag = inv[0]
    for _ in range(3):
        inv = uhf_reader.write_tag_usr(hex_data, epc_mask=tag.get_epc())
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
        inv = uhf_reader.read_tag_usr(length=math.ceil(len(hex_data)/2), epc_mask=tag.get_epc())
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


uart0 = UART(0, baudrate=115200, tx=Pin(16), rx=Pin(17), bits=8, parity=None, stop=1, timeout=1000)
reader = QRG2(uart0)

try:
    info = reader.get_reader_info()
    print(f"Connected Reader: {info['firmware']} V{info['firmware_version']}")

    config_reader(reader, 9, 16)
    # inventory_test(reader)
    # inventory_report_test(reader)
    # read_write_data(reader, "ABCD0123")

except RfidReaderException as exc:
    print(f"Error: {exc}")
