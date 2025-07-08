"""
UHF RFID Reader base implementation with AT protocol support

This module contains the UhfAtReader class which provides the core functionality
for UHF RFID operations including inventory, tag reading/writing, and configuration
management. All specific reader implementations inherit from this base class.

Author: neumann@metratec.com
"""

from time import time  # type: ignore  # ignore  pylint: disable=import-error,unused-import,no-name-in-module
from machine import UART  # type: ignore  # ignore  pylint: disable=import-error,unused-import

from .base import RfidReaderException, UhfTag
from .at_protocol import RfidReaderAt


class UhfAtReader(RfidReaderAt):
    """The implementation of the uhf gen2 reader with the **AT-protocol.**
    """

    def __init__(self, uart: UART):
        """_summary_

        Args:
            uart (UART): the communication interface
        """
        self._config: dict = {}
        super().__init__(uart)

    def _initialise(self):
        super()._initialise()
        try:
            # stop continuous inventory
            self._send_command('AT+BINV')
        except RfidReaderException:
            pass
        try:
            # stop continuous inventory report
            self._send_command('AT+BINVR')
        except RfidReaderException:
            pass
        self._config['inventory'] = self.get_inventory_settings()

    def get_inventory_settings(self) -> dict:
        """Gets the current reader inventory settings

        Raises:
            RfidReaderException: if an reader error occurs

        Returns:
            dict: with 'only_new_tag', 'with_rssi' and 'with_tid' entries
        """
        response: list[str] = self._send_command("AT+INVS?")
        # +INVS: 0,1,0
        data: list[str] = response[0][7:].split(',')
        try:
            config: dict[str, object] = {'only_new_tag': data[0] == '1',
                                         'with_rssi': data[1] == '1',
                                         'with_tid': data[2] == '1'
                                         }
            if len(data) >= 4:
                config['fast_start'] = data[3] == '1'
            if len(data) >= 5:
                config['phase'] = data[4] == '1'
            if len(data) >= 6:
                config['select'] = data[5]
            if len(data) >= 7:
                config['target'] = data[6]
            return config
        except IndexError as err:
            raise RfidReaderException(
                f"Not expected response for command AT+INVS? - {response}") from err

    def set_inventory_settings(self, only_new_tag: object = None, with_rssi: object = None,
                               with_tid: object = None, fast_start: object = None,
                               phase: object = None, select: object = None,
                               target: object = None) -> None:
        """Configure the inventory response

        Args:
            only_new_tag (bool, optional): Only return new tags. Defaults to False.

            with_rssi (bool, optional): Append the rssi value to the response. Defaults to True.

            with_tid (bool, optional): Append the tid to the response. Defaults to False.

            fast_start (bool, optional): Does an inventory without putting all tags into session
            state A at the start. This can speed up the start of the inventory, but it requires
            that all tags are in "reset state".

            phase (bool, optional): Append the the phase information to the inventory

            select (str, optional): Use to set witch tag should respond. 'ALL' for all, 'SL' for select asserted,
            'NSL' for select not asserted

            target (str, optional): Use to set witch tag should respond. Can be 'A' or 'B'

        Raises:
            RfidReaderException: if an reader error occurs
        """
        def bti(value):
            return '1' if value else '0'

        config: dict[str, object] = self._config['inventory']
        config_size = len(config)

        parameters: list[object] = []
        parameters.append(bti(only_new_tag) if only_new_tag is not None else bti(config['only_new_tag']))
        parameters.append(bti(with_rssi) if with_rssi is not None else bti(config['with_rssi']))
        parameters.append(bti(with_tid) if with_tid is not None else bti(config['with_tid']))
        if config_size >= 4:
            parameters.append(bti(fast_start) if fast_start is not None else bti(config['fast_start']))
        if config_size >= 5:
            parameters.append(bti(phase) if phase is not None else bti(config['phase']))
        if config_size >= 6:
            parameters.append(select if select is not None else config['select'])
        if config_size >= 7:
            parameters.append(target if target is not None else config['target'])

        self._send_command("AT+INVS", *parameters)

        # update configuration
        config['only_new_tag'] = only_new_tag
        config['with_rssi'] = with_rssi
        config['with_tid'] = with_tid
        if config_size >= 4:
            config['fast_start'] = fast_start
        if config_size >= 5:
            config['phase'] = phase
        if config_size >= 6:
            config['select'] = select
        if config_size >= 7:
            config['target'] = target

    def set_region(self, region: str) -> None:
        """Sets the used uhf region

        Args:
            region (Region): the uhf region

        Raises:
            RfidReaderException: if an reader error occurs
        """
        self._send_command("AT+REG", region)

    def get_region(self) -> str:
        """Return the configured uhf region

        Raises:
            RfidReaderException: if an reader error occurs

        Returns:
            Region: the used uhf region
        """
        response: list[str] = self._send_command("AT+REG?")
        # +REG: ETSI
        try:
            return response[0][6:]
        except IndexError as exc:
            raise RfidReaderException(
                f"Not expected response for command AT+REG? - {response}") from exc

    def set_tag_size(self, tags_size: int, min_tags: int = 0, max_tags: int = 256) -> None:
        """Configure the expected numbers of transponders in the field

        Args:
            tags_size (int): expected numbers of transponders

            min_tags (int, optional): Minimum numbers of transponders. Defaults to 0.

            max_tags (int, optional): Maximum numbers of transponders [min_tags...32768]. Defaults to 256.

        Raises:
            RfidReaderException: if an reader error occurs
        """
        q_start: int = 0
        q_min = None
        q_max = None
        while tags_size > pow(2, q_start):
            q_start += 1
        if min_tags:
            q_min = 0
            while min_tags > pow(2, q_min):
                q_min += 1
        else:
            q_min = 0
        if max_tags:
            q_max = 0
            while max_tags > pow(2, q_max):
                q_max += 1
        self._send_command("AT+Q", q_start, q_min, q_max)

    def get_tag_size(self) -> int:
        """Returns the configured tag size

        Raises:
            RfidReaderException: if an reader error occurs

        Returns:
            int: the configured tag size
        """
        response: list[str] = self._send_command("AT+Q?")
        # +Q: 4,2,15
        try:
            setting: list[str] = response[0][4:].split(",")
            return pow(2, int(setting[0]))
        except IndexError as exc:
            raise RfidReaderException(
                f"Not expected response for command AT+Q? - {response}") from exc

    def set_power(self, power: int) -> None:
        """Sets the antenna power of the reader for all antennas

        Args:
            power (int): antenna power in dbm [0,9]

        Raises:
            RfidReaderException: if an reader error occurs
        """
        self._send_command("AT+PWR", power)

    def get_power(self) -> int:
        """Return the current power level

        Raises:
            RfidReaderException: if an reader error occurs

        Returns:
            int: the current power level
        """
        response: list[str] = self._send_command("AT+PWR?")
        # +PWR: 9
        try:
            return int(response[0][6:])
        except IndexError as exc:
            raise RfidReaderException(
                f"Not expected response for command AT+PWR? - {response}") from exc

    def set_rf_mode(self, rf_mode: int) -> None:
        """Sets the RF mode for the reader
        
        RF modes control internal RF communication settings between tag and reader.
        Each mode corresponds to specific RF parameters optimized for different scenarios.
        
        Common modes:
        - 285: Sensitivity mode (slower, longer range)
        - 223: Balanced mode (good speed and range for ETSI)
        - 103: High speed mode (FCC only)
        
        Args:
            rf_mode (int): RF mode ID from protocol documentation
            
        Raises:
            RfidReaderException: if an reader error occurs or invalid mode
        """
        self._send_command("AT+RFM", rf_mode)

    def get_rf_mode(self) -> int:
        """Return the current RF mode
        
        Raises:
            RfidReaderException: if an reader error occurs
            
        Returns:
            int: the current RF mode ID
        """
        response: list[str] = self._send_command("AT+RFM?")
        # +RFM: 285
        try:
            return int(response[0][6:])
        except IndexError as exc:
            raise RfidReaderException(
                f"Not expected response for command AT+RFM? - {response}") from exc

    def get_inventory(self, ignore_error: bool = False) -> list[UhfTag]:
        """get the current inventory from the current antenna (see set_antenna)

        Raises:
            RfidReaderException: if an reader error occurs

        Returns:
            list[UhfTag]: An array with the founded transponder
        """
        responses: list[str] = self._send_command("AT+INV")
        inventory: list[UhfTag] = self._parse_inventory(responses, int(time()), ignore_error=ignore_error)
        current_antenna = self._config.get('antenna')
        if current_antenna:
            for tag in inventory:
                tag.set_antenna(current_antenna)
        return inventory

    def get_inventory_report(self, duration: int = 0, ignore_error: bool = False) -> list[UhfTag]:
        """gets an inventory report from the current antenna (see set_antenna)

        Args:
            duration (int, optional): inventory report duration in milliseconds [1..1000]. Defaults to 100 seconds.
            ignore_error (bool, optional): Set to True to ignore antenna errors. Defaults to False.


        Raises:
            RfidReaderException: if an reader error occurs

        Returns:
            list[UhfTag]: An array with the founded transponder
        """
        if duration == 0:
            responses: list[str] = self._send_command('AT+INVR')
        else:
            responses = self._send_command('AT+INVR', duration, timeout=2000 + duration)
        inventory: list[UhfTag] = self._parse_inventory(responses, int(time()), 7, ignore_error, True)
        return inventory

    def set_mask(self, mask: str, start: int = 0, memory: str = "EPC") -> None:
        """Set a mask

        Args:
            mask (str): the mask (hex)

            start (int, optional): start byte. Defaults to 0.

            bit_length (int, optional): Bits to check. Defaults to 0.

            memory (str, optional): the memory for the mask. ['PC','EPC','USR','TID'] Defaults to "EPC".

        Raises:
            RfidReaderException: if an reader error occurs

        """
        self._send_command('AT+MSK', memory, start, mask)

    def get_mask(self) -> dict:
        """Gets current reader mask.


        Raises:
            RfidReaderException: if an reader error occurs

        Returns:
            dict: dictionary with the mask settings
                  available entries: memory (str), start (int), mask (str)
        """
        responses: list[str] = self._send_command('AT+MSK?')
        # +MSK: EPC,0,0000
        # +MSK: OFF
        data: list[str] = responses[0][6:].split(',')
        return_value: dict = {'enabled': data[0] != "OFF"}
        if return_value['enabled']:
            return_value.update({'memory': data[0], 'start': int(data[1]), 'mask': data[2]})
        return return_value

    def reset_mask(self) -> None:
        """Remove the mask
        """
        self._send_command('AT+MSK', "OFF")

    def set_bit_mask(self, mask: str, start: int = 0, memory: str = "EPC") -> None:
        """Set a mask

        Args:
            mask (str): the binary mask, e.g. '0110'

            start (int, optional): start bit. Defaults to 0.

            bit_length (int, optional): Bits to check. Defaults to 0.

            memory (str, optional): the memory for the mask. ['PC','EPC','USR','TID'] Defaults to "EPC".

        Raises:
            RfidReaderException: if an reader error occurs

        """
        self._send_command('AT+BMSK', memory, start, mask)

    def get_bit_mask(self) -> dict:
        """Gets current reader mask.


        Raises:
            RfidReaderException: if an reader error occurs

        Returns:
            dict: dictionary with the mask settings
                  available entries: memory (str), start (int), mask (str), enabled (bool)
        """
        responses: list[str] = self._send_command('AT+BMSK?')
        # +BMSK: EPC,0,0000
        # +BMSK: OFF
        data: list[str] = responses[0][7:].split(',')
        return_value: dict = {'enabled': data[0] != "OFF"}
        if return_value['enabled']:
            return_value.update({'memory': data[0], 'start': int(data[1]), 'mask': data[2]})
        return return_value

    def reset_bit_mask(self) -> None:
        """Remove the bit mask
        """
        self._send_command('AT+BMSK', "OFF")

    def read_tag_data(self, start: int = 0, length: int = 1, memory: str = 'USR',
                      epc_mask: str = '') -> list[UhfTag]:
        """read the memory of the founded transponder

        Args:
            start (int, optional): Start address. Defaults to 0.

            length (int, optional): Bytes to read. Defaults to 1.

            epc_mask (str, optional): Epc mask filter. Defaults to None.

            memory (str, optional): Memory bank to read ["PC","EPC","USR","TID"]. Defaults to "USR".

        Raises:
            RfidReaderException: if an reader error occurs

        Returns:
            list[UhfTag]:  A list of transponders found.
        """
        responses: list[str] = self._send_command("AT+READ", memory, start, length, epc_mask)
        timestamp: int = int(time())
        inventory: list[UhfTag] = []
        for response in responses:
            # +READ: 3034257BF468D480000003EE,OK,0000
            # +READ: <No tags found>
            if response[7] == '<':
                # inventory message, no tag
                # messages: Antenna Error / NO TAGS FOUND / ROUND FINISHED ANT=2
                if response[8] == 'N':  # NO TAGS FOUND
                    pass
                continue
            info: list[str] = response[7:].split(',')
            tag: UhfTag = UhfTag()
            tag.set_epc(info[0])
            tag.set_timestamp(timestamp)
            try:
                if info[1] == 'OK':
                    tag.set_value(memory.lower(), info[2])
                    tag.set_data(info[2])
                else:
                    tag.set_error_message(info[1])
            except IndexError:
                # ignore index errors ... response not valid (+READ: <No tags found during inventory>)
                pass
            inventory.append(tag)
        return inventory

    def read_tag_usr(self, start: int = 0, length: int = 1, epc_mask: str = '') -> list[UhfTag]:
        """read the usr memory of the founded transponder

        Args:
            start (int, optional): Start address. Defaults to 0.

            length (int, optional): Bytes to read. Defaults to 1.

            epc_mask (str, optional): Epc mask filter. Defaults to None.

        Raises:
            RfidReaderException: if an reader error occurs

        Returns:
            list[UhfTag]: A list with the transponder found.
        """
        return self.read_tag_data(start, length, 'USR', epc_mask)

    def read_tag_tid(self, start: int = 0, length: int = 4, epc_mask: str = '') -> list[UhfTag]:
        """read the tid of the founded transponder

        Args:
            start (int, optional): Start address. Defaults to 0.

            length (int, optional): Bytes to read. Defaults to 1.

            epc_mask (str, optional): Epc mask filter. Defaults to None.

        Raises:
            RfidReaderException: if an reader error occurs

        Returns:
            list[UhfTag]: A list with the transponder found.
        """
        return self.read_tag_data(start, length, 'TID', epc_mask)

    def write_tag_data(self, data: str, start: int = 0,  memory: str = 'USR',
                       epc_mask: str = '') -> list[UhfTag]:
        """write the data to the founded transponder

        Args:
            data (str): data to write

            start (int, optional): Start address. Defaults to 0.

            memory (str, optional): Memory bank to read ["PC","EPC","USR"]. Defaults to "USR".

            epc_mask (str, optional): Epc mask filter. Defaults to None.

        Raises:
            RfidReaderException: if an reader error occurs

        Returns:
            list[UhfTag]: list with written tags, if a tag was not written the has_error boolean is true
        """

        # disable 'Too many arguments' warning - pylint: disable=R0913

        responses = self._send_command("AT+WRT", memory, start, data, epc_mask)
        return self._parse_tag_responses(responses, 6)

    def write_tag_usr(self, data: str, start: int = 0, epc_mask: str = '') -> list[UhfTag]:
        """write the data to the founded transponder

        Args:
            data (str): _description_

            start (int, optional): Start address. Defaults to 0.

            epc_mask (str, optional): Epc mask filter. Defaults to None.

        Raises:
            RfidReaderException: if an reader error occurs

        Returns:
            list[UhfTag]: list with written tags, if a tag was not written the has_error boolean is true
        """
        if not data:
            raise RfidReaderException("Data must be set")
        inv = self.write_tag_data(data, start, 'USR', epc_mask)
        return inv

    def write_tag_epc(self, tid: str, new_epc: str, start: int = 0) -> list[UhfTag]:
        """write the tag epc

        Args:
            tid (str): the tag id

            new_epc: the new epc

            start (int, optional): Start address. Defaults to 0.

        Raises:
            RfidReaderException: if an reader error occurs

        Returns:
            list[UhfTag]: list with written tags, if a tag was not written the has_error boolean is true
        """

        # disable 'Too many arguments' warning - pylint: disable=R0913
        if len(new_epc) % 4:
            raise RfidReaderException(" The new epc length must be a multiple of 4")
        tags: dict[str, UhfTag] = {}
        epc_words: int = int(len(new_epc) / 4)
        epc_length_byte = int(epc_words / 2) << 12
        if 1 == epc_words % 2:
            epc_length_byte |= 0x0800

        mask_settings: dict = {}
        if tid:
            mask_settings = self.get_mask()  # get current mask
            self.set_mask(tid, memory="TID")
        inventory_pc: list[UhfTag] = self.read_tag_data(0, 2, 'PC')
        if not inventory_pc:
            # no tags found
            return inventory_pc
        pc_byte = 0
        for tag in inventory_pc:
            data = int(str(tag.get_data()), 16) & 0x07FF
            if not pc_byte:
                pc_byte = data
            elif data != pc_byte:
                raise RfidReaderException("Different tags are in the field, which would result in"
                                          " data loss when writing. Please edit individually.")
        # write epc
        inventory_epc: list[UhfTag] = self.write_tag_data(new_epc, start, 'EPC')
        for tag in inventory_epc:
            tags[tag.get_epc()] = tag
            if not tag.has_error():
                old_epc: str = tag.get_epc()
                tag.set_epc(new_epc)
                tag.set_value("old_epc", old_epc)
        # write length
        pc_byte |= epc_length_byte
        inventory_pc = self.write_tag_data(f"{pc_byte:04X}", 0, 'PC')
        for tag_pc in inventory_pc:
            tag_epc = tags.get(tag_pc.get_epc())
            if tag_epc:
                if tag_pc.has_error():
                    if not tag_epc.has_error():
                        # write new epc length not ok
                        tag_epc.set_error_message("epc written, epc length not updated!")
                    else:
                        # both not successful:
                        tag_epc.set_error_message(f"epc not written - {tag_epc.get_error_message()}")
            elif not tag_pc.has_error():
                # tag epc length was updated
                tag_pc.set_error_message("epc not written, but epc length updated!")
                tags[tag_pc.get_epc()] = tag_pc
            # else: both epc write and epc length was not successful...ignore tag
        # Note: The field is active during these two write commands
        #       ...so both commands return the old epc and can be compared
        if tid:
            if mask_settings['enabled']:
                # reset to the last mask setting
                self.set_mask(mask_settings['memory'], mask_settings['start'], mask_settings['mask'])
            else:
                self.reset_mask()
        return list(tags.values())

    def kill_tag(self, password: str, epc_mask: str = '') -> list[UhfTag]:
        """Kill a transponder

        Args:
            password (str): the kill password (32 bit, 8 hex signs)

            epc_mask (str, optional): Epc mask filter. Defaults to None.

        Returns:
            list[UhfTag]: List with handled tag. If the tag has error, the kill was not successful
        """
        responses: list[str] = self._send_command("AT+KILL", password, epc_mask)
        # AT+KILL: 1234ABCD<CR><LF>
        # +KILL: ABCD01237654321001234567,ACCESS ERROR<CR><LF>
        # OK<CR><LF>
        return self._parse_tag_responses(responses, 7)

    def lock_tag(self, membank: str, password: str, epc_mask: str = '') -> list[UhfTag]:
        """Locking of a memory bank of the transponder

        Args:
            membank (str): the memory to lock ['EPC', 'USR']

            password (str): the access password (32 bit, 8 hex signs)

            epc_mask (str, optional): Epc mask filter. Defaults to None.

        Returns:
            list[UhfTag]: List with handled tag. If the tag has error, the lock was not successful
        """
        # membank: KILL,LCK,EPC,TID,USR
        responses: list[str] = self._send_command("AT+LCK", membank, password, epc_mask, timeout=10000)
        # AT+ULCK: USR,1234ABCD<CR>
        # <LF>
        # +LCK: ABCD01237654321001234567,ACCESS ERROR<CR>
        # +LCK: ABCD01237654321001234567,ACCESS ERROR<CR>
        # +LCK: ABCD01237654321001234567,ACCESS ERROR<CR><LF>
        # OK<CR><LF>
        return self._parse_tag_responses(responses, 6)

    def lock_user_memory(self, password: str, epc_mask: str = '') -> list[UhfTag]:
        """Locking of the user memory bank of the transponder

        Args:
            password (str): the access password (32 bit, 8 hex signs)

            epc_mask (str, optional): Epc mask filter. Defaults to None.

        Returns:
            list[UhfTag]: List with handled tag. If the tag has error, the lock was not successful
        """
        return self.lock_tag("USR", password, epc_mask)

    def lock_epc_memory(self, password: str, epc_mask: str = '') -> list[UhfTag]:
        """Locking of the epc memory bank of the transponder

        Args:
            password (str): the access password (32 bit, 8 hex signs)

            epc_mask (str, optional): Epc mask filter. Defaults to None.

        Returns:
            list[UhfTag]: List with handled tag. If the tag has error, the lock was not successful
        """
        return self.lock_tag("EPC", password, epc_mask)

    def unlock_tag(self, membank: str, password: str, epc_mask: str = '') -> list[UhfTag]:
        """Unlocking of a memory bank of the transponder

        Args:
            membank (str): the memory to lock ['EPC', 'USR']

            password (str): the access password (32 bit, 8 hex signs)

            epc_mask (str, optional): Epc mask filter. Defaults to None.

        Returns:
            list[UhfTag]: List with handled tag. If the tag has error, the unlock was not successful
        """
        # membank: KILL,LCK,EPC,TID,USR
        responses: list[str] = self._send_command("AT+ULCK", membank, password, epc_mask, timeout=10000)
        # AT+LCK: USR,1234ABCD<CR>
        # <LF>
        # +ULCK: ABCD01237654321001234567,ACCESS ERROR<CR><LF>
        # OK<CR><LF>
        return self._parse_tag_responses(responses, 7)

    def unlock_user_memory(self, password: str, epc_mask: str = '') -> list[UhfTag]:
        """Unlocking of the user memory bank of the transponder

        Args:
            password (str): the access password (32 bit, 8 hex signs)

            epc_mask (str, optional): Epc mask filter. Defaults to None.

        Returns:
            list[UhfTag]: List with handled tag. If the tag has error, the unlock was not successful
        """
        return self.unlock_tag("USR", password, epc_mask)

    def unlock_epc_memory(self, password: str, epc_mask: str = '') -> list[UhfTag]:
        """Unlocking of the epc memory bank of the transponder

        Args:
            password (str): the access password (32 bit, 8 hex signs)

            epc_mask (str, optional): Epc mask filter. Defaults to None.

        Returns:
            list[UhfTag]: List with handled tag. If the tag has error, the unlock was not successful
        """
        return self.unlock_tag("EPC", password, epc_mask)

    def lock_tag_permament(self, membank: str, password: str, epc_mask: str = '') -> list[UhfTag]:
        """Permament locking of a memory bank of the transponder

        Args:
            membank (str): the memory to lock ['EPC', 'USR']

            password (str): the access password (32 bit, 8 hex signs)

            epc_mask (str, optional): Epc mask filter. Defaults to None.

        Returns:
            list[UhfTag]: List with handled tag. If the tag has error, the lock was not successful
        """
        # membank: KILL,LCK,EPC,TID,USR
        responses: list[str] = self._send_command("AT+PLCK", membank, password, epc_mask)
        # AT+PLCK: USR,1234ABCD<CR>
        # <LF>
        # +PLCK: ABCD01237654321001234567,ACCESS ERROR<CR>
        # +PLCK: ABCD01237654321001234567,ACCESS ERROR<CR>
        # +PLCK: ABCD01237654321001234567,ACCESS ERROR<CR><LF>
        # OK<CR><LF>
        return self._parse_tag_responses(responses, 7)

    def lock_user_memory_permament(self, password: str, epc_mask: str = '') -> list[UhfTag]:
        """Permament l of the user memory bank of the transponder

        Args:
            password (str): the access password (32 bit, 8 hex signs)

            epc_mask (str, optional): Epc mask filter. Defaults to None.

        Returns:
            list[UhfTag]: List with handled tag. If the tag has error, the lock was not successful
        """
        return self.lock_tag_permament("USR", password, epc_mask)

    def lock_epc_memory_permament(self, password: str, epc_mask: str = '') -> list[UhfTag]:
        """Permament l of the epc memory bank of the transponder

        Args:
            password (str): the access password (32 bit, 8 hex signs)

            epc_mask (str, optional): Epc mask filter. Defaults to None.

        Returns:
            list[UhfTag]: List with handled tag. If the tag has error, the lock was not successful
        """
        return self.lock_tag_permament("EPC", password, epc_mask)

    def set_lock_password(self, password: str, new_password, epc_mask: str = '') -> list[UhfTag]:
        """sets the lock password

        Args:
            password (str): the access password (32 bit, 8 hex signs)

            new_password (_type_): the new access password (32 bit, 8 hex signs)

            epc_mask (str, optional): Epc mask filter. Defaults to None.

        Returns:
            list[UhfTag]: List with handled tag. If the tag has error, the password change was not successful
        """
        responses: list[str] = self._send_command("AT+PWD", "LCK", password, new_password, epc_mask)
        # AT+PWD: LCK,1234ABCD,1234ABCD<CR><LF>
        # +PWD: ABCD01237654321001234567,ACCESS ERROR<CR>
        # +PWD: ABCD01237654321001234567,ACCESS ERROR<CR>
        # +PWD: ABCD01237654321001234567,ACCESS ERROR<CR>
        # +PWD: ABCD01237654321001234567,ACCESS ERROR<CR>
        # +PWD: ABCD01237654321001234567,ACCESS ERROR<CR><LF>
        # OK<CR><LF>
        return self._parse_tag_responses(responses, 6)

    def set_kill_password(self, password: str, new_password, epc_mask: str = '') -> list[UhfTag]:
        """sets the kill password

        Args:
            password (str): the access password (32 bit, 8 hex signs)

            new_password (_type_): the new access password (32 bit, 8 hex signs)

            epc_mask (str, optional): Epc mask filter. Defaults to None.

        Returns:
            list[UhfTag]: List with handled tag. If the tag has error, the password change was not successful
        """
        responses: list[str] = self._send_command("AT+PWD", "KILL", password, new_password, epc_mask)
        # AT+PWD: LCK,1234ABCD,1234ABCD<CR><LF>
        # +PWD: ABCD01237654321001234567,ACCESS ERROR<CR>
        # +PWD: ABCD01237654321001234567,ACCESS ERROR<CR>
        # +PWD: ABCD01237654321001234567,ACCESS ERROR<CR>
        # +PWD: ABCD01237654321001234567,ACCESS ERROR<CR>
        # +PWD: ABCD01237654321001234567,ACCESS ERROR<CR><LF>
        # OK<CR><LF>
        return self._parse_tag_responses(responses, 6)

    def _parse_inventory(
            self, responses: list[str],
            timestamp: int, split_index: int = 6,
            ignore_error: bool = False, is_report: bool = False) -> list[UhfTag]:
        """Parse inventory response data into UhfTag objects
        
        Processes AT protocol inventory responses and creates structured tag objects.
        Handles various response formats based on inventory settings (RSSI, TID, Phase).
        
        Response Examples:
        - Basic: +INV: E002001234567890
        - With TID: +INV: E002001234567890,E200600311753F23
        - With RSSI: +INV: E002001234567890,E200600311753F23,-45
        - Report: +INVR: E002001234567890,5 (EPC,Count)
        - Messages: +INV: <NO TAGS FOUND>, +INV: <ROUND FINISHED, ANT=2>
        
        Args:
            responses (list[str]): Raw response lines from AT command
            timestamp (int): Unix timestamp for tag detection
            split_index (int): Character index where data starts (default: 6 for "+INV: ")
            ignore_error (bool): Skip error responses instead of raising exception
            is_report (bool): Parse as inventory report with count data
            
        Returns:
            list[UhfTag]: Parsed tag objects with EPC, TID, RSSI, and metadata
        """

        inventory: list[UhfTag] = []
        
        # Extract configuration for response parsing
        with_tid: bool = self._config['inventory']['with_tid']      # TID data included
        with_rssi: bool = self._config['inventory']['with_rssi']    # RSSI values included
        with_phase: bool = self._config['inventory'].get('phase', False)  # Phase information
        antenna: int = 0     # Current antenna being processed
        error: str = ''      # Error message accumulator
        
        # Process each response line
        for response in responses:
            # Skip non-response lines (must start with '+')
            if response[0] != '+':
                continue
                
            # Check for system messages vs tag data
            if response[split_index] == '<':
                # System messages: <NO TAGS FOUND>, <ROUND FINISHED, ANT=2>, <Error Message>
                if response[split_index+1] == 'N':  # NO TAGS FOUND
                    pass  # No action needed, empty result is valid
                elif response[split_index+1] == 'R':
                    # ROUND FINISHED ANT=X - extract antenna number
                    try:
                        antenna = int(response[-2:-1])
                    except (IndexError, ValueError) as err:
                        print("Error parsing inventory response - %s", err)
                elif ignore_error:
                    pass  # Skip error messages when instructed
                else:
                    print(f"error: {response[split_index+1:-1]}")
                    error = response[split_index+1:-1]
                continue
            info: list[str] = response[split_index:].split(',')
            # new_tag = UhfTag(info[0], timestamp, tid=info[1] if with_tid else '',
            #                  rssi=int(info[2]) if with_rssi and with_tid else int(info[1]) if with_rssi else 0,
            #                  seen_count=int(info[-1]) if is_report else 1)
            new_tag = UhfTag()
            new_tag.set_epc(info[0])
            new_tag.set_timestamp(timestamp)
            if with_tid:
                new_tag.set_tid(info[1])
            if with_rssi:
                new_tag.set_rssi(int(info[2]) if with_tid else int(info[1]))
            if is_report:
                new_tag.set_seen_count(int(info[-1]))
            if with_phase:
                new_tag['phase'] = [info[-2], info[-1]]
            inventory.append(new_tag)
        if error:
            error_detail = self._config.get('error', {})
            self._config.setdefault('error', error_detail)
            if antenna:
                error_detail[f"Antenna {antenna}"] = error
                msg = f"{error} - Antenna {antenna}"
            else:
                error_detail['message'] = error
                msg = error
            raise RfidReaderException(msg)
        if antenna:
            for tag in inventory:
                tag.set_antenna(antenna)
        return inventory

    def _parse_tag_responses(self, responses: list, prefix_length: int) -> list[UhfTag]:
        """Parsing the transponder responses. Used when the response list contains only the epc and the response code

        Args:
            responses (list): response list

            prefix_length (int): response command prefix length - len("+PREFIX: ")

            timestamp (float, optional): response timestamp.

        Returns:
            list[UhfTag]: list with handled tags
        """
        # +COMMAND: ABCD01237654321001234567,ACCESS ERROR<CR>
        # prefix_length = len("+COMMAND: ")
        timestamp: int = int(time())
        tags: list[UhfTag] = []
        for response in responses:
            if response[prefix_length] == '<':
                # inventory message, no tag
                # messages: Antenna Error / NO TAGS FOUND / ROUND FINISHED ANT=2
                if response[prefix_length+1] == 'N':  # NO TAGS FOUND
                    pass
                continue
            info: list[str] = response[prefix_length:].split(',')
            tag: UhfTag = UhfTag()
            tag.set_epc(info[0])
            tag.set_timestamp(timestamp)
            if info[1] != 'OK':
                tag.set_error_message(info[1])
            tags.append(tag)
        return tags

    def get_antenna_powers(self) -> list[int]:
        """Get power value per antenna (index 0 corresponds to antenna 1)

        Returns:
            list[int]: List with the power values for each antenna
        """
        responses: list[str] = self._send_command("AT+PWR?")
        # +PWR: 12,12,12,12
        data: list[str] = responses[0][6:].split(',')
        return list(map(int, data))

    def set_antenna_powers(self, antenna_powers: list[int]) -> None:
        """Set power values for multiple antennas

        Args:
            antenna_powers (list[int]): List with power values for each antenna
                                       (index 0 corresponds to antenna 1)
        """
        self._send_command("AT+PWR", *antenna_powers)

    def set_antenna_power(self, antenna: int, power: int) -> None:
        """Set power for a specific antenna

        Args:
            antenna (int): Antenna number (1-based)
            power (int): Antenna power in dBm

        Raises:
            RfidReaderException: If antenna not available or reader error occurs
        """
        if antenna <= 0:
            raise RfidReaderException(f"Antenna {antenna} not available")
        powers = self.get_antenna_powers()
        if antenna > len(powers):
            raise RfidReaderException(f"Antenna {antenna} not available")
        powers[antenna - 1] = power
        self.set_antenna_powers(powers)

    def set_antenna_multiplex(self, antennas) -> None:
        """Configure antenna multiplexing sequence

        Args:
            antennas (int or list): Number of antennas to multiplex OR 
                                   specific antenna sequence list

        Raises:
            RfidReaderException: If reader error occurs
        """
        if isinstance(antennas, int):
            self._send_command("AT+MUX", antennas)
        elif isinstance(antennas, list):
            self._send_command("AT+MUX", *antennas)

    def get_antenna_multiplex(self) -> list[int]:
        """Get current antenna multiplex sequence

        Returns:
            list[int]: The antenna sequence being used

        Raises:
            RfidReaderException: If reader error occurs
        """
        responses: list[str] = self._send_command("AT+MUX?")
        # +MUX: 1,2,3,....
        data: list[str] = responses[0][6:].split(',')
        if len(data) == 1:
            return [int(i) for i in data]
        return list(map(int, data))

    def get_external_multiplexer(self) -> int:
        """Get connected external multiplexer size

        Raises:
            RfidReaderException: If reader error occurs

        Returns:
            int: The multiplexer size (0 if none connected)
        """
        # +EMX: 4
        return int(self._send_command("AT+EMX?")[0][6:])

    def set_external_multiplexer(self, multiplexer_size: int):
        """Configure external multiplexer size

        Args:
            multiplexer_size (int): Size of connected multiplexer (4, 8, 16)

        Raises:
            RfidReaderException: If reader error occurs
        """
        self._send_command("AT+EMX", multiplexer_size)

    def set_antenna(self, antenna: int) -> None:
        """Select antenna to be used for operations

        Args:
            antenna (int): Antenna port to use

        Raises:
            RfidReaderException: If reader error occurs
        """
        self._send_command("AT+ANT", antenna)
        self._config['antenna'] = antenna

    def get_antenna(self) -> int:
        """Get currently selected antenna port

        Raises:
            RfidReaderException: If reader error occurs

        Returns:
            int: Currently selected antenna number
        """
        try:
            response: list[str] = self._send_command("AT+ANT?")
        except RfidReaderException as error:
            if "ERROR" in str(error):
                raise RfidReaderException("Multiple antennas not supported") from error
            raise error
        # +ANT: 2
        try:
            return int(response[0][6:])
        except IndexError as exc:
            raise RfidReaderException(
                f"Not expected response for command AT+ANT? - {response}") from exc

    def get_inventory_multi(self, ignore_error: bool = False) -> list[UhfTag]:
        """Get inventory using multiple antennas (configured with set_antenna_multiplex)

        Args:
            ignore_error (bool, optional): Skip antenna errors. Defaults to False.

        Raises:
            RfidReaderException: If reader error occurs

        Returns:
            list[UhfTag]: Array of transponders found across all antennas
        """
        responses: list[str] = self._send_command("AT+MINV")
        
        # Parse multiple inventory responses
        # +MINV: <Antenna Error><CR>
        # +MINV: <ROUND FINISHED, ANT=1><CR>
        # +MINV: 3034257BF468D480000003EB<CR>
        # +MINV: <ROUND FINISHED, ANT=2><CR>
        
        # Split responses into antenna sections
        inventory: list[UhfTag] = []
        last_index: int = 0
        for index, item in enumerate(responses):
            if item.startswith("+MINV: <R"):
                index += 1
                inventory.extend(self._parse_inventory(
                    responses[last_index:index], int(time()), 7, ignore_error))
                last_index = index
        return inventory
