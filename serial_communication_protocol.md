# Autoterm / Planar Serial Communication Protocol

## 1. Physical Layer

The physical connection between the Control Panel and the Heater Unit is a standard UART interface.

* **Interface:** UART (Universal Asynchronous Receiver-Transmitter)
* **Voltage Level:** 5V TTL (Logic High = 5V, Logic Low = 0V)
    * *Note:* A Logic Level Shifter is required when connecting to 3.3V microcontrollers (ESP32, Raspberry Pi).
* **Baud Rate:**
    * **9600 baud:** Standard for most modern Air 2D, 4D, and Flow 5D/14D heaters.
    * **2400 baud:** Legacy rate, found on some older Air 4D models and specific PU-27 controller versions.
* **Data Bits:** 8
* **Parity:** None (N)
* **Stop Bits:** 1

## 2. Message Frame Structure

Communication is packet-based. Every message, regardless of direction (Controller → Heater or Heater → Controller), follows this fixed byte structure.

The total length of a frame is **N + 7 bytes**, where N is the Payload Length.

| Byte Index | Field Name | Length | Description |
| :--- | :--- | :--- | :--- |
| **0** | **Sync/Preamble** | 1 Byte | Fixed: `0xAA`<br>Indicates the start of a new frame. |
| **1** | **Device Identifier** | 1 Byte | Identifies the device sending the message (see Section 3). |
| **2** | **Payload Length** | 1 Byte | The number of bytes in the **Payload** field (Index 5).<br>If `0x00`, the message contains no data payload. |
| **3** | **Command ID (High)** | 1 Byte | Fixed: `0x00`<br>High byte of the command identifier. In all observed traffic, this is `0x00`. |
| **4** | **Command ID (Low)** | 1 Byte | The specific command task identifier (see Section 4). |
| **5 ...** | **Payload** | *N* Bytes | Variable length data (defined by Byte 2).<br>Contains arguments for commands or sensor data in responses. |
| **Last - 1** | **CRC (Low)** | 1 Byte | CRC-16 Modbus (Low Byte) |
| **Last** | **CRC (High)** | 1 Byte | CRC-16 Modbus (High Byte) |


## 3. Field Definitions

### Byte 0: Sync/Preamble
* **Description:** The synchronization byte that marks the beginning of every frame.
* **Value:** `0xAA` (Fixed)
* **Function:** It is used by the receiver (Heater or Controller) to detect the start of a valid data packet in the serial stream.
* *Note:* Receivers should flush their buffer and wait for `0xAA` if a CRC error or timeout occurs.

### Byte 1: Device Identifier
* **Description:** Identifies the type of device that *originated* the message.
* **Values:**
    * `0x00`: **Boot / Init** – Temporary ID used by the heater during initialization/handshake immediately after power-up.
    * `0x02`: **Diagnostic Tool** – PC software or USB adapter. Has higher priority for specific commands (e.g., Unlock).
    * `0x03`: **Controller** – The Control Panel (PU-5, PU-27) or custom master device.
    * `0x04`: **Heater** – The Heater Unit (ECU).

### Byte 2: Payload Length
* **Description:** Defines the number of bytes contained *strictly* in the **Payload** section (starting at Byte 5).
* **Range:** `0x00` to `0xFF` (0–255)
* **Usage:**
    * If `0x00`: The message contains only the Header (5 bytes) and CRC (2 bytes). This is common for simple commands like **Stop** (`0x03`) or **Status Request** (`0x0F`).
    * If `> 0x00`: The receiver must read this many additional bytes before expecting the CRC.

### Byte 3: Command ID (High)
* **Description:** The Most Significant Byte (MSB) of the 16-bit Command Identifier.
* **Value:** `0x00` (Fixed/Reserved)
* **Function:** In all known Autoterm/Planar implementations (Air 2D/4D, Flow 5/14, Binar), this byte is **always** `0x00`. It acts as padding to align the protocol to 16-bit architecture or allow for future expansion of command IDs > 255.

### Byte 4: Command ID (Low)
* **Description:** The specific Task Identifier (LSB).
* **Common Values:**
    * `0x01`: **Start** – Triggers ignition sequence.
    * `0x02`: **Settings** – Updates configuration or requests current config.
    * `0x03`: **Stop** – Initiates shutdown and purge sequence.
    * `0x0F`: **Status** – Standard query for sensor data.
    * `0x11`: **Controller Temp** – Exchanges ambient temperature measured by the Controller.
        * *Note:* For other values see Section 4

