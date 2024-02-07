# Metratec RFID Reader SDK for MicroPython

With the Metratec RFID Reader SDK for MicroPython you can easily integrate Metratec RFID OEM reader modules into your MicroPython project and communicate with RFID transponders without having to know the reader protocol.

## Supported Products

This SDK supports the following Metratec OEM modules:

* QRG2
* DwarfG2-Mini (v2)
* DwarfG2 (v2)

## Requirements

The Metratec Reader must be connected to the controller via a UART.

## Installation

To use the a Metratec RFID reader in your MicroPython project, simply copy the metratec_rfid_lib.py file to your controller and change according to your hardware.

## Example Usage (for QRG2)

To use the QRG2 reader with your project, create a new QRG2 reader instance and define the connected UART. Then you can get the current inventory, read or write the transponder data.

Sample Code:

```python
from machine import UART, Pin
from metratec_rfid_lib import QRG2, RfidReaderException, UhfTag

# define the used uart
uart0 = UART(0, tx=Pin(1), rx=Pin(2))
try:
    # create the reader instance
    reader = QRG2(uart0)

    # get and print the current inventory
    inv: list[UhfTag] = reader.get_inventory()
    print(f"Tags found: {len(inv)}")
    for tag in inv:
        print(f" {tag.get_epc()}")
except RfidReaderException as exc:
    print(f"Error: {exc}")
```

