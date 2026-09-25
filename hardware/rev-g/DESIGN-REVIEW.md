# Rev G engineering review — 13 September 2026

The requested changes are implemented in a separate revision. [Independent audit](exports/independent-audit.json), [manufacturing audit](exports/manufacturing-audit.json), [ERC](exports/erc.json), [DRC](exports/drc-final.json) and [calculations](exports/protection-calculations.json) identify the exact native files checked. Rev F hashes remain unchanged. This review supports building a prototype, not declaring it proven for permanent vehicle installation.

The preceding G.2 layout added [Adi's routing and silkscreen corrections](ADI-G2-CHANGES.md), with 1.0 mm / 0.15 mm text and 0.15 mm printing clearance enforced. Circuit, BOM and component placement remain unchanged. G.3 now substitutes the external-antenna U2 and adds off-board ANT1; all electrical geometry is retained. See [G.3 verification](ANTENNA-G3-CHANGE.md). G.5 replaces G.4 mask tents with filled/capped thermal holes and renames the device Leafy. See [current manufacturing changes](FILLED-G5-CHANGE.md).

## Input damping and protection

C15 is Panasonic EEU-FR1J470H: FR series, 47 µF, 63 V, 6.3 mm diameter, 11.2 mm height, 2.5 mm straight-lead pitch. The H suffix selects taped packaging; the untaped EEU-FR1J470 was backordered in the live basket. R21 is Vishay CRCW25121R00FKEGHP, 1 Ω, 1.5 W, pulse-resistant 2512. It connects VPWR to C15 positive; C15 negative connects to GND. This RC branch damps the input ceramics while preserving the direct regulator supply path. The 100 V input ceramics and existing F1/D1/D3 remain.

The [TI regulator datasheet, §8.4–8.5](https://www.ti.com/lit/ds/symlink/lmr36510.pdf) motivates input damping and close bypass/feedback placement. A reproducible lumped-circuit estimate in `analyze_protection.py` sweeps assumed cable inductance 0.5–10 µH, source resistance 0.1–1 Ω, effective ceramic capacitance 0.5–2.42 µF, and bulk ESR 0.21–2 Ω. For an uncharged-capacitor 16 V hot plug, maximum predicted input peak falls from **31.45 V to 24.16 V**. Peak resistor power is 270.7 W, with at most 3.87 mJ dissipated in the modeled event. The [Vishay single-pulse curves](https://www.vishay.com/docs/20043/crcwhpe3.pdf) support choosing the larger pulse-resistant part; actual pulse shape and temperature still need checking.

This model assumes a conducting ideal input diode and no active regulator load or TVS conduction. It is a comparison, not a guaranteed vehicle envelope. It excludes fast edge parasitics, PCB inductance and component nonlinearities. It does **not** prove load-dump, reverse-transient, jump-start, ISO 7637/ISO 16750 or EMC compliance. D3 is still a 24 V stand-off SMBJ TVS; its specified clamp does not by itself prove the complete chain survives every vehicle pulse. No common-mode choke was added; the user's earlier decision to defer that remains respected.

## Battery protection and uninterrupted normal operation

U5 is specifically **TPS3760A012DYYR**, the adjustable 0.8 V undervoltage, active-low open-drain, non-latching variant. It must not be substituted with an overvoltage or latching variant. Its VDD is VPWR; RESET drives U1 EN. R22/R23 are 680 kΩ / 47 kΩ, 0.1%, 25 ppm/°C. R24 = 10 MΩ and R25 = 470 kΩ create additional hysteresis. C16 bypasses VDD, C17 filters SENSE, C18/C19 set sense/recovery delay. Pin functions and delay formulas were checked against the [TPS3760 datasheet](https://www.ti.com/lit/ds/symlink/tps3760.pdf).

Rev G.1 replaces the unavailable Q1 ordering code with this Catalog-grade part. It does not carry AEC-Q100 qualification or the Q1 datasheet's 70 V / 50 ms operating allowance. Its operating maximum is 65 V; 70 V is absolute maximum only. The user accepted these prototype trade-offs. See [the change and full geometry comparison](U5-G1-CHANGE.md).

Nominal protected-supply thresholds are 11.6686 V off and 12.6774 V restart. A conservative corner calculation including resistor temperature drift, reference error, input/output leakage and a conservative interpretation of hysteresis accuracy gives **11.41–11.92 V off** and **12.22–13.13 V restart**. These are circuit estimates, not individually calibrated thresholds. Actual battery voltage is higher by D1's current- and temperature-dependent forward drop. The supervisor senses after D1; the ADC cannot infer the changing diode drop exactly.

C18/C19 are 10 µF, within TI's recommended maximum. Nominal delays are 1.27 s / 12.7 s. Assuming 4–11 µF effective capacitance and TI timing limits gives roughly 0.41–1.86 s / 4.11–17.49 s. The capacitance envelope is an assumption pending bias/temperature measurement. Repeated disturbances can shorten delay if a timing capacitor has not fully discharged. Verify first-start, slow ramps, rapid dips and restart on the bench.

A board starting from the off state may need the Leaf in READY/charging, or a **13.5–14 V current-limited bench supply**, before it boots. Do not bypass U5 to make a weak battery keep the radio online. No intentional sleep schedule disconnects normal Wi-Fi operation, but low battery must be an exception. Battery chemistry remains unconfirmed: purchase at Biltema in January does not identify the model. This design assumes a conventional lead-acid accessory battery until its label is checked.

Shutdown leakage is not zero. The capacitor's full-rated-voltage leakage limit alone is about 29.6 µA. The supervisor, divider, pull-up, regulator and TVS add more; some relevant specifications are typical rather than guaranteed maxima. A sub-0.1 mA shutdown target and low-milliamp connected target are **measurement goals**, not established performance. Measure the complete board at the battery input, including temperature and router-loss conditions. Do not assume the Leaf will recharge its 12 V battery often enough to cover an unknown load.

## Powered-off ADC isolation

U6 is **TMUX1511PWR**. Channel 1 connects the original divider/filter node BAT_DIV to GPIO0/BAT_SENSE only when 3V3 is present. SEL1 is tied to 3V3; unused channels and their selects are grounded. C11 remains upstream of the switch; C20 bypasses U6. R26 = 100 kΩ pulls the ADC side down. The [TMUX1511 datasheet](https://www.ti.com/lit/ds/symlink/tmux1511.pdf) specifies powered-off protection and the leakage bounds used here.

At 65 V VPWR, the unpowered divider node is approximately 2.918 V, below the switch's 3.6 V protected signal limit. Using ±2 µA worst-case power-off leakage with R26 gives a 0.2 V ADC-side bound. When powered, R26 loads R8, changing the nominal ADC multiplier to 32.2766. Firmware uses ADC calibration and blocks Heat on if the reading is invalid. Meter-calibrate the divider gain; separately measure D1 drop.

## Placement, buttons and assembly

Measured pad-centre copper paths changed as follows:

| Route | Rev F | Rev G |
| --- | ---: | ---: |
| U1 VCC → C3 | 8.50 mm | 3.57 mm |
| U1 FB → R2 | 8.75 mm | 4.03 mm |
| U1 BOOT → C4 | 5.62 mm | 4.26 mm |

Local ground vias and close input bypass routing are retained. Native DRC has no added waivers. KiCad's configured ignored check classes remain visible in its report; “zero violations” does not mean every optional rule was enabled.

SW1/SW2 use PTS645SL43-2 LFS. The manufacturer's straight-through-hole drawing confirms 6.5 × 4.5 mm holes: pins 1/2 form one contact group, pins 3/4 the other. The PCB assigns those groups pad numbers 1 and 2 respectively. The [January 2026 manufacturer sheet](https://www.ckswitches.com/media/1471/pts645.pdf) lists −40 to +85 °C. Older distributor sheets/metadata list a narrower range; the downloaded older drawing is used only for geometry, not temperature qualification. The series is not automotive-certified and does not establish condensation resistance.

Factory scope is six parts: U1/U2/U4/U5/U6/L1. G.5 requires all 18 U1/U2 thermal holes epoxy-filled and copper-capped, with continuous top mask openings. JLC normal stencil engineering is accepted. Supplier fabrication/assembly review and physical solder-joint/bench checks remain; static audits cannot prove the completed manufacturing process. See `MANUFACTURING-NOTES.md`.

## Required prototype tests

1. Inspect all component orientations and joints; confirm no power-rail shorts. Hold ESP_EN low and power through J1 with current limiting. Sweep above the recovery threshold, then down through cutoff. Record VPWR and raw battery thresholds/delays at several temperatures and with rapid dips.
2. Scope U1 VIN/3V3 at startup, hot plug and Wi-Fi bursts; verify ESP32 rail remains 3.0–3.6 V, check ripple and load steps. Confirm C15 polarity and R21 pulse temperature. Laboratory transient testing is required before claiming automotive robustness.
3. Confirm ADC calibration, power-off isolation and shutdown current. Connect UART only while the board is powered; remove UART before removing board power.
4. Keep the board on the router for at least 24 hours; measure input current. Reboot/disconnect the router repeatedly, test weak signal, DHCP renewal and clients on the same LAN. Ensure no stale On request replays and no unintended CAN traffic occurs while idle.
5. Verify DB9/OBD continuity, actual TCU disconnection and likely 2013–2015 profile. Bench-test CAN with a correctly terminated second node first. Only then enable CAN writing and test Heat on/Off beside the car, including disconnected Wi-Fi and the local Off timer. Verify the car's own climate timeout: loss of board power cannot guarantee sending Off.
