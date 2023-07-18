"""
metratec rfid reader base class
"""

from time import time, ticks_ms  # type: ignore  # ignore  pylint: disable=import-error,unused-import,no-name-in-module
from machine import UART  # type: ignore  # ignore  pylint: disable=import-error,unused-import

__version_info__ = (1, 0, 0)
__version__ = ".".join(str(x) for x in __version_info__)
__author__ = 'neumann@metratec.com'


class RfidReaderException(Exception):
    """
    Exception class for the metratec rfid reader
    """


class Tag(dict):
    """Transponder class
    """

    def get_id(self) -> str:
        """ return the tag identifier"""
        return self.get_tid()

    def get_tid(self) -> str:
        """Return the tid

        Returns:
            str: the tid
        """
        return self.get('tid', '')

    def set_tid(self, tid: str) -> None:
        """Set the tid

        Args:
            tid (str): the tid to set
        """
        self.set_value('tid', tid)

    def get_timestamp(self) -> int:
        """Return the timestamp

        Returns:
            float: the timestamp
        """
        return self.get('timestamp', -1)

    def set_timestamp(self, timestamp: int) -> None:
        """Set the timestamp

        Args:
            timestamp (float): the timestamp to set
        """
        self.set_value('timestamp', timestamp)

    def get_first_seen(self) -> int:
        """Return the first seen timestamp

        Returns:
            float: the first seen timestamp
        """
        return self.get('first_seen', -1)

    def set_first_seen(self, timestamp: int) -> None:
        """Set the first seen timestamp

        Args:
            timestamp (float): the first seen timestamp to set
        """
        self.set_value('first_seen', timestamp)

    def get_last_seen(self) -> int:
        """Return the last seen timestamp

        Returns:
            float: the last seen timestamp
        """
        return self.get('last_seen', -1)

    def set_last_seen(self, timestamp: int) -> None:
        """Set the last seen timestamp

        Args:
            timestamp (float): the last seen timestamp to set
        """
        self.set_value('last_seen', timestamp)

    def get_data(self) -> str:
        """Return the user data

        Returns:
            str: the user data
        """
        return self.get('data', '')

    def set_data(self, data: str) -> None:
        """Set the data

        Args:
            data (str): the data to set
        """
        self.set_value('data', data)

    def get_antenna(self) -> int:
        """Return the antenna

        Returns:
            int: the antenna
        """
        return self.get('antenna', 0)

    def set_antenna(self, antenna: int) -> None:
        """Set the antenna

        Args:
            antenna (int): the antenna to set
        """
        self.set_value('antenna', antenna)

    def get_seen_count(self) -> int:
        """Return the seen count

        Returns:
            int: the seen count
        """
        count = self.get('seen_count')
        return count if count else 0

    def set_seen_count(self, seen_count: int) -> None:
        """Set the seen count

        Args:
            seen_count (int): the seen count to set
        """
        self.set_value('seen_count', seen_count)

    def has_error(self) -> bool:
        """Return true if the tag has a error message

        Returns:
            bool: true if the tag has a error message
        """
        return self.get('has_error', False)

    def get_error_message(self) -> str:
        """Return the error message

        Returns:
            str: the error message
        """
        return self.get('error_message', '')

    def set_error_message(self, message: str) -> None:
        """Set the error message

        Args:
            message (str): the error message to set
        """
        self.set_value('error_message', message)
        self.set_value('has_error', bool(message))

    def set_value(self, key: str, value) -> None:
        """Set a dictionary value

        Args:
            key (str): the key
            value (Any): the value to set
        """
        if value is not None:
            self[key] = value
        elif key in self:
            del self[key]


class UhfTag(Tag):
    """UHF Transponder class
    """

    def get_id(self) -> str:
        identifier: str = self.get_epc()
        return identifier if identifier else "unknown"

    def get_epc(self) -> str:
        """Return the epc

        Returns:
            str: the epc
        """
        return self.get('epc', '')

    def set_epc(self, epc: str) -> None:
        """Set the epc

        Args:
            epc (str): the epc to set
        """
        self.set_value('epc', epc)

    def get_rssi(self) -> int:
        """Return the rssi

        Returns:
            int: the rssi
        """
        return self.get('rssi', 0)

    def set_rssi(self, rssi: int) -> None:
        """Set the rssi

        Args:
            rssi (int): the rssi to set
        """
        self.set_value('rssi', rssi)