### Byte 5 ... N: Payload
* **Description:** The data arguments for the command.
* **Length:** Variable (defined by Byte 2)
* *Note:* See the "Message IDs & Command Reference" section for specific byte maps per Command ID.

### Byte N+1, N+2: Checksum (CRC-16)
* **Algorithm:** CRC-16 Modbus
* **Length:** 2 Bytes
* **Byte Order:** Little Endian (Low Byte first, High Byte second).
* **Parameters:**
    * **Polynomial:** `0x8005` (x¹⁶ + x¹⁵ + x² + 1)
    * **Initial Value:** `0xFFFF`
    * **XOR Out:** `0x0000`
    * **Reflect Input:** True
    * **Reflect Output:** True
* **Calculation Scope:** The CRC is calculated over **all** preceding bytes in the frame (from `0xAA` at Byte 0 up to the last byte of the Payload).

## 4. Message IDs & Command Reference

The **Command ID** (Byte 4) determines the function of the packet.
### Quick Reference

| ID (Hex) | Name | Direction | Payload Length | Description |
| :--- | :--- | :--- | :--- | :--- |
| **0x01** | **Start** | Ctrl → Heater | 2 / 6 Bytes | Start Heater (Short/Long format) |
| **0x02** | **Settings** | Ctrl ↔ Heater | 6 Bytes | Update Config / Read Config |
| **0x03** | **Stop** | Ctrl → Heater | 0 Bytes | Shutdown |
| **0x04** | **Serial Number** | Ctrl ↔ Heater | 0 / 5 Bytes | Get Serial Number |
| **0x06** | **SW Version** | Ctrl ↔ Heater | 0 / 5 Bytes | Get Firmware Version |
| **0x07** | **Diag Mode** | Ctrl → Heater | 1 Byte | Enable Engineering Telemetry Stream |
| **0x08** | **Set Fan Speed** | Ctrl → Heater | 1 Byte | Direct Fan Control (Hz) |
| **0x0B** | **History** | Ctrl ↔ Heater | 0 / 7 / 9 Bytes | Get Run Hours & Error Log |
| **0x0D** | **Unlock** | Ctrl → Heater | 0 Bytes | Clear Error 37 (Lockout) |
| **0x0F** | **Status** | Ctrl ↔ Heater | 0 / 10 / 19 Bytes | Get Sensor Data |
| **0x11** | **Controller Temp** | Ctrl ↔ Heater | 1 Byte | Broadcast Ambient Temp |
| **0x13** | **Fuel Pump** | Ctrl → Heater | 1 Byte | Prime Pump (Hz) |
| **0x1C** | **Handshake** | Ctrl ↔ Heater | 0 Bytes | Power-up Init |
| **0x23** | **Ventilation** | Ctrl → Heater | 4 Bytes | Ventilation (Fan Only) Mode |

---
### 4.1. Operational Control

#### **`0x01`** - Start
Triggers the heater ignition sequence using the provided configuration parameters.

* **Direction:** Controller → Heater
* **Length:** 6 Bytes (Optionally 2 Bytes)
* **Packet Map:** `[T-Lim] [Time] [Mode] [Temp] [Wait] [Level]`
    * **T-Lim (Byte 0):** Time Limit Flag (`0`=Enabled, `1`=Unlimited)
    * **Time (Byte 1):** Work Time in Minutes (e.g., `0x78` = 120 Minutes)
    * **Mode (Byte 2):** Control Strategy
        * `1`: Temperature (Internal Sensor)
        * `2`: Temperature (Controller Sensor - requires 0x11 messages)
        * `3`: Temperature (External Sensor)
        * `4`: Power Level Mode (Manual)
    * **Temp (Byte 3):** Target Temperature (°C) (`1`-`30`)
    * **Wait (Byte 4):** Standby Mode
        * `0`: **Off** (Shutdown after reaching target temp)
        * `1`: **On** (Circulate air/standby after reaching target temp)
    * **Level (Byte 5):** Power Level (`0`-`9`) (Used if Mode = 4)
* **Simple Start Packet Map:** `[T-Lim] [Time]`
    * **T-Lim (Byte 0):** Time Limit Flag (`0`=Enabled, `1`=Unlimited)
    * **Time (Byte 1):** Work Time in Minutes (e.g., `0x78` = 120 Minutes)
    * *Note:* Heater returns the full configuration structure confirming the actual running state.

