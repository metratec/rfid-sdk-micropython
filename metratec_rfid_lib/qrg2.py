"""
QRG2 UHF RFID Reader implementation

The QRG2 is a compact UHF RFID module that integrates antenna and reader 
into a single OEM module. It supports up to 9dBm output power and is 
ideal for applications requiring a simple, all-in-one RFID solution.

Available variants:
- QRG2_ETSI: ETSI-only version (Europe, restricted to ETSI region)
- QRG2_FCC: FCC-only version (North America, restricted to FCC region)

Features:
- Integrated antenna design
- Up to 9dBm output power
- Compact form factor
- Single antenna operation
- Full UHF Gen2 protocol support
- Regional compliance variants

Author: neumann@metratec.com
"""

from machine import UART  # type: ignore  # ignore  pylint: disable=import-error,unused-import

from .base import ExpectedReaderInfo, RfidReaderException
from .uhf_reader import UhfAtReader


@ExpectedReaderInfo("QRG2", "QRG2", 1.3)
class QRG2_ETSI(UhfAtReader):
    """QRG2 UHF RFID reader - ETSI variant (Europe)
    
    This is the European variant of the QRG2 reader that only supports 
    the ETSI region. Attempting to set any other region will raise an error.
    
    Use this class when you need to ensure compliance with European
    regulations or prevent accidental region misconfiguration.
    
    Specifications:
    - Output power: 0-9 dBm
    - Antenna: Integrated
    - Operating frequency: ETSI only (Europe)
    - Interface: UART (115200 baud)
    - Protocol: UHF Gen2 (ISO 18000-6C)
    """
    
    def __init__(self, uart: UART):
        """Initialize QRG2 ETSI reader
        
        Args:
            uart (UART): Configured UART interface for communication
        """
        self._allowed_regions = ["ETSI"]
        super().__init__(uart)
    
    def set_region(self, region: str) -> None:
        """Set the UHF region with validation
        
        Args:
            region (str): Region to set ("ETSI" only)
            
        Raises:
            RfidReaderException: If region not supported by this reader variant
        """
        if region not in self._allowed_regions:
            raise RfidReaderException(
                f"Region '{region}' not supported by {self.__class__.__name__}. "
                f"Allowed regions: {', '.join(self._allowed_regions)}")
        super().set_region(region)


@ExpectedReaderInfo("QRG2", "QRG2", 1.3)
class QRG2_FCC(UhfAtReader):
    """QRG2 UHF RFID reader - FCC variant (North America)
    
    This is the North American variant of the QRG2 reader that only supports 
    the FCC region. Attempting to set any other region will raise an error.
    
    Use this class when you need to ensure compliance with North American
    regulations or prevent accidental region misconfiguration.
    
    Specifications:
    - Output power: 0-9 dBm
    - Antenna: Integrated
    - Operating frequency: FCC only (North America)
    - Interface: UART (115200 baud)
    - Protocol: UHF Gen2 (ISO 18000-6C)
    """
    
    def __init__(self, uart: UART):
        """Initialize QRG2 FCC reader
        
        Args:
            uart (UART): Configured UART interface for communication
        """
        self._allowed_regions = ["FCC"]
        super().__init__(uart)
    
    def set_region(self, region: str) -> None:
        """Set the UHF region with validation
        
        Args:
            region (str): Region to set ("FCC" only)
            
        Raises:
            RfidReaderException: If region not supported by this reader variant
        """
        if region not in self._allowed_regions:
            raise RfidReaderException(
                f"Region '{region}' not supported by {self.__class__.__name__}. "
                f"Allowed regions: {', '.join(self._allowed_regions)}")
        super().set_region(region)