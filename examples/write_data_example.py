from machine import UART, Pin
from reader import QRG2, RfidReaderException, UhfTag

# define the used uart
uart0 = UART(0, tx=Pin(1), rx=Pin(2))
try:
    # create the reader instance
    reader = QRG2(uart0)

    # get and print the current inventory
    inv: list[UhfTag] = reader.write_tag_usr(start=0, data='ABCD')
    print(f"Tags processed: {len(inv)}")
    for tag in inv:
        if not tag.has_error():
            print(f" {tag.get_epc()}: Data written")
        else:
            print(f" {tag.get_epc()}: Error write data - {tag.get_error_message()}")

except RfidReaderException as exc:
    print(f"Error: {exc}")
