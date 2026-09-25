> **Historical development record.** The current release is [Leafy G.5](README.md). Use this file for context, not current ordering or wiring instructions.

# Homemade Wi-Fi heating control for the 2015 Leaf

## 1. The design

**Build a Wi-Fi box with one CAN interface and two buttons: Heat on and Heat off.** Use an ESP32 board with its CAN transceiver and power supply already assembled. Write the small Leaf-specific behavior as an ESPHome configuration. The car connects to the existing home Wi-Fi, which reaches its parking space. A browser on the same network opens the controls; Home Assistant and a continuously running computer are not required.

The target is the supplied UK-built Leaf, registered in Norway in October 2015, with ZE0 family designation and EM57 motor. The proposed firmware uses the **2013-2015 remote-climate sequence**. The registration's ZE0 label does not imply the 2011-2012 activation-wire arrangement. Registration year alone is not proof of model year: check the build date and original telematics unit before enabling commands. A late car with 2016 telematics would need the other CAN pair and corresponding command sequence; the proposed cable exposes both pairs, so that would not require buying a second CAN interface.[^1][^2]

For the 2013-2015 profile, OVMS sends wake-up and remote-climate commands through EV-CAN. Therefore **one CAN channel is sufficient for this narrow function**. The two-channel requirement in the earlier report concerned broader OVMS behavior. We are implementing just the climate command path.[^2]

Recommended electronics: **Waveshare ESP32-S3-RS485-CAN**, with the onboard Wi-Fi antenna. It combines the processor, CAN transceiver, 7-36V power input and enclosure. Its spare RS485 circuitry can remain unused. One assembled development board is simpler to build around than separate processor, CAN and power boards, even though it contains a few unused features.[^3][^4]

Daily use: open `http://leaf-heat.local/`, enter the device password, and press a button. Reserve its address in the router and save that address as a fallback if the phone does not resolve `.local`. Embed the web assets on the box so the page works even when the home's internet connection is down. Outside the home network it is unavailable; an existing home VPN could provide access later.[^7]

The buttons request the car's **remote climate mode**. They do not directly switch heater power or independently select a temperature. Verify that the car's remote-climate settings produce heating during commissioning. Use a fixed 15-minute session with an automatic Off request as the first firmware policy. This is a proposed local timeout, not a guarantee about the car's own timer.

## 2. Parts to buy

Buy one of each core item below. Prices were checked on 11 September 2026. Vendor amounts remain in their original currencies and exclude delivery and destination taxes unless stated. No orders have been placed.

| Qty | Component | Price and purchase note |
| --- | --- | --- |
| 1 | Waveshare ESP32-S3-RS485-CAN | Manufacturer lists $18.99-19.99 across antenna variants. Choose onboard antenna; allow $20. Enclosure and power conversion are included. Exact checkout stock needs confirmation.[^3][^4] |
| 1 | Nissan ZE0/e-NV200 OVMS OBD cable | £9.94 ex-VAT; listed in stock. This is only the passive cable, not an OVMS box.[^5] |
| 1 | Adafruit 3123 DB9 male terminal breakout | $2.95; listed in stock. Includes a small connector housing; connects the Leaf cable to loose wires.[^6] |
| 1 | Inline fuse holder and 1A fuse | Allow $3-6 equivalent locally. Fit in the positive supply lead and verify suitability against measured startup current and wire rating. |
| 1 set | Short stranded wires, heat-shrink, mounting ties/pads | Allow $3-7 equivalent. Keep CAN-H/CAN-L together as a twisted pair. |
| 0-1 | USB-C data cable | Reuse one; otherwise allow $3-6. Used with the car connection unplugged. |

**Core published cost: $21.94-22.94 + £9.94.** With the accessory allowances, budget **$30.94-41.94 + £9.94**, before shipping/tax. This is approximately a $45-60 class hardware build, rather than a quoted delivered total. Buying equivalent small connectors and wiring locally can avoid a disproportionate third shipping charge. Software costs $0; development and testing time are excluded.

## 3. Vehicle connections

Use the numbered terminals on the DB9 male breakout. This table applies to the **specific Nissan cable above**, not an arbitrary OBD-to-DB9 cable.[^5]

| Leaf OBD pin | Cable DB9 pin | Connect to Waveshare |
| --- | --- | --- |
| 16, permanent +12V | 9 | Power positive, through the inline fuse |
| 4, power ground | 3 | Power negative |
| 13, EV-CAN high | 7 | CAN H |
| 12, EV-CAN low | 2 | CAN L |

