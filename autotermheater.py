#!/usr/bin/python3
# -*- coding: utf-8 -*-

import logging
import serial
import serial.tools.list_ports as list_ports
import threading
import time

################
versionMajor = 0
versionMinor = 1
versionPatch = 2
################

status_text = {0: 'heater off', 1: 'starting', 2: 'warming up', 3: 'running', 4: 'shutting down'}


class Message:
    def __init__(self, preamble, device, length, msg_id1, msg_id2, payload=b''):
        self.preamble = preamble
        self.device = device
        self.length = length
        self.msg_id1 = msg_id1
        self.msg_id2 = msg_id2
        self.payload = payload


class AutotermUtils:
    def __init__(self, log_path, log_level=logging.DEBUG):
        self.logger = logging.getLogger(__name__)
        self.logger.setLevel(log_level)
        handler = logging.FileHandler(log_path)
        formatter = logging.Formatter(fmt='%(asctime)s  %(name)s %(levelname)s: %(message)s',
                                      datefmt='%d.%m.%Y %H:%M:%S')
        handler.setFormatter(formatter)
        handler.setLevel(logging.DEBUG)
        self.logger.addHandler(handler)

    @staticmethod
    def crc16(package: bytes):
        crc = 0xffff
        for byte in package:
            crc ^= byte
            for i in range(8):
                if (crc & 0x0001) != 0:
                    crc >>= 1
                    crc ^= 0xa001
                else:
                    crc >>= 1
        return crc.to_bytes(2, byteorder='big')

    def parse(self, package: bytes, min_packet_size=7):
        if len(package) < min_packet_size:
            self.logger.error('Parse: invalid length of package! ({})'.format(package.hex()))
            return 0
        while package[0] != 0xaa:
            if len(package) < min_packet_size:
                self.logger.error('Parse: invalid package! ({})'.format(package.hex()))
                return 0
            package = package[1:]
        if package[0] != 0xaa:
            self.logger.error('Parse: invalid bit 0 of package! ({})'.format(package.hex()))
            return 0
        if len(package) != int(package[2]) + min_packet_size:
            self.logger.error('Parse: invalid length of package! ({})'.format(package.hex()))
            return 0
        if package[1] not in [0x00, 0x02, 0x03, 0x04]:
            self.logger.error('Parse: invalid bit 1 of package! ({})'.format(package.hex()))
            return 0
        if package[-2:] != self.crc16(package[:-2]):
            self.logger.error('Parse: invalid crc of package! ({})'.format(package.hex()))
            return 0
        return Message(package[0], package[1], package[2], package[3], package[4], package[5:-2])

    def build(self, device, msg_id2, msg_id1=0x00, payload=b''):
        if device not in [0x00, 0x02, 0x03, 0x04]:
            self.logger.error('Built: invalid device! ({})'.format(device))
            return 0
        if msg_id1 not in range(256):
            self.logger.error('Built: invalid id1! ({})'.format(msg_id1))
            return 0
        if msg_id2 not in range(256):
            self.logger.error('Built: invalid id2! ({})'.format(msg_id1))
            return 0
        package = b'\xaa' + device.to_bytes(1, byteorder='big') \
                  + len(payload).to_bytes(1, byteorder='big') \
                  + msg_id1.to_bytes(1, byteorder='big') \
                  + msg_id2.to_bytes(1, byteorder='big') + payload
        return package + self.crc16(package)


