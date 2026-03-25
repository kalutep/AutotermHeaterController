# Comfort Panel with Autoterm 44D


### Initial Boot Handshake
* **Purpose:** Executed exactly once when the control panel is powered on.
* **Behavior:** The controller wakes up and immediately requests static hardware identity data to populate its internal memory. Once this data is received, the standard polling loop sequence starts.
* **Command Sequence:**
  * **`0x06`**: Software Version Request
  * **`0x04`**: Serial Number Request

| Time | Direction | Raw Message | Decoded Message | Description |
| :--- | :--- | :--- | :--- | :--- |
| **`T+0s`** | **C » H** | `AA 03 00 00 06 5E BC` | **`0x06`**: Software Version Request | The controller wakes up and asks the heater for its active firmware version. |
| **`T+0s`** | **H » C** | `AA 04 05 00 06 03 01 0E 02 03 62 C1` | **`0x06`**: Software Version Report | Heater replies with its 5-byte firmware version: **3.1.14.2.3** (`0E` hex = 14). |
| **`T+2s`** | **C » H** | `AA 03 00 00 04 9F 3D` | **`0x04`**: Serial Number Request | Controller asks for the hardware identity (Product Code and Serial Number). |
| **`T+2s`** | **H » C** | `AA 04 05 00 04 12 9E 00 15 80 05 3D` | **`0x04`**: Serial Number Report | Heater replies. Product Code: **4766** (`12 9E`). Serial Number: **5504** (`00 15 80`). |
| **`T+2s`** | **C » H** | `AA 03 00 00 02 9D BD` | **`0x02`**: Settings Request | Controller asks the heater for its currently active session configuration. |
| **`T+2s`** | **H » C** | `AA 04 06 00 02 00 78 02 0F 00 01 FA 3C` | **`0x02`**: Settings Report | Heater confirms: 120m Timer (`00 78`), Panel Mode (`02`), Target 15°C (`0F`), Fan Lvl 1 (`01`). |
| **`T+3s`** | **C » H** | `AA 03 00 00 0F 58 7C` | **`0x0F`**: Status Request | Controller begins the standard telemetry loop, asking for live sensor data. |
| **`T+3s`** | **H » C** | `AA 04 0A 00 0F 00 01 00 15 7F 00 83 01 2E 00 60 60` | **`0x0F`**: Status Report | Heater confirms Standby (`00 01`), Int Temp 21°C (`15`), 13.1V (`00 83`), Chamber 29°C (`01 2E`). |
| **`T+4s`** | **C » H** | `AA 03 01 00 11 14 B2 51` | **`0x11`**: Thermostat Broadcast | Controller pushes its internal ambient room temperature to the heater (Hex `14` = **20°C**). |
| **`T+4s`** | **H » C** | `AA 04 01 00 11 14 72 E4` | **`0x11`**: Thermostat Confirm | Heater echoes the `14` byte, acknowledging the room is currently 20°C. |

### Standard Idle Polling Loop (3 Full Cycles)
* **Purpose:** The steady-state heartbeat of the heater, repeating every ~3 seconds.
* **Behavior:** Immediately following the handshake, the controller falls into an infinite 3-part loop. It passively verifies that the target settings haven't changed, requests live sensor data (voltage, state, internal temperatures), and constantly pushes the latest ambient room temperature to the heater's ECU.
* **Command Sequence:**
  * **`0x02`**: Settings Request *(Passive limit/target check)*
  * **`0x0F`**: Status Request *(Live sensor telemetry)*
  * **`0x11`**: Thermostat Broadcast *(Ambient room temp update)*

