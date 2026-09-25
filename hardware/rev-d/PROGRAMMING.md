# Complete hand assembly first

Rev D arrives with only U1, U2, U4 and L1 fitted. Complete the remaining 37 components and the inspection in HAND-ASSEMBLY.md before connecting power.

# Programming Rev D

Rev D uses the ESP32-C3's built-in **UART0 bootloader**. The programmer is a reusable external accessory; there is no USB socket on this PCB. The firmware has not yet been written, so the instructions below define the hardware setup and recovery procedure, not a claim that heater software is ready.

## Required accessories

1. A USB-to-UART adapter with **3.3 V TX/RX logic**, compatible with the Mac. For example, [Adafruit's prewired CP2102 cable](https://www.adafruit.com/product/954) lists 3.3 V data signals and costs $9.95 before shipping/tax when checked on 12 September 2026. Its red wire is **5 V power and must remain insulated and disconnected**. Its USB-A plug may need an adapter for the Mac. Its lack of automatic reset signals is expected: use the board's buttons.
2. A regulated, current-limited **12 V DC bench supply**, with at least 0.5 A available for later Wi-Fi testing. Begin first-power inspection with a lower current limit, then raise it after checking the board. This powers the board through its existing fuse and regulator.
3. A female DB9 breakout or a verified bench lead mating with J1, connecting only **pin 9 to +12 V and pin 3 to supply ground**. The manufacturer should solder J1 and J3. The breakout/bench supply are separate accessories, not items in the PCB BOM.

Use the connector's pin numbers and a continuity meter. Do not infer DB9 numbering from a mirrored rear view. The car cable is disconnected throughout bench programming.

## Connections

| Board connection | Connect to |
|---|---|
| J1 pin 9 | Bench supply +12 V |
| J1 pin 3 | Bench supply ground |
| J3 pin 1 — GND, square pad | Adapter GND |
| J3 pin 2 — RX | Adapter TX; green wire on Adafruit 954 |
| J3 pin 3 — TX | Adapter RX; white wire on Adafruit 954 |
| Adapter power wire | **No connection** |

J3 is an unshrouded 2.54 mm header; it is not mechanically keyed. The square pad identifies pin 1. With the `GND / RX / TX` labels upright, the contacts run left to right in that order. The three header pins carry no power supply. A ready-made keyed lead could be specified later, but it is not included in this BOM.

The UART is not isolated. Power the board from the bench supply before plugging the adapter into USB. Connect the ground before the signal wires. Disconnect the adapter from USB before removing board power, because powered UART signals can feed an unpowered controller through protection diodes. Keep loose jumper extensions short; the initial programming speed is **115200 baud**. Higher speeds are not qualified.

## Initial installation or recovery

1. Disconnect the vehicle. Verify polarity and connections with power off, then power the board from the current-limited 12 V supply. Confirm approximately 3.3 V at the regulator output.
2. Connect the UART adapter as above and connect it to the Mac. Select its serial port in the flashing tool.
3. Hold **BOOT**. Press and release **RESET**, then release **BOOT**. This holds GPIO9 low while reset is released; GPIO8 and GPIO2 remain pulled high.
4. Confirm the serial boot log reports download mode, then flash the ESP32-C3 image at 115200 baud using the offsets in that firmware build's generated flash arguments. Do not guess flash offsets or use an image for the earlier Waveshare design.
5. After a successful flash, release BOOT and press RESET again to start the application. Automatic reset through DTR/RTS is not wired on this board.
6. Verify Wi-Fi and the safe idle state on the bench before considering a vehicle connection.

Keep UART download enabled during development; do not burn security eFuses or disable ROM download as part of prototype flashing. Wi-Fi OTA can handle later application updates once we implement it, but UART is the recovery path for a blank board, wrong Wi-Fi settings or a broken application. See [Espressif's download guidance](https://docs.espressif.com/projects/esp-hardware-design-guidelines/en/latest/esp32c3/download-guidelines.html) and [OTA documentation](https://docs.espressif.com/projects/esp-idf/en/stable/esp32c3/api-reference/system/ota.html).
