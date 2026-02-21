# Autoterm Controller Initialization Protocols

This document describes the initialization sequences and UART connection strategies for individual Autoterm heater controllers.

Upon being powered on or connected, the controller initiates a handshake process to establish communication with the heater. Because different heater models and firmware versions may operate at different communication speeds, the controller attempts to send initialization messages across various baud rates. Once the heater successfully receives a message and replies, the controller identifies the correct baud rate, halts the initialization sweep, and establishes a stable communication link.

The raw serial communication logs used to document these sequences are available in the `message_captures/controller_initialization/` directory of this repository.

## 1. Comfort Control

The Comfort Control unit utilizes a "hunt-and-peck" strategy, infinitely cycling between two specific baud rates until a response is received from the heater. It does not employ a burst strategy; instead, it sends a single packet, waits, switches baud rate, and repeats.

### Supported Baud Rates
* **2400 bps**
* **9600 bps**

### Initialization Cycle
* **Strategy:** Infinite Loop, the controller continuously toggles between the two supported baud rates. It displays "No connection!" on the screen while continuing to loop indefinitely.
* **Cycle Length:** Approximately 6.5 seconds per complete cycle.
* **Target Message ID:** It strictly uses message ID `0x06` across all attempts.

### Sequence Steps
The controller continuously alternates between the following three states:
* **State 1 (9600 Baud):** Transmits message `aa 03 00 00 06 5e bc`, followed by a 2.5-second delay.
* **State 2 (2400 Baud):** Transmits message `aa 03 00 00 06 5e bc`, followed by a 1.5-second delay.
* **State 3 (2400 Baud):** Transmits message `07 07`, followed by a 2.5-second delay.
    * *Note:* While the exact purpose of the `07 07` message remains unknown, further investigation confirms it is a 2400 baud transmission.

---

## 2. OLED Control panel (PU-27)

The OLED Control panel employs a deterministic, multi-stage initialization sweep. It broadcasts a burst of 15 identical messages at a specific baud rate and Message ID before moving to the next configuration.

### Supported Baud Rates
* **1200 bps**
* **2400 bps**
* **9600 bps** 

### Initialization Cycle
* **Strategy:** Finite Sequential Sweep. The controller executes a 4-stage sequence once. If no connection is established after the final stage, the transmission sequence terminates.
* **Cycle Length:** The complete initialization sweep takes approximately 60 seconds.
* **Target Message IDs:** The message ID changes depending on the current stage, utilizing `0x1C`, `0x1E`, and `0x04`.

### Sequence Steps
The controller executes the following five stages sequentially:
* **Stage 0 (2400 Baud):** Transmits 6 messages of `1b 1b`. 
  * *Note:* The exact meaning of these messages is currently unknown.
* **Stage 1 (2400 Baud):** Transmits 15 messages `aa 03 00 00 1c 95 3d` (Message ID: `0x1C`).
* **Stage 2 (1200 Baud):** Transmits 15 messages `aa 03 00 00 1e 54 bc` (Message ID: `0x1E`).
* **Stage 3 (2400 Baud):** Transmits 15 messages `aa 03 00 00 04 9f 3d` (Message ID: `0x04`).
* **Stage 4 (9600 Baud):** Transmits 15 messages `aa 03 00 00 04 9f 3d` (Message ID: `0x04`).