#### **`0x02`** - Settings
Updates configuration without triggering ignition (if Standby), or updates parameters live (if Running). Also used to read current config.

* **Direction:** Controller ↔ Heater
* **Length:** 6 Bytes
* **Packet Map:** `[T-Lim] [Time] [Mode] [Temp] [Wait] [Level]`
    * *Note:* Identical structure to **Start (Full)**
    * **T-Lim (Byte 0):** Time Limit Flag (`0` = Enabled, `1` = Unlimited)
    * **Time (Byte 1):** Work Time in Minutes (e.g., `0x78` = 120 Minutes)
    * **Mode (Byte 2):** Control Strategy
        * `1`: Temperature (Internal Sensor)
        * `2`: Temperature (Controller Sensor - requires 0x11 messages)
        * `3`: Temperature (External Sensor)
        * `4`: Power Level Mode (Manual)
    * **Temp (Byte 3):** Target Temperature (°C) (`1`-`30`)
    * **Wait (Byte 4):** Standby Mode
        * `0`: **Off** (Shutdown after reaching target temp)
        * `1`: **On** (Circulate air/standby after reaching target temp)
    * **Level (Byte 5):** Power Level (`0`-`9`) (Used if Mode = 4)

#### **`0x03`** - Stop
Initiates the shutdown sequence. The heater will stop fuel metering, burn off remaining fuel, and purge the chamber (fan runs high).
* **Direction:** Controller → Heater
* **Length:** 0 Bytes
* *Note:* The heater sends a status of "Cooling Down" (Code 3.4 / 0x0304) until fully stopped.

#### **`0x23`** - Ventilation
Activates "Fan Only" mode (turns on the intake fan without ignition). Air Heaters only.

* **Direction:** Controller → Heater
* **Length:** 4 Bytes
* **Packet Map:** `[T-Lim] [Time] [Level] [Unknown]`
    * **T-Lim (Byte 0):** Time Limit Flag (`0`=Enabled, `1`=Unlimited) **!NOT VERIFIED!**
    * **Time (Byte 1):** Work Time in Minutes (e.g., `0x78` = 120 Minutes) **!NOT VERIFIED!**
    * **Level (Byte 2):** Fan Speed Level (`0`-`9`)
    * **Unknown (Byte 3):** Typically `0x00`

---

### 4.2. Status & Telemetry

#### **`0x0F`** - Status
The primary poll command. Controller asks for status, Heater replies with sensor data.

* **Direction:** Controller ↔ Heater
* **Length:** 19 Bytes (Response, optionally 10 Bytes)

**Response Payload Map (0x0F Response):**

| Offset | Field Name | Format | Notes (Air vs. Liquid) |
| :--- | :--- | :--- | :--- |
| **0-1** | **Status Code** | `uint16` | Major.Minor State (e.g., `0x0300` = Running). |
| **2** | **Error Code** | `uint8` | `0x00` = No Error. |
| **3** | **Temp 1** | `int8` | **Air:** Intake Temp.<br>**Liquid:** Coolant Temp (°C). |
| **4** | **Temp 2** | `int8` | **Air:** Ext. Sensor / Output Temp.<br>**Liquid:** Intake Air Temp. |
| **5-6** | **Voltage** | `uint16` | Supply Voltage (V * 10). Big Endian. |
| **7-8** | **Flame Temp** | `uint16` | Heat Exchanger Temp (Kelvin). Big Endian. |
| **11** | **Fan Setpoint** | `uint8` | **Air:** Fan RPM (Hz).<br>**Liquid:** Blower RPM (Hz). |
| **12** | **Fan Actual** | `uint8` | **Air:** Fan RPM (Hz).<br>**Liquid:** Blower RPM (Hz). |
| **14** | **Fuel Pump** | `uint8` | Pump Frequency (Hz * 10). |
| **18** | **Water Pump** | `uint8` | **Liquid Only:** `0`=Off, `1`=On.<br>*(Unused on Air Heaters)*. |

*Note:* Some heater models or firmware versions may return a truncated **10-Byte Payload**. This contains the first 10 bytes of the standard structure below (Offsets 0–9).

