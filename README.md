# Metratec RFID Reader SDK for MicroPython

With the Metratec RFID Reader SDK for MicroPython you can easily integrate Metratec RFID OEM reader modules into your MicroPython project and communicate with RFID transponders without having to know the reader protocol.

## Supported Products

This SDK supports the following Metratec OEM modules:

| Module | Max Power | Antennas | Region | Description |
|--------|-----------|----------|---------|-------------|
| QRG2_ETSI | 9 dBm | 1 (integrated) | ETSI only | European variant with region validation |
| QRG2_FCC | 9 dBm | 1 (integrated) | FCC only | North American variant with region validation |
| DwarfG2-Mini v2 | 9 dBm | 1 (external) | Universal | Compact module with external antenna and low output |
| DwarfG2 v2 | 21 dBm | 1 (external) | Universal | Compact module with external antenna and medium output |
| DwarfG2_XR v2 | 27 dBm | 1 (external) | Universal | Compact module with external antenna and higher output |


## Requirements

The Metratec Reader must be connected to the controller via a UART.

## Installation

To use the a Metratec RFID reader in your MicroPython project, simply copy the metratec_rfid_lib.py file to your controller and change according to your hardware.

## Usage Examples

### Basic Inventory (QRG2_ETSI)

```python
from machine import UART, Pin
from metratec_rfid_lib import QRG2_ETSI, RfidReaderException, UhfTag

# Define UART connection
uart0 = UART(0, tx=Pin(16), rx=Pin(17))  # check pin assignment with your hardware/board

try:
    # Create reader instance (ETSI variant)
    reader = QRG2_ETSI(uart0)
    
    # Set power level (0-9 for QRG2)
    reader.set_power(9)
    
    # Set region (ETSI only for this variant)
    reader.set_region("ETSI")
    
    # Get inventory
    tags: list[UhfTag] = reader.get_inventory()
    print(f"Tags found: {len(tags)}")
    for tag in tags:
        print(f"EPC: {tag.get_epc()}")
        print(f"TID: {tag.get_tid()}")
        print(f"RSSI: {tag.get_rssi()}")
        
except RfidReaderException as exc:
    print(f"Error: {exc}")
```


### Medium Power Operation (DwarfG2 v2)

```python
from machine import UART, Pin
from metratec_rfid_lib import DwarfG2_v2, RfidReaderException

uart0 = UART(0, tx=Pin(16), rx=Pin(17))  # check pin assignment with your hardware/board

try:
    reader = DwarfG2_v2(uart0)
    
    # Set high power level (up to 21 dBm)
    reader.set_power(21)
    
    # Configure RF mode for optimal performance
    reader.set_rf_mode(285)  # Sensitivity mode
    
    # Get inventory with high power
    tags = reader.get_inventory()
    print(f"Found {len(tags)} tags with high power")
    
except RfidReaderException as exc:
    print(f"Error: {exc}")
```

### Reading and Writing Tag Data

```python
# Read user memory from tag
try:
    # Read 4 bytes from user memory starting at byte 0
    tags = reader.read_tag_usr(length=4, start=0)
    for tag in tags:
        if not tag.has_error():
            print(f"Data: {tag.get_data()}")
        else:
            print(f"Error: {tag.get_error_message()}")
            
    # Write data to user memory
    hex_data = "DEADBEEF"
    tags = reader.write_tag_usr(hex_data)
    for tag in tags:
        if tag.has_error():
            print(f"Write failed: {tag.get_error_message()}")
        else:
            print("Write successful")
            
except RfidReaderException as exc:
    print(f"Error: {exc}")
```

### Advanced Configuration

```python
try:
    reader = QRG2_ETSI(uart0)
    
    # Set RF mode for optimal performance
    reader.set_rf_mode(285)  # Sensitivity mode
    
    # Configure region (ETSI only for this variant)
    reader.set_region("ETSI")
    
    # Set inventory settings (ONT, RSSI, TID, FastStart, Phase)
    reader.set_inventory_settings(False, True, True, False, False)
    
    # Use inventory report for multiple reads
    tags = reader.get_inventory_report(duration=500)  # 500ms scan
    
except RfidReaderException as exc:
    print(f"Error: {exc}")
```

## Troubleshooting

**Common Issues:**

1. **No tags found**: Check antenna connection and increase power level
2. **Communication errors**: Verify UART pins and baud rate (115200)
3. **Inconsistent reads**: Try different RF modes or adjust power levels or Q value
4. **Memory errors**: Ensure tag supports the memory bank you're accessing

**Error Handling:**

All reader operations can throw `RfidReaderException`. Always wrap reader calls in try-catch blocks for robust error handling.