class ExpectedReaderInfo():
    """Expected reader info decorator
    """

    def __init__(self, firmware_name: str, hardware_name: str, min_firmware: float) -> None:
        """_summary_

        Args:
            firmware_name (str): firmware name
            hardware_name (str): hardware name
            min_firmware (str): minimum required firmware version
        """
        self._firmware_name = firmware_name
        self._hardware_name = hardware_name
        self._min_firmware = min_firmware

    def __call__(self, clazz):
        """
        Adds the property to the class properties field.
        Creates the field if needed.

        :param clazz: The class to decorate
        :return: The decorated class
        """
        properties = getattr(clazz, "_expected_reader", None)
        if not properties:
            properties = {}
            setattr(clazz, "_expected_reader", properties)
        properties["firmware_name"] = self._firmware_name
        properties["hardware_name"] = self._hardware_name
        properties["min_firmware"] = self._min_firmware
        return clazz


class RfidReaderGen2():
    """The base implementation of a rfid reader
    """

    def __init__(self, uart: UART):
        self._uart = uart
        self._initialise()

    def _prepare_command(self, command: str, *parameters) -> str:
        # prepare the command with the AT protocol style
        if not parameters:
            return command
        return command + "=" + ",".join(str(x) for x in parameters if x is not None)

    def _send_command(self, command: str, *parameters, timeout: int = 2000, command_response: bool = True) -> list[str]:
        send_command = self._prepare_command(command, *parameters)
        # print(f"send: {send_command}")
        self._uart.write((send_command + '\r').encode())
        max_time = ticks_ms() + timeout
        response: str = ""
        response_started = not command_response
        while True:
            resp = self._uart.readline()
            # print(f"recv1: {resp}")
            if resp is None:
                if max_time <= ticks_ms():
                    break
                else:
                    continue
            resp = resp[:-2]
            if not resp:
                continue
            resp = resp.decode()
            # print(f"recv2: {resp}")
            if response_started:
                if resp == 'OK':
                    return response.split("\r") if response else [""]
                if resp == 'ERROR':
                    try:
                        msg = response[response.rindex(
                            "<")+1:response.rindex(">")]
                    except ValueError:
                        msg = response
                    raise RfidReaderException(str(msg))
                response = resp
            else:
                if send_command in resp:
                    response_started = True
        if not response:
            raise RfidReaderException(f"no reader response for command {send_command}")
        raise RfidReaderException(f"wrong response for command {send_command} - {str(response)}")

    def _initialise(self):
        """Initialise and prepare the reader
        """
        self._uart.init(baudrate=115200, bits=8, parity=None, stop=1, timeout=500)
        self._send_command('ATE1', command_response=False)

    def get_reader_info(self) -> dict[str, str]:
        """Returns the reader information

        Raises:
            RfidReaderException: if an reader error occurs

        Returns:
            dict: With the 'firmware', 'firmware_version', 'hardware', 'hardware_version'
                  and 'serial_number' information
        """
        command: str = "ATI"
        response: list[str] = self._send_command(command)
        # +SW: PULSAR_LR 0100
        # +HW: PULSAR_LR 0100
        # +SERIAL: 2020090817420000
        try:
            firmware: list[str] = response[0].split(" ")
            hardware: list[str] = response[1].split(" ")
            serial: list[str] = response[2].split(" ")
            info: dict[str, str] = {
                'firmware': firmware[1],
                'firmware_version': firmware[2],
                'hardware': hardware[1],
                'hardware_version': hardware[2],
                'serial_number': serial[1]}
            expected = getattr(self, "_expected_reader", {})
            if info['hardware'] != expected.get('hardware_name', 'unknown'):
                raise RfidReaderException(
                    f"Wrong reader type! {expected.get('hardware_name','unknown')} expected, {info['hardware']} found")
            if info['firmware'] != expected.get('firmware_name', 'unknown'):
                raise RfidReaderException(f"Wrong reader firmware! {expected.get('firmware_name','unknown')} expected" +
                                          f", {info['firmware']} found")
            firmware_version = float(f"{info['firmware_version'][0:2]}.{info['firmware_version'][2:4]}")
            if firmware_version > expected.get('min_firmware', 1.0):
                raise RfidReaderException("Reader firmware too low, please update! " +
                                          f"Minimum {expected.get('min_firmware')} expected, {firmware_version} found")
            return info
        except IndexError as err:
            raise RfidReaderException(
                f"Wrong reader - Not expected info response - {response}") from err