Leave DB9 4 and 5 unused for the proposed 2015 profile. They expose the other CAN pair. Confirm pin numbers by continuity with the entire cable unplugged; do not infer them from wire colors or a mirrored connector drawing. The standard generic cables examined do not expose the required EV-CAN pair.

Keep the board's **CAN 120-ohm termination disconnected**: the car is an existing terminated network. Use the power terminals for car power. **Disconnect the car cable before connecting USB**; Waveshare explicitly warns against simultaneous terminal and USB power.[^4]

For a 2013-2015 Leaf with the original telematics unit fitted, unplug its documented large connector so it cannot override climate requests. OVMS places it behind the glovebox on left-hand-drive cars. Follow the 2013-2016 installation instructions, not the ZE1 gateway instructions. Cars without the unit need no such step. Confirm the TCU generation before disconnection.[^1]

## 4. Firmware specification

**Use ESPHome as a small standalone device.** Its existing web server supplies the two button controls and password protection, and its ESP32 CAN component supports the chip's internal controller at 500 kbit/s. A laptop builds and flashes the configuration; it does not need to stay on afterwards.[^7][^8]

Configure the exact Waveshare board for ESP32-S3, with **CAN TX on GPIO15 and RX on GPIO16**, as shown by the manufacturer's schematic. Use standard 11-bit CAN identifiers and a 500 kbit/s bus. The first image should be listen-only; enable transmitting after the cable and received traffic are verified.[^8][^9]

The following sequence comes from the inspected OVMS 2013-2015 implementation. It is the firmware specification to reproduce and verify on this car, not a claim that custom firmware has already been built.[^2][^10]

| Action | Standard CAN frame | Timing |
| --- | --- | --- |
| Wake before On or Off | ID `0x679`, DLC 1, data `00`; then ID `0x5C0`, DLC 8, eight zero bytes | Send once each at the start of the action |
| Heat on request | ID `0x56E`, DLC 1, data `4E` | 24 sends, at 100 ms intervals |
| On-sequence completion | ID `0x56E`, DLC 1, data `46` | In upstream, a one-shot 1-second timer starts on the 23rd repeat; it fires at approximately 3.3 seconds from action start |
| Heat off request | ID `0x56E`, DLC 1, data `56` | After wake-up, 24 sends at 100 ms intervals |

The completion byte `46` is a separate upstream command from the explicit Off byte `56`. Keep this distinction and the timing. Do not continuously send a keep-awake message while waiting for a button press. No relay or switching of heater supply is involved.

The implementation should have two exposed buttons, **Heat on** and **Heat off**, rather than an optimistic switch that implies it knows the physical state. Display a short request result and timestamp. Successful CAN transmission is not proof of warm air; add actual state feedback only if it proves dependable during vehicle tests.

On starts the short command sequence and the local 15-minute deadline. Off cancels every pending On repeat, completion callback and timeout before sending its own sequence. Repeated taps must not queue several heating sessions. Network recovery and boot must never replay an On request. A dropped Wi-Fi connection must not cancel a running local Off deadline. If a transmit error occurs, report it and stop the sequence rather than retrying forever.

Configure the built-in web server with local assets and authentication. Keep it on the home LAN without router port forwarding. Use USB updates for version one; a tiny bespoke phone app, broker and server would add unnecessary work. ESPHome's web-server documentation describes the authentication and local-asset settings.[^7]

This approach avoids the previous T-Call build's missing Leaf hardware dependencies because it copies only the required behavior into a different, much smaller firmware configuration. It is not a trimmed OVMS binary or a promise that full OVMS runs on this board.

## 5. Build and verification

**Step 1: assemble and flash on the desk.** Fit the board and connector housings, wire the four connections, and label them. Verify the unpowered cable with a meter. Flash the listen-only image over USB. Confirm both buttons load locally and require a password. The orderable board is a development platform; its factory demo is not Leaf heater firmware.

**Step 2: establish the vehicle profile.** Confirm the build/TCU generation, apply the documented TCU disconnection if needed, and connect the box with the car stationary. Check received EV-CAN traffic at 500 kbit/s. A 2016-type TCU would change the selected pair and protocol before any transmit test. Restore the original wiring if the car reports unexpected behavior.

**Step 3: prove On and Off.** After a full vehicle sleep, test heating while plugged in and while unplugged, subject to the car's normal battery and climate constraints. Confirm warm air physically. Test Off after startup, during the initial request sequence, and near the 15-minute deadline. Confirm the car resumes sleeping after the session. Repeat at least ten parked start/stop cycles.

