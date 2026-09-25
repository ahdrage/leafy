# Rev G vehicle wiring and firmware interface

This guide applies to the **100 × 100 mm custom Rev G board**. The earlier development-board plan has different GPIO assignments. Buildable prototype firmware is supplied in [firmware/leaf-heat](../../firmware/leaf-heat/README.md), with CAN writing disabled by default. Complete hand assembly and bench tests before vehicle connection.

## Cable, identified by numbered contacts

Use the exact Nissan OVMS cable pinout below. Board J1 is a male DB9; the cable end is female. Check continuity with the cable unplugged at both ends. Do not identify pins by wire colour or a mirrored connector drawing.

| Vehicle OBD-II contact | Cable DB9 / board J1 contact | Rev G function |
| --- | --- | --- |
| 16 | 9 | CAR_12V, through F1 and D1 |
| 4 | 3 | GND |
| 13 | 7 | EV-CAN high |
| 12 | 2 | EV-CAN low |
| 6 | 5 | Alternate CAN high; **not connected on this PCB** |
| 14 | 4 | Alternate CAN low; **not connected on this PCB** |

J1 contacts 1, 6 and 8 are also unconnected. The two PCB connector shell anchors connect to GND. The specified cable mapping is published by [OpenEnergyMonitor](https://shop.openenergymonitor.com/nissan-ze0-e-nv200-obd2-ovms-cable/). A generic OBD/DB9 cable is not interchangeable merely because it fits.

## Confirm the vehicle profile

The intended profile is the **2013–2015 EV-CAN remote-climate implementation**. The owner remembers disconnecting the original TCU when installing OVMS. This supports the profile but must be checked physically before CAN writes are enabled. Registration in 2015 and the registration document's ZE0 label alone do not establish the TCU generation. Record the vehicle build/model year and fitted TCU before enabling transmissions.

OVMS instructs owners of the applicable 2013–2016 configuration to disconnect the original TCU's large white plug if fitted. Its 2016–2017 instructions instead isolate TCU CAN while retaining other connections for the hands-free microphone. Follow the instructions matching the actual vehicle. See [OVMS installation guidance](https://docs.openvehicles.com/en/latest/components/vehicle_nissanleaf/docs/index.html#remote-climate-control).

**Rev G cannot select the alternate bus in software.** It has one transceiver connected to J1 pins 2/7; pins 4/5 go nowhere. A car requiring the later profile needs a reviewed cable remapping or hardware revision as well as different firmware commands. This PCB also lacks the separate activation output used by the earliest cars.

## Firmware GPIO map

| Function | ESP32-C3 GPIO | Module U2 contact | Connected hardware |
| --- | --- | --- | --- |
| CAN transmit | 4 | 3 | U3 TXD, contact 1 |
| CAN receive | 5 | 4 | U3 RXD, contact 4 |
| CAN standby | 1 | 17 | U3 STB, contact 8; HIGH = standby |
| Protected-input measurement | 0 / ADC1_CH0 | 18 | R7/R8/C11 divider through U6, with R26 loading |
| Status LED | 7 | 6 | R9/D6; HIGH lights LED |
| UART receive | 20 | 11 | R19, U4, J3 pin 2; adapter TX |
| UART transmit | 21 | 12 | R18, U4, J3 pin 3; adapter RX |
| BOOT | 9 | 8 | SW2; held LOW during reset for download |

GPIO2 and GPIO8 have pull-ups. EN has a 10 kΩ / 1 µF reset network and SW1. These module pin functions and boot straps match [Espressif's module datasheet](https://www.espressif.com/sites/default/files/documentation/esp32-c3-wroom-02_datasheet_en.pdf). J3 carries **3.3 V logic and ground only**; use [firmware instructions](../../firmware/leaf-heat/README.md).

U3 is TCAN3404DRQ1. Its SHDN pin 5 is permanently grounded; the controller continues to use STB pin 8. C13 remains an extra 3V3 bypass, while C12 is the short local VCC bypass.

R10 holds CAN standby high during reset. Firmware must keep standby high until the CAN controller is initialized with a recessive TX state; then use LOW for normal CAN operation. Use 500 kbit/s classical CAN, 11-bit identifiers. The board adds no termination; a separate two-node bench network needs its own correct termination. Check STB, TX and the bus during reset, flashing and crashes. The transceiver mode/pinout is documented by [TI](https://www.ti.com/lit/gpn/TCAN3404-Q1).

The battery divider reads **VPWR after the fuse and diode**, not raw battery voltage. With U6 enabled, R26 loads R8: the nominal multiplier is 32.2766; at VPWR = 12 V the ADC node is about 0.372 V. Calibrate against a meter at J1 and allow for changing diode drop. Configure the ADC range explicitly and average settled readings. U5 now controls the regulator independently; see DESIGN-REVIEW.md for cutoff/recovery thresholds.

## Narrow protocol specification for the confirmed earlier profile

The implementation follows the source-verified sequence below. It has host tests and a successful build, but no powered CAN/vehicle test yet:

| Action | Standard CAN frame | Timing |
| --- | --- | --- |
| Wake before On or Off | 0x679, DLC 1, `00`; then 0x5C0, DLC 8, all zeros | Once per action |
| On | 0x56E, DLC 1, `4E` | 24 sends, 100 ms apart |
| On completion | 0x56E, DLC 1, `46` | One second after the 23rd On repeat, about 3.3 s after starting |
| Off | 0x56E, DLC 1, `56` | 24 sends, 100 ms apart, after wake |

Verified against `SendCommand`, `RemoteCommandTimer`, `CommandWakeupAZE0`, `RemoteCommandHandler` and timer initialization in [OVMS revision 85074a0](https://github.com/openvehicles/Open-Vehicle-Monitoring-System-3/blob/85074a0ae7a983b308c6e2e081185492527ee073/vehicle/OVMS.V3/components/vehicle_nissanleaf/src/vehicle_nissanleaf.cpp), with the repeat count in its [header](https://github.com/openvehicles/Open-Vehicle-Monitoring-System-3/blob/85074a0ae7a983b308c6e2e081185492527ee073/vehicle/OVMS.V3/components/vehicle_nissanleaf/src/vehicle_nissanleaf.h). The first timer-driven command is approximately 100 ms after wake; the count is 24 total in this implementation despite the header comment's wording.

The application serializes requests and is designed to cancel stale completion timers when Off is requested, stop bounded retries on errors, and never replay an old On command after a reset or Wi-Fi reconnection. Initially prove receive-only operation. Report request sent separately from confirmed climate operation. Validate actual heating and stopping on this car; these frames request the vehicle's climate function and do not directly switch or select the heater element.