#### **`0x11`** - Controller Temp
Is used to broadcast the ambient temperature measured by the external control panel's sensor to the heater. This allows the heater to regulate its output based on the cabin temperature.

* **Direction:** Controller ↔ Heater
* **Length:** 1 Byte
* **Packet Map:** `[Temp]`
    * **Temp (Byte 0):** Controller Temperature (`int8` °C).

---

### 4.3. Identification & Handshake

#### **`0x04`** - Serial Number
Retrieves the heater's unique 5-byte hardware identifier, composed of a 2-byte model/year prefix and a 3-byte unique serial number.

* **Direction:** Controller ↔ Heater
* **Length:** 5 Bytes (Response)
* **Packet Map:** `[Prefix] [Serial Number]`
    * **Prefix (Bytes 0-1):** Model/Year ID (`uint16`, Big Endian).
    * **Serial (Bytes 2-4):** Unique ID (`uint24`, Big Endian).

#### **`0x06`** - SW Version
Requests the firmware and bootloader version information from the heater's ECU to identify the installed software revision.

* **Direction:** Controller ↔ Heater
* **Length:** 5 Bytes (Response)
* **Packet Map:** `[Major] [Minor] [Patch] [Build] [Bootloader]`
    * **Major/Minor/Patch:** Firmware Version (e.g., 1.2.3).

#### **`0x1C`** - Handshake
Initiates the communication session between the controller and the heater immediately after power-up, serving as a "wake-up" signal to verify device presence. Heater may reply with Device ID `0x00`.

* **Direction:** Controller ↔ Heater
* **Length:** 0 Bytes

---

### 4.4. Diagnostics & Testing
*Typically used by factory tools.*

#### **`0x07`** - Diag Mode
Enable or disable a special high-frequency telemetry stream from the heater, typically used by factory calibration tools or PC software.

* **Direction:** Controller → Heater
* **Length:** 1 Byte
* **Packet Map:** `[State]`
    * **State (Byte 0):** `0` = Disable, `1` = Enable Telemetry

#### **`0x08`** - Set Fan Speed
Drive directly the intake fan at a specific speed (frequency), bypassing the heater's internal temperature regulation logic.

* **Direction:** Controller → Heater
* **Length:** 1 Byte
* **Packet Map:** `[Speed]`
    * **Speed (Byte 0):** Target fan frequency (Hz) (`0x00` = Stop, `0x14` = Min, `0x64` = Max)

#### **`0x0B`** - History
Retrieves the heater's lifetime operational statistics, including total run hours, the number of start cycles, and the last three recorded error codes.

* **Direction:** Controller ↔ Heater
* **Length:** 7 or 9 Bytes (Response)
* **Packet Map:** `[Time] [Starts] [Err 1] [Err 2] [Err 3] [Reserved]`
    * **Time (Bytes 0-1):** Total Run Time in Hours (`uint16`, Big Endian).
    * **Starts (Bytes 2-3):** Total Start Cycles (`uint16`, Big Endian).
    * **Err 1-3 (Bytes 4-6):** Most recent error codes.
    * **Reserved (Byte 7-8):** Optional, present in 9-byte response

#### **`0x0D`** - Unlock
Clears the "Error 37" hard lockout state caused by three consecutive overheat or failed start attempts, resetting the heater to allow normal operation.

* **Direction:** Controller → Heater
* **Length:** 0 Bytes

#### **`0x13`** - Fuel Pump
Activates the fuel metering pump at a specified frequency to prime the fuel lines and bleed air from the system during installation or maintenance.

* **Direction:** Controller → Heater
* **Length:** 1 Byte
* **Packet Map:** `[Frequency]`
    * **Frequency (Byte 0):** Pump Rate in Hz (`0x01`–`0xFF`).

## 5. Status Codes (Bytes 0 & 1 of Status Response)

The first two bytes of the Status Response (`0x0F`) form the Operational State.
* **Byte 0:** Major State (Mode)
* **Byte 1:** Minor State (Sub-process)