| Time | Direction | Raw Message | Decoded Message | Description |
| :--- | :--- | :--- | :--- | :--- |
| **`T+0s`** | **C » H** | `AA 03 00 00 02 9D BD` | **`0x02`**: Settings Request | Controller passively checks if active settings have changed. |
| **`T+0s`** | **H » C** | `AA 04 06 00 02 00 78 02 0F 00 01 FA 3C` | **`0x02`**: Settings Report | Heater confirms: 120m limit (`00 78`), Mode 2, Target 15°C (`0F`). |
| **`T+1s`** | **C » H** | `AA 03 00 00 0F 58 7C` | **`0x0F`**: Status Request | Controller asks for live sensor telemetry. |
| **`T+1s`** | **H » C** | `AA 04 0A 00 0F 00 01 00 15 7F 00 83 01 2E 00 60 60` | **`0x0F`**: Status Report | Heater confirms it is in Standby (`00 01`), Int Temp 21°C (`15`), 13.1V (`00 83`). |
| **`T+2s`** | **C » H** | `AA 03 01 00 11 12 B2 51` | **`0x11`**: Thermostat Broadcast | Controller broadcasts room temp of 18°C (`12` Hex). |
| **`T+2s`** | **H » C** | `AA 04 01 00 11 12 72 E4` | **`0x11`**: Thermostat Confirm | Heater echoes the `12` payload, acknowledging the temperature is 18°C. |
| **`T+3s`** | **C » H** | `AA 03 00 00 02 9D BD` | **`0x02`**: Settings Request | Controller checks settings again. |
| **`T+3s`** | **H » C** | `AA 04 06 00 02 00 78 02 0F 00 01 FA 3C` | **`0x02`**: Settings Report | Heater replies with identical settings data. |
| **`T+4s`** | **C » H** | `AA 03 00 00 0F 58 7C` | **`0x0F`**: Status Request | Controller checks telemetry again. |
| **`T+4s`** | **H » C** | `AA 04 0A 00 0F 00 01 00 15 7F 00 83 01 2E 00 60 60` | **`0x0F`**: Status Report | Heater returns identical telemetry data, remaining safely in Standby. |
| **`T+5s`** | **C » H** | `AA 03 01 00 11 14 B2 51` | **`0x11`**: Thermostat Broadcast | Controller broadcasts temp of 20°C (`14` Hex). |
| **`T+5s`** | **H » C** | `AA 04 01 00 11 14 72 E4` | **`0x11`**: Thermostat Confirm | Heater acknowledges the 20°C reading. |
| **`T+6s`** | **C » H** | `AA 03 00 00 02 9D BD` | **`0x02`**: Settings Request | **[LOOP 3]** Controller checks settings for the third time. |
| **`T+6s`** | **H » C** | `AA 04 06 00 02 00 78 02 0F 00 01 FA 3C` | **`0x02`**: Settings Report | Heater replies with identical settings data. |
| **`T+7s`** | **C » H** | `AA 03 00 00 0F 58 7C` | **`0x0F`**: Status Request | Controller asks for live sensor telemetry. |
| **`T+7s`** | **H » C** | `AA 04 0A 00 0F 00 01 00 15 7F 00 83 01 2E 00 60 60` | **`0x0F`**: Status Report | Heater confirms identical status and temperatures. |
| **`T+8s`** | **C » H** | `AA 03 01 00 11 14 B2 51` | **`0x11`**: Thermostat Broadcast | Controller broadcasts 20°C (`14` Hex) again. |
| **`T+8s`** | **H » C** | `AA 04 01 00 11 14 72 E4` | **`0x11`**: Thermostat Confirm | Heater echoes the `14` payload. |

### Heater Ignition Sequence
* **Purpose:** To explicitly command the heater to exit Standby and begin the physical combustion process using a specific operational profile.
* **Behavior:** The controller sends a Turn ON command using a payload with `FF` (Ignore/Keep) masks to selectively retain existing settings (like the timer) while updating others (like the power level). Once the heater confirms the merged profile, the controller immediately sends a Settings Request to "lock" this profile into the heater's memory. The heater's internal state machine then takes over, transitioning through the physical ignition phases (Glow Plug Warming, Fuel Delivery, Flame Stabilization), which are monitored via the standard polling loop.
* **Command Sequence:**
  * **`0x01`**: Heater ON Request *(Initiates startup using a masked settings profile)*
  * **`0x02`**: Settings Request *(Immediately verifies and locks the active profile)*

