# Autoterm Heater Controller
The purpose of this project is to control Planar (Autoterm) heater using Raspberry PI and Python. It also allows you to obtain information from the heater and pass it on.
I have a Planar (Autoterm) 4D (44D) diesel heater with PU-27 controller installed in my car. I would like to control the heater remotely, e. g. via SMS or over the Internet. Planar offers its own GSM modem, but I would like to use more SMS-based functionalities in my car with only one SIM card. 

## Introduction
The heater and the controller use a 5V UART interface. Communication is based on request – response model (controller sends request and heater responds to it). Communication happens on 1 s intervals. Messages have 16-bit checksum at the end (CRC16 MODBUS).
It is also possible to connect the heater to the computer either using original Autoterm “USB adapter for diagnostic equipment” (which is really expensive) or using any FT232 USB to UART (5V) board and obtain additional information from the heater with special Planar software. 

### Forwarding bytes
I bought two FT232 mini-USB to UART boards with selectable 5V or 3.3V interface level (like [this](https://www.aliexpress.com/item/32896631192.html?spm=a2g0o.12057483.product-detail-btn.1.d5643b97Qj3SNY)) and connected them to the Raspberry Pi with USB cables. I used jump wires to connect to the heater and the controller. First, I connected the heater (Rx, Tx, GND) and the Planar controller (Rx, Tx, GND). After some initial problems I created a simple serial passthrough program in Python (in my case the only usable bitrate was 2400). You can find the program in utils/serial_passthrough.py. Then I could connect the red wires from the heater and the controller (be careful, the red wire is +12 V and can destroy your Raspberry). The controller has turned on and initiated communication. On the Raspberry I was able to catch and read messages. With this simple program I was able to determine message structure. 
Message structure:
* byte 0: preamble (always 0xaa)
* byte 1: device (0x03 for messages from heater, 0x04 from the controller, 0x02 for some diagnostic messages)
* byte 2: payload length (uint8_t)
* byte 3: message ID1 (so far always 0x00)
* byte 4: message ID2
* byte 5+: payload

Last two bytes are checksum (CRC16, little endian Modbus) counted from all the bytes.

### Forwarding messages
Then I tried to detect and read the whole message for a better understanding. You can find the program in utils/message_passthrough.py. It detects a valid message that starts with 0xAA, then it reads the “device” byte and payload length, and the rest of the message. You can find further information about messages in [messages_controller.md](messages/messages_controller.md) file. 

### Diagnostics connection
I connected the heater to my computer via Raspberry to capture messages. One FT232 board is connected to Raspberry with USB cable and with jump wires to the heater. The other one (set to 3.3 V) is connected to Raspberry header pins GND, Tx, Rx and with USB cable to the computer. You also need to configure UART interface on your Raspberry (disable login shell accessible over serial and enable serial port hardware). With this setup, I detected several other messages from which more information about the heater can be obtained. See the [messages_diagnostic.md](messages/messages_diagnostic.md)  file for more information about these messages.

## Using autoterm_heater.py module
