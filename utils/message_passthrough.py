import serial

#use this when connecting to a PC with diagnostic software
#ser1 = serial.Serial('/dev/serial0', 2400, bytesize=serial.EIGHTBITS, parity=serial.PARITY_NONE, stopbits=serial.STOPBITS_ONE)

ser1 = serial.Serial('/dev/ttyUSB1', 2400, bytesize=serial.EIGHTBITS, parity=serial.PARITY_NONE, stopbits=serial.STOPBITS_ONE)
ser2 = serial.Serial('/dev/ttyUSB0', 2400, bytesize=serial.EIGHTBITS, parity=serial.PARITY_NONE, stopbits=serial.STOPBITS_ONE)

ser1.flushInput()
ser2.flushInput()

while True:
    if ser1.inWaiting() > 0:
        message = ser1.read(1)
        if message != b'\xaa':
            ser2.write(message)
            print('1 >> 2: ERROR: ', message)
            continue
        message += ser1.read(2)
        message += ser1.read(message[-1]+4)

        ser2.write(message)
        
        print('1 >> 2: ', (message).hex())

 
    if ser2.inWaiting() > 0:
        message = ser2.read(1)
        if message != b'\xaa':
            ser1.write(message)
            print('2 >> 1: ERROR: ', message)
            continue
        message += ser2.read(2)
        message += ser2.read(message[-1]+4)

        ser1.write(message)

        print('2 >> 1: ', (message).hex())

        