| Time | Direction | Raw Message | Decoded Message | Description |
| :--- | :--- | :--- | :--- | :--- |
| **`T+0s`** | **C » H** | `AA 03 06 00 01 FF FF 04 FF 02 01 EA 1F` | **`0x01`**: Heater ON Request | Controller sends the Start command. It uses `FF` masks to say: *Keep Timer, Set Power 4, Keep Target Temp, Use Panel Mode.* |
| **`T+0s`** | **H » C** | `AA 04 06 00 01 00 28 04 0F 02 01 1E CE` | **`0x01`**: Heater ON Confirm | Heater accepts the start command and fills in the `FF` blanks: *40m Timer (`00 28`), Power 4, 15°C Target (`0F`).* |
| **`T+1s`** | **C » H** | `AA 03 00 00 02 9D BD` | **`0x02`**: Settings Request | Standard loop check: Controller asks the heater for its current active profile. |
| **`T+1s`** | **H » C** | `AA 04 06 00 02 00 28 04 0F 02 01 1E FD` | **`0x02`**: Settings Report | Heater confirms the new heating profile is active in its memory. |
| **`T+1s`** | **C » H** | `AA 03 06 00 02 FF FF 04 FF 02 01 EA 2C` | **`0x02`**: Settings Lock | Controller explicitly writes/locks the same masked profile back to the heater to ensure settings sync. |
| **`T+1s`** | **H » C** | `AA 04 06 00 02 00 28 04 0F 02 01 1E FD` | **`0x02`**: Settings Confirm | Heater confirms the locked settings. The physical ignition process now begins! |

### Mid-Operation Settings Change
* **Purpose:** To adjust active heating parameters (like target power, target temperature, or panel mode features) on the fly without interrupting the combustion process.
* **Behavior:** Instead of sending a Turn ON (`0x01`) command, the controller simply pushes a Settings Lock (`0x02`) command populated with the new desired values. It uses `FF` masks for the parameters it wants to leave alone, and specifies the new hex values for the parameters it wants to change. The heater accepts the new profile, saves it, and instantly applies it to the active running session.
* **Command Sequence:**
  * **`0x02`**: Settings Request/Lock *(Pushes masked profile mid-operation)*

| Relative Time | Direction | Raw Hex Message | Message (Decoded) | Description |
| :--- | :--- | :--- | :--- | :--- |
| **`T+0s`** | **C » H** | `AA 03 06 00 02 FF FF 04 FF 02 07 E8 AC` | **`0x02`**: Settings Request | Controller pushes a settings update mid-operation. Notice the last byte changed to `07`, while others retain the `FF` "ignore" mask. |
| **`T+0s`** | **H » C** | `AA 04 06 00 02 00 28 04 0F 02 07 1C 7D` | **`0x02`**: Settings Report | Heater confirms the new profile is active: *40m Timer (`00 28`), Mode 4, Target 15°C (`0F`), Vent 2, Level 8 (`07`).* |

### Shutdown Sequence
* **Purpose:** Safely extinguishes the combustion flame and cools the internal ceramic heat exchanger to prevent hardware damage from residual heat.
* **Behavior:** The controller sends a simple, dedicated Turn OFF (`0x03`) request. The heater immediately cuts power to the fuel pump and transitions its internal state from `03.xx` (Main Heating) to `04.xx` (Cool-Down Phase). During this phase, the primary fan runs at high speed to purge exhaust gases and shed heat. The standard polling loop continues to monitor the dropping temperatures. Once the internal heat exchanger drops below a safe threshold (roughly 57°C, taking 4 to 5 minutes), the heater autonomously turns off the fan and drops back to `00.01` (Standby).
* **Command Sequence:**
  * **`0x03`**: Turn OFF Request
  * **`0x0F`**: Status Request *(Monitors state change to `04.00` and eventually `00.01`)*
* *Note: Comfort Panel sends shutdown request only once.*

| Relative Time | Direction | Raw Hex Message | Message (Decoded) | Description |
| :--- | :--- | :--- | :--- | :--- |
| **`T+0s`** | **C » H** | `AA 03 00 00 03 5D 7C` | **`0x03`**: Turn OFF Request | Controller issues the hard stop command. |
| **`T+0s`** | **H » C** | `AA 04 00 00 03 29 7D` | **`0x03`**: Turn OFF Confirm | Heater acknowledges the command and cuts the fuel pump immediately. |
| **`T+3s`** | **C » H** | `AA 03 00 00 0F 58 7C` | **`0x0F`**: Status Request | Controller checks live telemetry in the standard polling loop. |
| **`T+3s`** | **H » C** | `AA 04 0A 00 0F 04 00 00 19 7F 00 80 01 D6...` | **`0x0F`**: Status Report | Heater confirms State **`04.00`** (Cool-Down Phase). Exchanger Temp is at 197°C (`01 D6`). Fan is running high. |
| **`...`** | | | | *(~4.5 Minutes pass as the polling loop watches the temperature drop)* |
| **`T+266s`**| **C » H** | `AA 03 00 00 0F 58 7C` | **`0x0F`**: Status Request | Controller checks live telemetry. |
| **`T+266s`**| **H » C** | `AA 04 0A 00 0F 00 01 00 11 7F 00 83 01 4A...` | **`0x0F`**: Status Report | Exchanger Temp has dropped to 57°C (`01 4A`). Heater confirms it has returned to State **`00.01`** (Standby). Fan is OFF. |

