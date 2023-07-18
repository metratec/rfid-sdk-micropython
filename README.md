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

## License

MIT License

Copyright (c) 2023 metratec GmbH

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
