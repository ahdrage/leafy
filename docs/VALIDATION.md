# Validation status — 16 November 2026

**Power observation:** the highest owner-reported bench-display reading was 9 mA, within a reported 4–9 mA range before battery telemetry was installed. At 12–14 V, 9 mA corresponds to approximately 0.108–0.126 W. The voltage paired with that observation was not recorded, so this is a calculation, not a measured maximum wattage. Short peaks, average parked consumption and consumption with the latest telemetry firmware still need measurement.

**The prototype has demonstrated plugged-in On/Off, owner-reported unplugged On, and live dashboard/BMS battery display.** The latest dual-value firmware is flashed and the owner accepted the display. This is not complete validation for unattended vehicle use. See the [15 November commissioning record](COMMISSIONING-2026-11-15.md) and [16 November follow-up](WEBSITE-BATTERY-2026-11-16.md) for conditions and evidence provenance.

| Area | Evidence / status |
| --- | --- |
| CAD | Previously saved G.5 ERC/DRC: zero reported violations, unconnected items or schematic mismatches under configured rules, with refill/parity checks. No CAD change or fresh CAD run in this documentation update. |
| Native audits | Existing checks cover 55 components, pin/net mapping, factory scope and fabrication comparisons. |
| Manufacturing | G.5 CAM and six-part placement reviewed in September; boards received. Photos cannot establish internal thermal-pad solder quality or fill quality. |
| Assembly | Owner completed one test unit: six factory parts plus 48 hand parts, D6 LED omitted. R3 and J1 solder rework recorded. Full BOM still contains 55 parts. |
| Power | Owner measured approximately 3.3–3.33 V at TP4; cutoff at TP3 approximately 11.66 V and restart approximately 12.25 V, with repeated cycling reported. No scope/transient or measured-delay qualification. |
| ADC | One-point correction 0.9820 applied; calibrated display close to meter. Reads protected supply after D1, not traction-battery SOC. |
| Current | Owner observed approximately 4–9 mA before battery telemetry was installed. Remeasure with the new listen windows; peaks, average, shutdown and router-loss current remain unqualified. |
| Firmware | Latest dual-value image built, flashed with verified hashes, reset and served live status. All 48 host checks and isolated real-browser regression passed. Earlier 41/45-check records are historical. |
| Web UI | Key validation/session saving, Forget, buttons, both SOC values/ages and Off-request countdown tested. Three-second status timeout and overlap guard tested. HTTP 202 proves queue acceptance only. |
| CAN receive | 64,223 frames received in diagnostic mode; zero drops. Nine early controller bus errors remained unchanged over subsequent approximately 80 seconds; cause unresolved. |
| CAN transmit / climate | Owner-confirmed plugged-in On/Off and subsequent unplugged On on preceding firmware. Unplugged Off and On/Off regression on latest telemetry image remain unrecorded; no second-node bench fault tests. |
| Battery telemetry | Latest image received dashboard 95% / BMS 92.5%, each age 26 seconds, protected supply 13.70 V, reader/command errors 0. Owner accepted display; exact simultaneous instrument comparison not separately logged. Sleeping-bus/stale recovery still needs physical testing. |
| API / iOS | Native app and test targets build. Seven host model tests and 23 server tests pass. Interactive iOS 26.1 simulator tests used a fake board through the real API; XCUITest execution was blocked by Xcode’s service-attachment error. No physical iPhone/vehicle acceptance through the bridge. [Evidence](../ios/verification/2026-11-16.md). |
| Low traction battery | Earlier accepted On did not heat at reported approximately 10% SOC; success followed connecting charging. Low SOC is plausible, not a proven root cause or precise cutoff. |
| Enclosure | Existing mesh/geometry and G.5 compatibility checks; no printed fit/environmental validation recorded. |

The tested unit's software heat threshold is **11.9 V at TP3/VPWR**, as requested by the owner. The public template retains **12.2 V**, CAN writes disabled and uncalibrated correction 1.0. Hardware cutoff remains independent and unchanged. A functional result on this car is not approval for arbitrary Leaf model years or cables.

## Remaining checks

1. On the latest installed image, perform a supervised On/Off cycle with charging disconnected and the car OFF. Unplugged On already succeeded on the preceding image; explicitly record unplugged Off and regression after the telemetry change. Use adequate traction-battery charge, recording SOC, ignition state, voltage, response and warnings; no precise Nissan SOC threshold has been established.
2. Observe actual shutdown at the local 15-minute timer, including Wi-Fi loss. Correlate logs to distinguish Leafy's Off request from the car's own timeout.
3. Test repeated sessions, reboot/reconnection without stale commands, and consequences of board power loss; establish the vehicle's own timeout.
4. Complete hardware CAN fault/standby tests with a second correctly terminated node: arbitration, missing ACK, bus-off and pending-frame cancellation. These were deferred because a second device was unavailable; listening in the car was not an equivalent test.
5. Scope regulation/startup/ripple/load steps and input hot-plug behaviour; assess transient protection with suitable equipment.
6. Measure cutoff/recovery delays and temperature/rapid-dip behaviour, powered-off ADC isolation, shutdown current and average/peak input current with the new passive sampling schedule.
7. At least 24-hour network/power soak with router restart, DHCP renewal and weak signal; record current under connected/disconnected conditions and verify no unintended replay.
8. Check printed case, cable fit, antenna strain relief, mounting and environmental suitability.
9. Compare dashboard CAN SOC with the instrument panel simultaneously; observe independent sample ages, sleeping-bus stale labels and recovery. BMS and dashboard percentages need not match.

See [design review](../hardware/rev-g/DESIGN-REVIEW.md), [historical firmware fixes](../firmware/leaf-heat/verification/REVIEW-FIXES.md) and the [latest website/vehicle evidence](WEBSITE-BATTERY-2026-11-16.md). Earlier JSON/build reports retain the status at their own stage; a past “untested” statement is not a denial of the later functional result.

Record test date, hardware revision, firmware image hash/non-secret settings, instruments, wiring, supply/temperature, expected/measured results and pass/fail. The UI still reports actual heater state as unverified because it does not decode confirming vehicle telemetry. No ISO 7637/16750, EMC, completed-device radio, ingress or automotive qualification is claimed.