### Standalone Ventilation Mode
* **Purpose:** To run the internal blower fan for air circulation without igniting the combustion burner or engaging the fuel pump.
* **Behavior:** Instead of using the standard `0x01` Heater ON command, the controller issues a dedicated `0x23` Ventilation ON request containing the desired timer and fan speed level. Once confirmed, the heater transitions its internal state to `03.23` (Ventilation Mode). Because the burner is never ignited and the heat exchanger remains at ambient temperature, issuing a Turn OFF (`0x03`) command results in an immediate transition back to Standby (`00.01`). The safety cool-down phase (`04.00`) is intelligently bypassed.
* **Command Sequence:**
  * **`0x23`**: Ventilation ON Request *(Initiates fan-only mode)*
  * **`0x0F`**: Status Request *(Monitors state change to `03.23`)*
  * **`0x03`**: Turn OFF Request *(Results in an instant return to Standby)*

| Relative Time | Direction | Raw Hex Message | Message (Decoded) | Description |
| :--- | :--- | :--- | :--- | :--- |
| **`T+0s`** | **C » H** | `AA 03 03 00 23 00 1E 02 DA 7A` | **`0x23`**: Vent ON Request | Controller requests ventilation mode: 30m timer (`00 1E`), Fan Level 2 (`02`). |
| **`T+0s`** | **H » C** | `AA 04 04 00 23 00 1E 02 00 C5 6C` | **`0x23`**: Vent ON Confirm | Heater accepts the ventilation parameters and starts the fan. |
| **`T+2s`** | **C » H** | `AA 03 00 00 02 9D BD` | **`0x02`**: Settings Request | Controller verifies the newly active settings profile. |
| **`T+2s`** | **H » C** | `AA 04 06 00 02 00 1E 04 0F 02 02 1B 75`| **`0x02`**: Settings Report | Heater confirms profile with 30m timer and Fan Level 2. |
| **`T+6s`** | **C » H** | `AA 03 00 00 0F 58 7C` | **`0x0F`**: Status Request | Controller checks live telemetry in the standard polling loop. |
| **`T+6s`** | **H » C** | `AA 04 0A 00 0F 03 23 00 16 7F 00 83...`| **`0x0F`**: Status Report | Heater confirms State **`03.23`** (Ventilation). Exchanger temp is ambient (`01 38` / 31°C). |
| **`...`** | | | | *(Ventilation runs normally. Mid-flight fan speed changes can occur here via `0x02`)* |
| **`T+56s`**| **C » H** | `AA 03 00 00 03 5D 7C` | **`0x03`**: Turn OFF Request | Controller issues the hard stop command. |
| **`T+56s`**| **H » C** | `AA 04 00 00 03 29 7D` | **`0x03`**: Turn OFF Confirm | Heater acknowledges and stops the fan immediately. |
| **`T+59s`**| **C » H** | `AA 03 00 00 0F 58 7C` | **`0x0F`**: Status Request | Controller checks live telemetry. |
| **`T+59s`**| **H » C** | `AA 04 0A 00 0F 00 01 00 15 7F 00 83...`| **`0x0F`**: Status Report | Heater instantly drops to State **`00.01`** (Standby), bypassing the cool-down phase because no heat was generated. |

### Extended System Information Request
* **Purpose:** To retrieve granular hardware details and lifetime statistics (Working Time, Serial Numbers, Firmware versions) to populate the "Info" menu.
* **Behavior:** The controller executes a burst of sequential memory reads, stepping through the heater's EEPROM 4 bytes at a time.
* **Command Sequence:** `0x0B` (Memory Read). Payload: `[Addr_High, Addr_Low, Length]`.

