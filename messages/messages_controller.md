# Controller messages 

This file describes which messages are used for communication between the heater and the controller. Aparently the messages vary depending on the type of heater and controller. 

Planar/Autoterm 4D/44D and PU-27 controller were used.

For better understanding the "Payload" and "Checksum" parts are separeted with `|`.

### Initialization:
These messages are used after connecting the controller to the heater. They probably contain information about the type of heater and controller.

```
C >> H  1b
C >> H  1b
C >> H  1b
C >> H  1b
C >> H  1b
C >> H  1b
C >> H  1b
C >> H  1b
C >> H  1b
C >> H  1b
C >> H  1b
C >> H  1b
C >> H  aa 03 00 00 1c | 95 3d
H >> P  aa 00 00 00 1c | d1 3d
C >> H  aa 03 00 00 04 | 9f 3d
H >> P  aa 04 05 00 04 | 12 9e 00 15 80 | 05 3d
C >> H  aa 03 00 00 06 | 5e bc
H >> P  aa 04 05 00 06 | 03 01 0e 02 03 | 62 c1
C >> H  aa 03 00 00 06 | 5e bc
H >> P  aa 04 05 00 06 | 03 01 0e 02 03 | 62 c1
```

### Status:
Controller asks for heater status, polls this one periodically.

```
C >> H aa 03 00 00 0f | 58 7c
H >> C aa 04 0a 00 0f | 00 01 00 1a 7f 00 7b 01 2b 00 | 50 ad
                        s1 s2 er ht et    bv ft ft
```
- `s1`: Status
  - `00`: Heater off
  - `01`: Starting
  - `02`: Warming up
  - `03`: Running
  - `04`: Shutting down
- `er`: Heater errors
- `ht`: Heater temperature (as single byte in °C)
- `et`: External temperature (as single byte in °C, 7f when disconnected)
- `bv`: Battery voltage (as voltage * 10)
- `ft`: Heater flame temperature (as two bytes, big endian, in Kelvin)

### Controller temperature:
These messages are used by the controller to report the temperature to the heater. Heater confirms and repeat the same temperature.

```
C >> H  aa 03 01 00 11 | 1a | 76 d0
H >> C  aa 04 01 00 11 | 1a | b6 65
                         ct
```
- `ct`: Controller temperature (as single byte in °C)

### Get/set settings:
The controller asks the heater for the current setting.

```
C >> H  aa 03 00 00 02 | 9d bd
H >> C  aa 04 06 00 02 | 00 78 04 0f 00 02 | 73 7c
                               md ts vt pl
```
Or the controller sends new settings to the heater.

```
C >> H  aa 03 06 00 02 | ff ff 04 0f 00 01 | b9 2d
H >> C  aa 04 06 00 02 | 00 78 04 0f 00 01 | 72 3c
                               md ts vt pl
```
- `md`: Mode
  - `01`: By heater temperature
  - `02`: By controller temperature
  - `03`: By external temperature
  - `04`: By power
- `ts`: Temperature setpoint in °C as a single byte
- `vt`: Ventilation
  - `01`: On
  - `02`: Off
- `pl`: Power level (0-9)

### Shutdown:
This message is sent by the controller to turn off the heater. It repeats it every 10 s until the heater turns off. 

```
C >> H  aa 03 00 00 03 | 5d 7c
H >> C  aa 04 00 00 03 | 29 7d
```

### Start ventilation:
When the ventilation is switched on, the controller sends a message to the heater with the settings. It is sent twice in short succession. 

```
C >> H  aa 03 04 00 23 | ff ff 02 0f | 05 0d
H >> C  aa 04 04 00 23 | 00 78 02 32 | 0f 0d
C >> H  aa 03 04 00 23 | ff ff 02 0f | 05 0d
H >> C  aa 04 04 00 23 | 00 78 02 3b | 09 cd
                               pl
```
- `pl`: Power level (0-9)

### Start heater:
This message turns on the heater with selected settings. Heater confirms it in response. It is sent twice in short succession. 
```
C >> H  aa 03 06 00 01 | ff ff 04 0f 00 02 | b8 5e
H >> C  aa 04 06 00 01 | 00 78 04 0f 00 02 | 73 4f
C >> H  aa 03 06 00 01 | ff ff 04 0f 00 02 | b8 5e
H >> C  aa 04 06 00 01 | 00 78 04 0f 00 02 | 73 4f
                               md ts vt pl
```
- `md`: Mode
  - `01`: By heater temperature
  - `02`: By controller temperature
  - `03`: By external temperature
  - `04`: By power
- `ts`: Temperature setpoint in °C as a single byte
- `vt`: Ventilation
  - `01`: On
  - `02`: Off
- `pl`: Power level (0-9)
