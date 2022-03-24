# Diagnostic messages

In this file messages sent between heater and PC with diagnostic software are described. Aparently the messages vary depending on the type of heater and controller. 

Planar/Autoterm 4D/44D and PU-27 controller were used.

For better understanding the "Payload" and "Checksum" parts are separeted with `|`.

### Initialization:
These messages are used after connecting the PC to the heater. They probably contain information about the type of heater and controller.

```
PC >> H   aa 02 00 00 00 | a0 3d
PC >> H   aa 03 00 00 06 | 5e bc
 H >> PC  aa 04 05 00 06 | 03 01 0e 02 03 | 62 c1
```

### PC sends periodically:
Message sent periodically by PC without any heater response.

```
PC >> H   aa 02 00 00 00 | a0 3d
```

### Get heater software version:
Message sent from PC diagnostic software to find out heater software version.
```
PC >> H   aa 03 00 00 06 | 5e bc
 H >> PC  aa 04 05 00 06 | 03 01 0e 02 03 | 62 c1 
                           v1 v2 v3 v4
```
Software version consicts of `v1`.`v2`.`v3`.`v4` e.g. `3.1.14.2` 

### Heater errors:
Message sent by PC to list heater errors. In this case no errors were found.
```
PC >> H   aa 03 00 00 0f | 58 7c
 H >> PC  aa 04 0a 00 0f | 00 01 00 1d 7f 00 7d 01 41 00 | b8 f5
```
This message contains error 30 information.
```
PC >> H   aa 03 00 00 0f | 58 7c
 H >> PC  aa 04 0a 00 0f | 00 01 1e 18 7f 00 7c 01 42 00 | 34 21
                                 er
```

### Unblock button
Messege sent after "Unblock" button in the diagnostics software is pressed.
```
PC >> H   aa 03 00 00 0d | 99 fd
 H >> PC  aa 00 00 00 0d | dd fd
```

### Controlling heater:
This message is sent by PC to turn the heater on.

```
PC >> H   aa 03 02 00 01 | 00 28 | 27 39
 H >> PC  aa 04 06 00 01 | 00 28 04 0f 00 05 | bd ce
```

### Ventilation mode control:
This message is sent by PC to turn the ventilation mode on.

```
PC >> H   aa 03 01 00 08 | 60 | 05 5a
 H >> PC  aa 04 01 00 08 | 60 | c5 ef
```
Or to turn ventilation mode off.

```
PC >> H   aa 03 01 00 08 | 00 | 2d 5a
 H >> PC  aa 04 01 00 08 | 00 | ed ef
```

### Diagnostic mode:
PC sends this message to turn on the diagnostic mode on the heater.

```
PC >> H   aa 03 01 00 07 | 01 | 1d 9e
 H >> PC  aa 04 01 00 07 | 01 | dd 2b
```
After the diagnostic mode is switched on, the heater periodically sends messages that contain a lot of information.

```
 H >> PC  aa 02 48 00 01 | 000100000000049200000400000000000000012a012b00027f19007a00350244032803ff026201f8016b003d003403ff0000200000040f05000000000000000003ff000062000000 | 51 06
 H >> PC  aa 02 48 00 01 | 000100000000049300000500000000000000012a012b00027f19007a00350244032803ff026301f9016a003d003403ff0000200000040f05000000000000000003ff000062000000 | 80 e6
 H >> PC  aa 02 48 00 01 | 000100000000049400000600000000000000012a012b00027f19007a00350244032803ff026201f9016a003d003403ff0000200000040f05000000000000000003ff000062000000 | b3 58
 H >> PC  aa 02 48 00 01 | 000200000000056700000760600000000000012a012afe007f19007500350228032803ff026301f6016c003c003403fe0000200000040f0500000000000000000074000062000000 | 56 69
 H >> PC  aa 02 48 00 01 | 000200000000056800000860610000000000012a012a00fe7f1900750035022a032a03ff026301fd016a003c003403ff0000200000040f0500000000000000000074000063000000 | 53 39
 H >> PC  aa 02 48 00 01 | 000200000000056900000960600000000000012a012afefe7f19007500350228032903ff026301f8016b003c003403fe0000200000040f0500000000000000000074000063000000 | 05 ab
                           s1s2        c1c1  c2c2drmr          ctctftft    etht  bv
```
- `s1`: Status 1
- `s2`: Status 2
  - `00`: Heater off
  - `01`: Starting
  - `02`: Warming up
  - `03`: Running
  - `04`: Shutting down
- `c1`: Counter 1
- `c2`: Counter 2
- `dr`: Defined RPM
- `mr`: Measured RPM
- `ct`: Heater chamber temperature (as two bytes, big endian, in Kelvin)
- `ft`: Flame temperature (as two bytes, big endian, in Kelvin)
- `et`: External temperature (as single byte in °C, 7f when disconnected)
- `ht`: Heater temperature (as single byte in °C)
- `bv`: Battery voltage (as voltage * 10)

Diagnostic mode could be switch off with this message.

```
PC >> H   aa 03 01 00 07 | 00 | dd 5f
 H >> PC  aa 04 01 00 07 | 00 | 1d ea
```