| Relative Time | Direction | Raw Hex Message | Message (Decoded) | Description |
| :--- | :--- | :--- | :--- | :--- |
| **`T+0s`** | **C » H** | `AA 03 03 00 0B 00 1B 04 28 F0` | **`0x0B`**: Read `0x1B` | Request 4 bytes starting at `0x1B`. |
| **`T+0s`** | **H » C** | `AA 04 06 00 0B 00 1B 00 1B 88 97 20 C6` | **`0x0B`**: Report `0x1B` | Heater returns data from `0x1B`. |
| **`T+0s`** | **C » H** | `AA 03 03 00 0B 00 1F 04 E8 F2` | **`0x0B`**: Read `0x1F` | Request 4 bytes starting at `0x1F`. |
| **`T+0s`** | **H » C** | `AA 04 06 00 0B 00 1F 00 1B C4 D0 12 43` | **`0x0B`**: Report `0x1F` | Heater returns data from `0x1F`. |
| **`T+0s`** | **C » H** | `AA 03 03 00 0B 00 23 04 E8 E3` | **`0x0B`**: Read `0x23` | Request 4 bytes starting at `0x23`. |
| **`T+0s`** | **H » C** | `AA 04 06 00 0B 00 23 00 0F 2E 40 1F 1C` | **`0x0B`**: Report `0x23` | Heater returns data from `0x23`. |
| **`T+0s`** | **C » H** | `AA 03 03 00 0B 00 27 04 28 E1` | **`0x0B`**: Read `0x27` | Request 4 bytes starting at `0x27`. |
| **`T+0s`** | **H » C** | `AA 04 06 00 0B 00 27 00 05 04 C7 DF 92` | **`0x0B`**: Report `0x27` | Heater returns data from `0x27`. |
| **`T+0s`** | **C » H** | `AA 03 03 00 0B 00 2B 04 28 E4` | **`0x0B`**: Read `0x2B` | Request 4 bytes starting at `0x2B`. |
| **`T+0s`** | **H » C** | `AA 04 06 00 0B 00 2B 00 02 19 97 73 3A` | **`0x0B`**: Report `0x2B` | Heater returns data from `0x2B`. |
| **`T+1s`** | **C » H** | `AA 03 03 00 0B 00 2F 04 E8 E6` | **`0x0B`**: Read `0x2F` | Request 4 bytes starting at `0x2F`. |
| **`T+1s`** | **H » C** | `AA 04 06 00 0B 00 2F 00 01 44 2B 92 02` | **`0x0B`**: Report `0x2F` | Heater returns data from `0x2F`. |
| **`T+1s`** | **C » H** | `AA 03 03 00 0B 00 33 04 28 EE` | **`0x0B`**: Read `0x33` | Request 4 bytes starting at `0x33`. |
| **`T+1s`** | **H » C** | `AA 04 06 00 0B 00 33 00 00 D6 F7 69 EE` | **`0x0B`**: Report `0x33` | Heater returns data from `0x33`. |
| **`T+1s`** | **C » H** | `AA 03 03 00 0B 00 37 04 E8 EC` | **`0x0B`**: Read `0x37` | Request 4 bytes starting at `0x37`. |
| **`T+1s`** | **H » C** | `AA 04 06 00 0B 00 37 00 00 4C 1A 44 B5` | **`0x0B`**: Report `0x37` | Heater returns data from `0x37`. |
| **`T+1s`** | **C » H** | `AA 03 03 00 0B 00 3B 04 E8 E9` | **`0x0B`**: Read `0x3B` | Request 4 bytes starting at `0x3B`. |
| **`T+1s`** | **H » C** | `AA 04 06 00 0B 00 3B 00 00 3C D9 D4 C0` | **`0x0B`**: Report `0x3B` | Heater returns data from `0x3B`. |
| **`T+1s`** | **C » H** | `AA 03 03 00 0B 00 3F 04 28 EB` | **`0x0B`**: Read `0x3F` | Request 4 bytes starting at `0x3F`. |
| **`T+2s`** | **H » C** | `AA 04 06 00 0B 00 3F 00 00 50 9D 27 1C` | **`0x0B`**: Report `0x3F` | Final 4 bytes returned from `0x3F`. |
