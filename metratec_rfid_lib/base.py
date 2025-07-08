"""
Base classes and utilities for Metratec RFID Reader SDK

This module contains the fundamental building blocks used throughout the SDK:
- Exception classes for error handling
- Tag classes for representing RFID transponders
- Utility decorators for reader configuration

Author: neumann@metratec.com
"""

__version_info__ = (1, 2, 0)
__version__ = ".".join(str(x) for x in __version_info__)
__author__ = 'neumann@metratec.com'


class RfidReaderException(Exception):
    """
    Exception class for Metratec RFID reader operations
    
    Raised when communication errors, protocol errors, or tag operation
    failures occur during reader interactions.
    """


class Tag(dict):
    """Base transponder class with common tag properties and methods
    
    Inherits from dict to allow flexible storage of tag attributes.
    Provides standardized access methods for common tag properties.
    """

    def get_id(self) -> str:
        """Return the primary tag identifier (defaults to TID)"""
        return self.get_tid()

    def get_tid(self) -> str:
        """Return the Tag ID (TID)
        
        The TID is a unique identifier stored in the tag's memory.
        
        Returns:
            str: The tag identifier
        """
        return self.get('tid', '')

    def set_tid(self, tid: str) -> None:
        """Set the Tag ID (TID)
        
        Args:
            tid (str): The tag identifier to set
        """
        self.set_value('tid', tid)

    def get_timestamp(self) -> int:
        """Return the detection timestamp
        
        Returns:
            int: Unix timestamp when tag was detected (-1 if not set)
        """
        return self.get('timestamp', -1)

    def set_timestamp(self, timestamp: int) -> None:
        """Set the detection timestamp
        
        Args:
            timestamp (int): Unix timestamp to set
        """
        self.set_value('timestamp', timestamp)

    def get_first_seen(self) -> int:
        """Return the first detection timestamp
        
        Returns:
            int: Unix timestamp of first detection (-1 if not set)
        """
        return self.get('first_seen', -1)

    def set_first_seen(self, timestamp: int) -> None:
        """Set the first detection timestamp
        
        Args:
            timestamp (int): Unix timestamp to set
        """
        self.set_value('first_seen', timestamp)

    def get_last_seen(self) -> int:
        """Return the last detection timestamp
        
        Returns:
            int: Unix timestamp of last detection (-1 if not set)
        """
        return self.get('last_seen', -1)

    def set_last_seen(self, timestamp: int) -> None:
        """Set the last detection timestamp
        
        Args:
            timestamp (int): Unix timestamp to set
        """
        self.set_value('last_seen', timestamp)

    def get_data(self) -> str:
        """Return user data stored on the tag
        
        Returns:
            str: Hex-encoded user data
        """
        return self.get('data', '')

    def set_data(self, data: str) -> None:
        """Set user data for the tag
        
        Args:
            data (str): Hex-encoded data to store
        """
        self.set_value('data', data)

    def get_antenna(self) -> int:
        """Return the antenna number that detected this tag
        
        Returns:
            int: Antenna number (0 if not set)
        """
        return self.get('antenna', 0)

    def set_antenna(self, antenna: int) -> None:
        """Set the antenna number for this tag
        
        Args:
            antenna (int): Antenna number to set
        """
        self.set_value('antenna', antenna)

    def get_seen_count(self) -> int:
        """Return the number of times this tag was detected
        
        Returns:
            int: Detection count
        """
        count = self.get('seen_count')
        return count if count else 0

    def set_seen_count(self, seen_count: int) -> None:
        """Set the detection count for this tag
        
        Args:
            seen_count (int): Number of detections
        """
        self.set_value('seen_count', seen_count)

    def has_error(self) -> bool:
        """Check if tag has an error condition
        
        Returns:
            bool: True if tag has an error message
        """
        return self.get('has_error', False)

    def get_error_message(self) -> str:
        """Return the error message for this tag
        
        Returns:
            str: Error message (empty if no error)
        """
        return self.get('error_message', '')

    def set_error_message(self, message: str) -> None:
        """Set an error message for this tag
        
        Args:
            message (str): Error message to set
        """
        self.set_value('error_message', message)
        self.set_value('has_error', bool(message))

    def set_value(self, key: str, value) -> None:
        """Set a dictionary value with None handling
        
        Args:
            key (str): Dictionary key
            value: Value to set (None values remove the key)
        """
        if value is not None:
            self[key] = value
        elif key in self:
            del self[key]


class UhfTag(Tag):
    """UHF-specific transponder class with EPC and RSSI support
    
    Extends the base Tag class with UHF-specific properties like
    Electronic Product Code (EPC) and signal strength (RSSI).
    """

    def get_id(self) -> str:
        """Return the primary identifier (EPC for UHF tags)"""
        identifier: str = self.get_epc()
        return identifier if identifier else "unknown"

    def get_epc(self) -> str:
        """Return the Electronic Product Code (EPC)
        
        The EPC is the primary identifier for UHF RFID tags.
        
        Returns:
            str: Hex-encoded EPC
        """
        return self.get('epc', '')

    def set_epc(self, epc: str) -> None:
        """Set the Electronic Product Code (EPC)
        
        Args:
            epc (str): Hex-encoded EPC to set
        """
        self.set_value('epc', epc)

    def get_rssi(self) -> int:
        """Return the Received Signal Strength Indicator (RSSI)
        
        Returns:
            int: RSSI value in dBm (0 if not measured)
        """
        return self.get('rssi', 0)

    def set_rssi(self, rssi: int) -> None:
        """Set the RSSI value
        
        Args:
            rssi (int): RSSI value in dBm
        """
        self.set_value('rssi', rssi)


class ExpectedReaderInfo():
    """Decorator for specifying expected reader firmware and hardware
    
    This decorator is used to mark reader classes with their expected
    firmware and hardware information for validation purposes.
    """

    def __init__(self, firmware_name: str, hardware_name: str, min_firmware: float) -> None:
        """Initialize reader info decorator
        
        Args:
            firmware_name (str): Expected firmware name
            hardware_name (str): Expected hardware name  
            min_firmware (float): Minimum required firmware version
        """
        self._firmware_name = firmware_name
        self._hardware_name = hardware_name
        self._min_firmware = min_firmware

    def __call__(self, clazz):
        """Apply reader info to class
        
        Adds the expected reader information to the class as attributes
        that can be used for validation during initialization.
        
        Args:
            clazz: The class to decorate
            
        Returns:
            The decorated class with reader info attributes
        """
        properties = getattr(clazz, "_expected_reader", None)
        if not properties:
            properties = {}
            setattr(clazz, "_expected_reader", properties)
        properties["firmware_name"] = self._firmware_name
        properties["hardware_name"] = self._hardware_name
        properties["min_firmware"] = self._min_firmware
        return clazz