**Step 4: test loss of connectivity.** Turn off the router during heating and confirm the device's local Off deadline still runs. Restore Wi-Fi and confirm it does not replay a command. Reboot the box and verify that it never requests heat merely because it started. Separately establish what the car does if power to the box is removed during a heating session; the box cannot enforce its own timeout while unpowered.

**Step 5: measure parked power and cold operation.** This is the unresolved engineering check for the otherwise simple hardware. The board has an isolated CAN supply and indicator circuitry that consume power even when the processor sleeps. A processor deep-sleep figure is not the whole box's consumption. At a measured 25 mA from 12V, for example, the box would consume 0.60 Ah/day or 4.2 Ah/week. That is an illustrative calculation, not measured performance.

Begin with supervised use and measure the actual current after the car sleeps. Disconnect for extended parking until an acceptable energy budget is established. If standby draw is excessive, improve the supply/sleep arrangement before treating the box as permanently installed. Low-voltage software shutdown alone may leave the CAN supply consuming power. Cold-start and reconnect tests at the intended Norwegian winter temperatures are required; a whole-board winter operating rating was not established from the supplier information.

The schematic includes a buck supply, reverse-polarity diode and TVS components. Those are useful protections, but the published 7-36V input range does not establish automotive load-dump immunity. Check the completed input circuit and measured vehicle conditions before unattended installation. This is a prototype validation item, not a request to design a custom automotive PCB before the first supervised trial.[^9]

Allow one wiring/installation session plus firmware development and repeated trials, then at least 72 hours of initial parked observation. There is no need to wait for the ZE1 harness discussed in the earlier report. **The selected first build is this single-board Wi-Fi design.** Its two functional uncertainties are exact TCU generation and unattended power behavior; neither justifies adding cellular hardware.

## Sources

Prices and live documentation checked on 11 September 2026. Code links refer to the same pinned OVMS revision as the original research. The vehicle description and home Wi-Fi coverage were supplied by the owner. The new hardware and firmware remain untested on the car.

[^1]: Open Vehicles. [Nissan Leaf integration and 2013-2016 TCU instructions](https://docs.openvehicles.com/en/latest/components/vehicle_nissanleaf/docs/index.html#remote-climate-control).
[^2]: Open Vehicles. [Leaf command implementation](https://github.com/openvehicles/Open-Vehicle-Monitoring-System-3/blob/85074a0ae7a983b308c6e2e081185492527ee073/vehicle/OVMS.V3/components/vehicle_nissanleaf/src/vehicle_nissanleaf.cpp). `SendCommand`, `RemoteCommandTimer`, `CommandWakeupAZE0` and `CommandClimateControl`; revision dated 4 September 2026.
[^3]: Waveshare. [ESP32-S3-RS485-CAN product listing](https://www.waveshare.com/product/iot-communication/short-range-wireless/esp32-s3-rs485-can.htm). Manufacturer's indexed listing: $18.99-19.99; antenna selection. Direct checkout availability was not verified.
[^4]: Waveshare. [ESP32-S3-RS485-CAN documentation](https://www.waveshare.com/wiki/ESP32-S3-RS485-CAN). 7-36V input, case, CAN protection, termination jumper and warning against simultaneous USB/terminal power.
[^5]: OpenEnergyMonitor. [Nissan ZE0/e-NV200 cable](https://shop.openenergymonitor.com/nissan-ze0-e-nv200-obd2-ovms-cable/). £9.94 ex-VAT; exact OBD-to-DB9 mapping.
[^6]: Adafruit. [DB9 male terminal breakout, product 3123](https://www.adafruit.com/product/3123). $2.95, including housing.
[^7]: ESPHome. [Web server component](https://esphome.io/components/web_server/). Local access, embedded assets, authentication and update configuration.
[^8]: ESPHome. [ESP32 CAN component](https://esphome.io/components/canbus/esp32_can/). TWAI controller, 500 kbit/s and listen-only operation.
[^9]: Waveshare. [ESP32-S3-RS485-CAN schematic](https://files.waveshare.com/wiki/ESP32-S3-RS485-CAN/ESP32-S3-RS485-CAN-Schematic.pdf). GPIO15/16, TJA1051 transceiver, isolated supply, XL1509 and input protection.
[^10]: Open Vehicles. [Leaf constants](https://github.com/openvehicles/Open-Vehicle-Monitoring-System-3/blob/85074a0ae7a983b308c6e2e081185492527ee073/vehicle/OVMS.V3/components/vehicle_nissanleaf/src/vehicle_nissanleaf.h). Repeat count 24; timer intervals are defined in the implementation in source 2.