class UhfReaderGen2(RfidReaderGen2):
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
        self.set_inventory_settings(False, True, True)

    def get_inventory_settings(self) -> dict:
        """Gets the current reader inventory settings

        Raises:
            RfidReaderException: if an reader error occurs

        Returns:
            dict: with 'only_new_tag', 'with_rssi' and 'with_tid' entries
        """
        response: list[str] = self._send_command("AT+INVS?")
        # +INVS: 0,1,0
        try:
            config: dict[str, bool] = {'only_new_tag': response[0][7] == '1',
                                       'with_rssi': response[0][9] == '1', 'with_tid': response[0][11] == '1'}
            return config
        except IndexError as err:
            raise RfidReaderException(
                f"Not expected response for command AT+INVS? - {response}") from err

    def set_inventory_settings(self, only_new_tag: bool = False, with_rssi: bool = True,
                               with_tid: bool = False) -> None:
        """Configure the inventory response

        Args:
            only_new_tag (bool, optional): Only return new tags. Defaults to False.

            with_rssi (bool, optional): Append the rssi value to the response. Defaults to True.

            with_tid (bool, optional): Append the tid to the response. Defaults to False.

        Raises:
            RfidReaderException: if an reader error occurs
        """
        self._send_command("AT+INVS", 1 if only_new_tag else 0, 1 if with_rssi else 0, 1 if with_tid else 0)

        # update configuration
        config = self._config.get('inventory', {})
        if not config:
            self._config['inventory'] = config
        config['only_new_tag'] = only_new_tag
        config['with_rssi'] = with_rssi
        config['with_tid'] = with_tid

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

    def get_inventory(self, ignore_error: bool = False) -> list[UhfTag]:
        """get the current inventory from the current antenna (see set_antenna)

        Raises:
            RfidReaderException: if an reader error occurs

        Returns:
            list[Tag]: An array with the founded transponder
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
            list[Tag]: An array with the founded transponder
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
        # +CINV: 3034257BF468D480000003EC,E200600311753E33,1755 +CINV=<ROUND FINISHED, ANT=2>
        # +INV: 0209202015604090990000145549021C,E200600311753F23,1807

        inventory: list[UhfTag] = []
        with_tid: bool = self._config['inventory']['with_tid']
        with_rssi: bool = self._config['inventory']['with_rssi']
        antenna: int = 0
        error: str = ''
        for response in responses:
            if response[0] != '+':
                continue
            if response[split_index] == '<':
                # inventory message, no tag
                # messages: Antenna Error / NO TAGS FOUND / ROUND FINISHED ANT=2
                if response[split_index+1] == 'N':  # NO TAGS FOUND
                    pass
                elif response[split_index+1] == 'R':
                    # ROUND FINISHED ANT2
                    try:
                        antenna = int(response[-2:-1])
                    except (IndexError, ValueError) as err:
                        print("Error parsing inventory response - %s", err)
                elif ignore_error:
                    pass
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


@ExpectedReaderInfo("QRG2", "QRG2", 1.3)
class QRG2(UhfReaderGen2):
    """The QRG2 is the first UHF RFID module that integrates all necessary components (read/write and antenna)
    into a single product. Just place the module in your machine and start using UHF RFID. This gives you the
    advantage of cheaper UHF transponders and longer read ranges at a price comparable to HF RFID systems.
    """


# uart0 = UART(0, baudrate=115200, tx=Pin(16), rx=Pin(17), bits=8, parity=None, stop=1, timeout=1000)
# reader = QRG2(uart0)

# try:
#     print("Get Reader Info: ")
#     print(reader.get_reader_info())
#     # reader.set_inventory_settings(False, False, True)
#     # print(reader.get_inventory())
#     reader.set_inventory_settings(False, False, False)
#     # print(reader.get_inventory())
#     print(reader.get_inventory_report())
# except RfidReaderException as exc:
#     print(f"Error: {exc}")
