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
