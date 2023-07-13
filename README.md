# Metratec Reader Library for MicroPython

With the Metratec Reader Library for MicroPython you can easily integrate Metratec RFID readers into your MicroPython project and communicate with RFID transponders without having to know the reader protocol.

## Requirements

The Metratec Reader must be connected to the controller via a UART.

## Installation

To use the Metratec QRG2 reader in your MicroPython project, simply copy the metratec_reader.py file to your controller.

## Usage

To use the QRG2 reader with your project, create a new QRG2 reader instance and define the connected UART. Then you can get the current inventory, read or write the transponder data.

Sample Code:

```python
from machine import UART, Pin
from reader import QRG2, RfidReaderException, UhfTag

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
