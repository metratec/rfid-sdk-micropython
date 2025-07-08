from machine import UART, Pin
# Import from metratec_rfid package (copy metratec_rfid/ folder to device)
# OR copy metratec_rfid_lib.py as reader.py for single-file usage
try:
    from metratec_rfid import QRG2_ETSI, RfidReaderException, UhfTag
except ImportError:
    # Fallback to single-file import for backward compatibility
    from reader import RfidReaderException, UhfTag
    # Note: Regional variants not available in single-file mode

# define the used uart
uart0 = UART(0, tx=Pin(1), rx=Pin(2))
try:
    # create the reader instance (ETSI variant)
    if 'QRG2_ETSI' in globals():
        reader = QRG2_ETSI(uart0)
    else:
        print("Regional variants not available in single-file mode")
        print("Use package mode (copy metratec_rfid/ folder) for regional variants")
        exit()

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