class AutotermHeater(AutotermUtils):
    def __init__(self, log_path, serial_port1=None, baudrate1=2400, serial_port2=None, baudrate2=2400, serial_num=None,
                 log_level=logging.DEBUG):
        super().__init__(log_path, log_level)
        self.port1 = serial_port1
        self.baudrate1 = baudrate1
        self.port2 = serial_port2
        self.baudrate2 = baudrate2
        self.serial_num = serial_num

        self.logger = logging.getLogger(__name__)
        self.logger.setLevel(log_level)
        handler = logging.FileHandler(log_path)
        formatter = logging.Formatter(fmt='%(asctime)s  %(name)s %(levelname)s: %(message)s',
                                      datefmt='%d.%m.%Y %H:%M:%S')
        handler.setFormatter(formatter)
        handler.setLevel(logging.DEBUG)
        self.logger.addHandler(handler)

        self.logger.info('AutotermHeater v {}.{}.{} is starting.'.format(versionMajor, versionMinor, versionPatch))

        self._connected = False
        while not self._connected:
            self._connect()

        self._working = False
        self._start_working()

    def _write_message(self, ser_port, message):
        try:
            if ser_port.write(message) != len(message):
                self.logger.critical('Cannot send whole message to serial port {}!'.format(ser_port.port))
        except serial.serialutil.SerialException:
            self._connected = False
            self.logger.error('Cannot write to serial port {}!'.format(ser_port.port))

    def _message_waiting(self, ser_port):
        try:
            return ser_port.in_waiting
        except OSError:
            self._connected = False
            self.logger.error('Cannot check serial port {} for incoming messages!'.format(ser_port.port))
            return 0

    def _connect(self):
        if self.serial_num:
            # Search for USB devices based on serial number
            ports = [port.device for port in list_ports.comports() if port.serial_number == self.serial_num]
            if len(ports) == 0:
                self.logger.error('No serial adapters were found!')
                time.sleep(10)
            elif len(ports) == 1:
                self.port1 = ports[0]
                self.port2 = None
                self.logger.info('One serial adapter was found')
            elif len(ports) == 2:
                self.port1 = ports[0]
                self.port2 = ports[1]
                self.logger.info('Two serial adapters were found')
            else:
                self.logger.error('More than two serial adapters were found!')
                time.sleep(10)

        # Try to connect to one or both adapters
        if self.port1:
            try:
                self._ser1 = serial.Serial(self.port1, self.baudrate1, bytesize=serial.EIGHTBITS,
                                           parity=serial.PARITY_NONE, stopbits=serial.STOPBITS_ONE, timeout=0.5,
                                           write_timeout=0.5)
                self._ser1.reset_input_buffer()

                self._connected = True

                self.logger.info('Serial connection to ' + self.port1 + ' established')

            except serial.serialutil.SerialException:
                self.logger.critical('Cannot connect to serial port!')
                time.sleep(10)

        if self.port2:
            try:
                self._ser2 = serial.Serial(self.port2, self.baudrate2, bytesize=serial.EIGHTBITS,
                                           parity=serial.PARITY_NONE, stopbits=serial.STOPBITS_ONE, timeout=0.5,
                                           write_timeout=0.5)
                self._ser2.reset_input_buffer()

                self.logger.info('Serial connection to ' + self.port2 + ' established')

            except serial.serialutil.SerialException:
                self.logger.error('Cannot connect to serial port!')
                time.sleep(10)

        self._write_lock_timer = None
        self._write_lock_delay = 10

        self._ser_heater = None
        self._ser_controller = None

    def _disconnect(self):
        if self._ser1:
            self._ser1.close()
        if self._ser2:
            self._ser2.close()
        self._connected = False

    def _reconnect(self):
        self._disconnect()
        while not self._connected:
            self._connect()

    def _start_working(self):

        self._working = True

        # Buffer for messages
        self._send_to_heater = []

        self._heater_timer = None
        self._shutdown_request = False
        self._shutdown_timer = time.time()
        self._shutdown_delay = 10  # Sets how often raspberry sends messages to turn heater off

        # Heater info value
        # Following values are stored in tuples with timestamp
        self._heater_software_version = (None, None, None, None, None)
        self._heater_serial_number = (None, None, None)

        # Heater settings values
        self._settings_timer = time.time()
        self._settings_delay = 5  # Sets how often raspberry asks for settings
        # Following values are stored in tuples with timestamp
        self._heater_mode = (None, None)
        self._heater_setpoint = (None, None)
        self._heater_ventilation = (None, None)
        self._heater_power_level = (None, None)

        # Heater status values
        self._status_timer = time.time()
        self._status_delay = 5  # Sets how often raspberry asks for status
        # Following values are stored in tuples with timestamp
        self._heater_status1 = (None, None)
        self._heater_status2 = (None, None)
        self._heater_errors = (None, None)
        self._heater_temperature = (None, None)
        self._external_temperature = (None, None)
        self._battery_voltage = (None, None)
        self._flame_temperature = (None, None)

        # Controller temperature value
        # Following values are stored in tuples with timestamp
        self._controller_temperature = (None, None)

        # Diagnostic values
        # Following values are stored in tuples with timestamp
        self._d_status1 = (None, None)
        self._d_status2 = (None, None)
        self._d_counter1 = (None, None)
        self._d_counter2 = (None, None)
        self._d_defined_rev = (None, None)
        self._d_measured_rev = (None, None)
        self._d_fuel_pump1 = (None, None)
        self._d_fuel_pump2 = (None, None)
        self._d_chamber_temperature = (None, None)
        self._d_flame_temperature = (None, None)
        self._d_external_temperature = (None, None)
        self._d_heater_temperature = (None, None)
        self._d_battery_voltage = (None, None)

        # Create and start worker thread
        self._worker_thread = threading.Thread(target=self._worker_thread, daemon=True)
        self._worker_thread.start()

    def _stop_working(self):
        self._working = False
        self._worker_thread.join(10.0)

    def _process_message(self, message, ser_message):
        new_message = self.parse(message)

        if new_message == 0:
            return 0

        # Heater and controller port assignment
        if not self._ser_controller and new_message.device == 0x03:
            self._ser_controller = ser_message
        if not self._ser_heater and new_message.device == 0x04:
            self._ser_heater = ser_message

        # Initialization message received
        if new_message.device == 0x00:
            self.logger.info('Initialization message ({})'.format(message.hex()))

        # Diagnostic message received
        elif new_message.device == 0x02:
            if new_message.msg_id2 == 0x00:
                self.logger.info('PC sends initialization diagnostic message')
            # Diagnostic message from heater received
            elif new_message.msg_id2 == 0x01:
                if len(new_message.payload) == 72:
                    self._d_status1 = (new_message.payload[0], time.time())
                    self._d_status2 = (new_message.payload[1], time.time())
                    self._d_counter1 = (int.from_bytes(new_message.payload[5:8], 'big'), time.time())
                    self._d_counter2 = (int.from_bytes(new_message.payload[8:11], 'big'), time.time())
                    self._d_defined_rev = (new_message.payload[11], time.time())
                    self._d_measured_rev = (new_message.payload[12], time.time())
                    self._d_fuel_pump1 = (new_message.payload[14], time.time())
                    self._d_fuel_pump2 = (new_message.payload[16], time.time())
                    self._d_chamber_temperature = (int.from_bytes(new_message.payload[18:20], 'big'), time.time())
                    self._d_flame_temperature = (int.from_bytes(new_message.payload[20:22], 'big'), time.time())
                    self._d_external_temperature = (new_message.payload[24], time.time())
                    self._d_heater_temperature = (new_message.payload[25], time.time())
                    self._d_battery_voltage = (new_message.payload[27] / 10, time.time())
                    self.logger.info('Heater sends diagnostic message ({})'.format(new_message.payload.hex()))
                else:
                    self.logger.warning(
                        'Heater sends diagnostic message, wrong payload length ({})'.format(new_message.payload.hex()))

        # New message is from controller
        elif new_message.device == 0x03:
            # Do not send messages, waiting for response from the heater
            self._write_lock_timer = time.time() + self._write_lock_delay
            # 01 - Controller turns heater on
            if new_message.msg_id2 == 0x01:
                self._heater_timer = None
                self.logger.info('Controller turns heater on with settings {}'.format(new_message.payload[2:].hex()))
            # 02 - Controller asks for settings
            elif new_message.msg_id2 == 0x02:
                if new_message.length == 0:
                    self.logger.info('Controller asks for settings')
                else:
                    self._heater_timer = None
                    self.logger.info('Controller set new settings ({})'.format(new_message.payload[2:].hex()))
            # 03 - Controller turns off the heater
            elif new_message.msg_id2 == 0x03:
                self._heater_timer = None
                self.logger.info('Controller turns off the heater')
            # 04 - Controller asks for serial number
            elif new_message.msg_id2 == 0x04:
                self.logger.info('Controller asks for serial number')
            # 06 - Controller asks for software version
            elif new_message.msg_id2 == 0x06:
                self.logger.info('Controller asks for software version')
            # 07 - Controller asks for status
            elif new_message.msg_id2 == 0x0f:
                self.logger.info('Controller asks for status')
            # 11 - Controller reports temperature
            elif new_message.msg_id2 == 0x11:
                if len(new_message.payload) == 1:
                    self._controller_temperature = (new_message.payload[0], time.time())
                    self.logger.info('Controller reports temperature {} °C'.format(new_message.payload[0]))
                else:
                    self.logger.warning(
                        'Controller reports temperature, wrong payload length ({})'.format(new_message.payload.hex()))
            # 1c - Controller sends initialization message
            elif new_message.msg_id2 == 0x1c:
                self.logger.info('Controller sends initialization message')
            # 23 - Controller turns ventilation
            elif new_message.msg_id2 == 0x23:
                self.logger.info(
                    'Controller turns ventilation on with settings {}'.format(new_message.payload[2:].hex()))
            # Unknown message
            else:
                self.logger.warning('Unknown message from controller: {}'.format(message.hex()))

        # New message is from heater
        elif new_message.device == 0x04:
            # Response from heater received, can send other messages
            self._write_lock_timer = None
            # 01 - Heater confirms starting up
            if new_message.msg_id2 == 0x01:
                if len(new_message.payload) == 6:
                    self._heater_mode = (new_message.payload[2], time.time())
                    self._heater_setpoint = (new_message.payload[3], time.time())
                    self._heater_ventilation = (new_message.payload[4], time.time())
                    self._heater_power_level = (new_message.payload[5], time.time())
                    self.logger.info('Heater confirms starting up ({})'.format(new_message.payload.hex()))
                else:
                    self.logger.warning(
                        'Heater confirms starting up, wrong payload length ({})'.format(new_message.payload.hex()))
                # Reset settings timer
                self._settings_timer = time.time()
            # 02 - Heater reports settings
            elif new_message.msg_id2 == 0x02:
                if len(new_message.payload) == 6:
                    self._heater_mode = (new_message.payload[2], time.time())
                    self._heater_setpoint = (new_message.payload[3], time.time())
                    self._heater_ventilation = (new_message.payload[4], time.time())
                    self._heater_power_level = (new_message.payload[5], time.time())
                    self.logger.info('Heater reports settings ({})'.format(new_message.payload.hex()))
                else:
                    self.logger.warning(
                        'Heater reports settings, wrong payload length ({})'.format(new_message.payload.hex()))
                # Reset settings timer
                self._settings_timer = time.time()
            # 03 - Heater confirms turn off request
            elif new_message.msg_id2 == 0x03:
                self.logger.info('Heater confirms turn off request')
            # 04 - Heater reports serial number
            elif new_message.msg_id2 == 0x04:
                if len(new_message.payload) == 5:
                    self._heater_serial_number = (
                        int.from_bytes(new_message.payload[0:2], 'big'),
                        int.from_bytes(new_message.payload[2:5], 'big'),
                        time.time())
                    self.logger.info('Heater reports serial number ({})'.format(new_message.payload.hex()))
                else:
                    self.logger.warning(
                        'Heater reports serial number, wrong payload length ({})'.format(new_message.payload.hex()))
            # 06 - Heater reports software version
            elif new_message.msg_id2 == 0x06:
                if len(new_message.payload) == 5:
                    self._heater_software_version = (
                        new_message.payload[0], new_message.payload[1], new_message.payload[2], new_message.payload[3],
                        time.time())
                    self.logger.info('Heater reports software version ({})'.format(new_message.payload.hex()))
                else:
                    self.logger.warning(
                        'Heater reports software version, wrong payload length ({})'.format(new_message.payload.hex()))
            # 07 - Heater confirms turning on/off diagnostic mode
            elif new_message.msg_id2 == 0x07:
                if len(new_message.payload) == 1:
                    if new_message.payload[0] == 0:
                        self.logger.info('Heater confirms turning diagnostic mode off')
                    elif new_message.payload == 1:
                        self.logger.info('Heater confirms turning diagnostic mode on')
                    else:
                        self.logger.warning(
                            'Heater confirms turning diagnostic on/off, wrong payload value ({})'.format(
                                new_message.payload.hex()))
                else:
                    self.logger.warning('Heater confirms turning diagnostic on/off, wrong payload length ({})'.format(
                        new_message.payload.hex()))
            # 0f - Heater reports status
            elif new_message.msg_id2 == 0x0f:
                if len(new_message.payload) == 10:
                    self._heater_status1 = (new_message.payload[0], time.time())
                    self._heater_status2 = (new_message.payload[1], time.time())
                    self._heater_errors = (new_message.payload[2], time.time())
                    self._heater_temperature = (new_message.payload[3], time.time())
                    self._external_temperature = (new_message.payload[4], time.time())
                    self._battery_voltage = (new_message.payload[6] / 10, time.time())
                    self._flame_temperature = (int.from_bytes(new_message.payload[7:9], 'big'), time.time())
                    self.logger.info('Heater reports status ({})'.format(new_message.payload.hex()))
                else:
                    self.logger.warning(
                        'Heater reports status, wrong payload length ({})'.format(new_message.payload.hex()))
                # Reset status timer
                self._status_timer = time.time()
            # 11 - Heater confirms controller temperature
            elif new_message.msg_id2 == 0x11:
                if len(new_message.payload) == 1:
                    self.logger.info('Heater confirms controller temperature {} °C'.format(new_message.payload[0]))
                else:
                    self.logger.warning('Heater confirms controller temperature, wrong payload length ({})'.format(
                        new_message.payload.hex()))
            # 1c - Heater responds to initialization message
            elif new_message.msg_id2 == 0x1c:
                self.logger.info('Heater responds to initialization message')
            # 23 - Heater confirms turning ventilation on
            elif new_message.msg_id2 == 0x23:
                self.logger.info('Heater confirms turning ventilation on ({})'.format(new_message.payload.hex()))
            # Unknown message
            else:
                self.logger.warning('Unknown message from heater ({})'.format(message.hex()))
        # Unknown device id
        else:
            self.logger.warning('Unknown device id in message ({})'.format(message.hex()))
        # Message processed
        return 1

    def _worker_thread(self):
        self.logger.info('Worker started')

        while self._working:
            if not self._connected:
                self._reconnect()
            else:
                if self._message_waiting(self._ser1) > 0:
                    message = self._ser1.read(1)
                    if message == b'\x1b':
                        self._write_message(self._ser2, message)
                        self.logger.debug('Initialization message forwarded (1 >> 2: {})'.format(message.hex()))
                        continue
                    if message != b'\xaa':
                        self._ser1.reset_input_buffer()
                        self.logger.warning('Unknown message detected, disposed (1 >> 2: {})'.format(message.hex()))
                        continue
                    message += self._ser1.read(2)
                    message += self._ser1.read(message[-1] + 4)

                    self._write_message(self._ser2, message)
                    self.logger.debug('Message forwarded (1 >> 2: {})'.format(message.hex()))
                    self._process_message(message, self._ser1)

                if self._message_waiting(self._ser2) > 0:
                    message = self._ser2.read(1)
                    if message == b'\x1b':
                        self._write_message(self._ser1, message)
                        self.logger.debug('Initialization message forwarded (2 >> 1: {})'.format(message.hex()))
                        continue
                    if message != b'\xaa':
                        self._ser2.reset_input_buffer()
                        self.logger.warning('Unknown message detected, disposed (2 >> 1: {})'.format(message.hex()))
                        continue
                    message += self._ser2.read(2)
                    message += self._ser2.read(message[-1] + 4)

                    self._write_message(self._ser1, message)
                    self.logger.debug('Message forwarded (2 >> 1: {})'.format(message.hex()))
                    self._process_message(message, self._ser2)

                if self._write_lock_timer:
                    if time.time() >= self._write_lock_timer:
                        self.logger.error('Write lock timer has expired, the heater did not respond')
                        self._write_lock_timer = None

                if len(self._send_to_heater) > 0 and not self._write_lock_timer:
                    message = self._send_to_heater.pop(0)
                    if self._ser_heater:
                        self._write_message(self._ser_heater, message)
                        self.logger.info('Program sends message to heater ({})'.format(message.hex()))
                    else:
                        self._write_message(self._ser1, message)
                        self._write_message(self._ser2, message)
                        self.logger.warning('Program sends message to both adapters ({})'.format(message.hex()))
                    self._write_lock_timer = time.time() + self._write_lock_delay

                if self._heater_timer:
                    if time.time() >= self._heater_timer:
                        self.shutdown()

                if self._shutdown_request:
                    if self._heater_status1[0] == 0:
                        self._shutdown_request = False
                    elif time.time() > self._shutdown_timer + self._shutdown_delay:
                        message = self.build(0x03, 0x03)
                        if message != 0:
                            self._send_to_heater.append(message)
                        self._shutdown_timer = time.time()

                if time.time() >= self._status_timer + self._status_delay and not self._write_lock_timer:
                    self.asks_for_status()

                if time.time() >= self._settings_timer + self._settings_delay and not self._write_lock_timer:
                    self.asks_for_settings()

    # Heater and ventilation controlling
    def get_heater_timer(self):
        return self._heater_timer

    def set_heater_timer(self, timer):
        self._heater_timer = time.time() + (timer * 60)

    def shutdown(self):
        self._shutdown_request = True

    def turn_on_ventilation(self, power, timer=None):
        if timer:
            self._heater_timer = time.time() + (timer * 60)
        payload = b'\xff\xff' + power.to_bytes(1, byteorder='big') + b'\x0f'
        message = self.build(0x03, 0x23, payload=payload)
        if message != 0:
            self._send_to_heater.append(message)
            self._send_to_heater.append(message)
            # Message is sent twice as from the controller

    def turn_on_heater(self, mode, setpoint=0x0f, ventilation=0x00, power=0x00, timer=None):
        if timer:
            self._heater_timer = time.time() + (timer * 60)
        payload = b'\xff\xff' + mode.to_bytes(1, byteorder='big') \
                  + setpoint.to_bytes(1, byteorder='big') \
                  + ventilation.to_bytes(1, byteorder='big') \
                  + power.to_bytes(1, byteorder='big')
        message = self.build(0x03, 0x01, payload=payload)
        if message != 0:
            self._send_to_heater.append(message)
            self._send_to_heater.append(message)
            # Message is sent twice as from the controller

    def change_settings(self, mode, setpoint=0x0f, ventilation=0x00, power=0x00, timer=None):
        if timer:
            self._heater_timer = time.time() + (timer * 60)
        payload = b'\xff\xff' + mode.to_bytes(1, byteorder='big') \
                  + setpoint.to_bytes(1, byteorder='big') \
                  + ventilation.to_bytes(1, byteorder='big') \
                  + power.to_bytes(1, byteorder='big')
        message = self.build(0x03, 0x02, payload=payload)
        if message != 0:
            self._send_to_heater.append(message)
            self._send_to_heater.append(message)
            # Message is sent twice as from the controller

    # Heater info
    def ask_for_heater_software_version(self):
        message = self.build(0x03, 0x06)
        if message != 0:
            self._send_to_heater.append(message)

    def get_heater_software_version(self):
        return self._heater_software_version

    def ask_for_heater_serial_number(self):
        message = self.build(0x03, 0x04)
        if message != 0:
            self._send_to_heater.append(message)

    def get_heater_serial_number(self):
        return self._heater_serial_number

    # Heater settings
    def asks_for_settings(self):
        message = self.build(0x03, 0x02)
        if message != 0:
            self._send_to_heater.append(message)

    def get_heater_mode(self):
        return self._heater_mode

    def get_heater_setpoint(self):
        return self._heater_setpoint

    def get_heater_ventilation(self):
        return self._heater_ventilation

    def get_heater_power_level(self):
        return self._heater_power_level

    # Heater status
    def asks_for_status(self):
        message = self.build(0x03, 0x0f)
        if message != 0:
            self._send_to_heater.append(message)

    def get_heater_status(self):
        return self._heater_status1, self._heater_status2

    def get_heater_status_text(self):
        if self._heater_status1[0]:
            if self._heater_status1[0] in status_text.keys():
                return status_text[self._heater_status1[0]]
        return 'unknown status'

    def get_heater_errors(self):
        return self._heater_errors

    def get_heater_temperature(self):
        return self._heater_temperature

    def get_external_temperature(self):
        return self._external_temperature

    def get_battery_voltage(self):
        return self._battery_voltage

    def get_flame_temperature(self):
        return self._flame_temperature

    # Controller temperature
    def report_controller_temperature(self, temperature):
        payload = temperature.to_bytes(1, byteorder='big')
        message = self.build(0x03, 0x11, payload=payload)
        if message != 0:
            self._send_to_heater.append(message)
            self._controller_temperature = temperature

    def get_controller_temperature(self):
        return self._controller_temperature

    # Diagnostic
    def diagnostic_on(self):
        payload = b'\x01'
        message = self.build(0x03, 0x07, payload=payload)
        if message != 0:
            self._send_to_heater.append(message)

    def diagnostic_off(self):
        payload = b'\x00'
        message = self.build(0x03, 0x07, payload=payload)
        if message != 0:
            self._send_to_heater.append(message)

    def unblock(self):
        message = self.build(0x03, 0x0d)
        if message != 0:
            self._send_to_heater.append(message)

    def get_d_status(self):
        return self._d_status1, self._d_status2

    def get_d_counter1(self):
        return self._d_counter1

    def get_d_counter2(self):
        return self._d_counter2

    def get_d_defined_rev(self):
        return self._d_defined_rev

    def get_d_measured_rev(self):
        return self._d_measured_rev

    def get_d_fuel_pump1(self):
        return self._d_fuel_pump1

    def get_d_fuel_pump2(self):
        return self._d_fuel_pump2

    def get_d_chamber_temperature(self):
        return self._d_chamber_temperature

    def get_d_flame_temperature(self):
        return self._d_flame_temperature

    def get_d_external_temperature(self):
        return self._d_external_temperature

    def get_d_heater_temperature(self):
        return self._d_heater_temperature

    def get_d_battery_voltage(self):
        return self._d_battery_voltage