| Hex | State (Major.Minor) | Description |
| :--- | :--- | :--- |
| **0x00 00** | 0.0 | Sleep / Off |
| **0x00 01** | 0.1 | Standby (Waiting for command) |
| **0x01 00** | 1.0 | Purge: Cooling Flame Sensor |
| **0x01 01** | 1.1 | Purge: Ventilating Combustion Chamber |
| **0x02 01** | 2.1 | Pre-Heat (Glow Plug On) |
| **0x02 02** | 2.2 | Ignition Sequence 1 |
| **0x02 03** | 2.3 | Ignition Sequence 2 |
| **0x02 04** | 2.4 | Ramp Up (Stabilizing Combustion) |
| **0x03 00** | 3.0 | Heating (Running - PID Active) |
| **0x03 23** | 3.35 | Ventilation Mode (Fan Only) |
| **0x03 04** | 3.4 | Cooling Down (Stopping) |
| **0x04 00** | 4.0 | Shutdown Complete |

## 6. Error Codes (Byte 2 of Status Response)

These codes appear in **Byte 2** of the Status Response (`0x0F`) when a fault occurs.

| Code (Dec) | Code (Hex) | Description | Specific Notes (Air vs. Liquid) |
| :--- | :--- | :--- | :--- |
| **0** | **0x00** | **No Error** | Normal Operation. |
| **1** | **0x01** | **Overheat** | **Air:** Heat Exchanger > 250°C (Check Intake/Outlet).<br>**Liquid:** Coolant > 102°C (Check Water Pump/Airlock). |
| **2** | **0x02** | **Potential Overheat** | Measured temp > 55°C at shutdown (Purge failed to cool). |
| **5** | **0x05** | **Flame Sensor Fault** | Sensor Open/Short circuit. |
| **6** | **0x06** | **Temperature Sensor Fault** | **Air:** Intake Air Sensor.<br>**Liquid:** Coolant Temp Sensor. |
| **9** | **0x09** | **Glow Plug Fault** | Open/Short circuit or wrong resistance. |
| **10** | **0x0A** | **Motor RPM Fault** | Fan/Blower motor not spinning or seized. |
| **11** | **0x0B** | **Air Temperature Fault** | **Air:** Intake sensor disconnected.<br>**Liquid:** *Unused*. |
| **12** | **0x0C** | **Over Voltage** | > 30V (24V system) or > 16V (12V system). |
| **13** | **0x0D** | **No Start** | Failed to ignite after 2 automatic attempts. |
| **14** | **0x0E** | **Water Pump Fault** | **Liquid Only:** Water pump Open/Short circuit. |
| **15** | **0x0F** | **Under Voltage** | < 20V (24V system) or < 10V (12V system). |
| **16** | **0x10** | **Ventilation Duration** | Ventilation time exceeded (during shutdown). |
| **17** | **0x11** | **Fuel Pump Fault** | Fuel Pump Open/Short circuit. |
| **20** | **0x14** | **No Communication** | Heater not receiving data from Controller/Modem. |
| **29** | **0x1D** | **Flame Blowout** | Flame lost during operation (run mode). |
| **30** | **0x1E** | **Flame Detection** | Flame detected *before* start (Sensor stuck high). |
| **31** | **0x1F** | **Overheat (Exit)** | **Air:** Outlet temperature sensor overheat. |
| **33** | **0x21** | **Control Lockout** | Heater locked due to 3 consecutive Overheats. |
| **37** | **0x25** | **Locked (Hard)** | **CRITICAL:** 3 consecutive Start Failures or Overheats.<br>*Requires Unlock Command (`0x0D`) to reset.* |
| **78** | **0x4E** | **Flame Failure** | **Liquid Only:** Flame lost during run & restart failed. |

## 7. Data Encoding & Formulas

### 7.1. Temperature Encoding
* **Type A (Internal, External, Controller Sensors):** 8-bit Signed Integer (`int8`).
    * `Range: -128°C to +127°C`
* **Type B (Flame Sensor):** 16-bit Unsigned Integer (**Big Endian**) in **Kelvin**.
    * `Temp (°C) = ((Byte7 << 8) | Byte8) - 273.15`

### 7.2. Voltage Encoding
Voltage is a 16-bit Big Endian integer spanning **Byte 5 and Byte 6**.
* **Formula:** `Voltage = ((Byte5 << 8) | Byte6) / 10.0`
* *Note:* Byte 5 is non-zero for 24V systems (Values > 25.5V).

### 7.3. Fan RPM
Fan speed is transmitted as Frequency (Hz).
* **Formula:** `RPM = Byte_Val * 60`

### 7.4. Fuel Pump
Pump speed is transmitted as Frequency * 10.
* **Formula:** `Hz = Byte_Val / 10.0`