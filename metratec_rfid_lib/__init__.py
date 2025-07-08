"""
Metratec RFID Reader SDK for MicroPython

This package provides a comprehensive interface for communicating with Metratec UHF RFID readers
using the AT protocol. It supports various Metratec OEM modules including QRG2, DwarfG2 series,
and DwarfG2_XR variants.

Key Features:
- AT protocol implementation for UART communication
- Support for multiple reader types with different power capabilities
- Tag inventory, reading, and writing operations
- Multi-antenna support for advanced readers
- Comprehensive error handling and validation
- RF mode configuration for optimal performance

Supported Readers:
- QRG2_ETSI: 9dBm, integrated antenna (ETSI region only)
- QRG2_FCC: 9dBm, integrated antenna (FCC region only)
- DwarfG2-Mini v2: 9dBm, 1 external antenna  
- DwarfG2 v2: 21dBm, 1 external antenna
- DwarfG2_XR v2: 27dBm, 1 external antenna

Usage:
    from metratec_rfid import QRG2_ETSI, RfidReaderException, UhfTag
    from machine import UART, Pin
    
    uart = UART(0, tx=Pin(1), rx=Pin(2))
    reader = QRG2_ETSI(uart)
    reader.set_region("ETSI")
    tags = reader.get_inventory()

Author: info@metratec.com
Version: 2.0.0
"""

# Import all public classes and exceptions for backward compatibility
from .base import (
    RfidReaderException,
    Tag,
    UhfTag,
    ExpectedReaderInfo,
    __version__,
    __version_info__,
    __author__
)

from .at_protocol import RfidReaderAt
from .uhf_reader import UhfAtReader
from .qrg2 import QRG2_ETSI, QRG2_FCC
from .dwarfg2 import DwarfG2_v2, DwarfG2_Mini_v2, DwarfG2_XR_v2

# Define what gets imported with "from metratec_rfid import *"
__all__ = [
    # Exception classes
    'RfidReaderException',
    
    # Tag classes
    'Tag',
    'UhfTag',
    
    # Base reader classes
    'RfidReaderAt',
    'UhfAtReader',
    
    # Specific reader implementations
    'QRG2_ETSI',
    'QRG2_FCC',
    'DwarfG2_v2',
    'DwarfG2_Mini_v2', 
    'DwarfG2_XR_v2',
    
    # Utility classes
    'ExpectedReaderInfo',
    
    # Version information
    '__version__',
    '__version_info__',
    '__author__'
]

# Module metadata
__version__ = "2.0.0"
__version_info__ = (2, 0, 0)
__author__ = 'info@metratec.com'