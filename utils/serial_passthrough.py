import serial

#use this when connecting to a PC with diagnostic software
#ser1 = serial.Serial('/dev/serial0', 2400, bytesize=serial.EIGHTBITS, parity=serial.PARITY_NONE, stopbits=serial.STOPBITS_ONE)

ser1 = serial.Serial('/dev/ttyUSB1', 2400, bytesize=serial.EIGHTBITS, parity=serial.PARITY_NONE, stopbits=serial.STOPBITS_ONE)
ser2 = serial.Serial('/dev/ttyUSB0', 2400, bytesize=serial.EIGHTBITS, parity=serial.PARITY_NONE, stopbits=serial.STOPBITS_ONE)

ser1.flushInput()
ser2.flushInput()

while True:
    if ser1.inWaiting() > 0:
        data = ser1.read()
        ser2.write(data)

        print('1: ', data)

        
    if ser2.inWaiting() > 0:
        data = ser2.read()
        ser1.write(data)

        print('2: ', data)
