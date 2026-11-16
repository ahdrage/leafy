# Website and vehicle progress — 16 November 2026

**The latest firmware is installed and displaying both battery percentages received from the car.** The owner confirmed that the display looks good. Earlier today the owner also reported successful Heat On without the charging cable, on the preceding firmware. Unplugged Heat Off and a heater regression on the latest image have not yet been recorded.

API/iOS development was paused during this website session. It later resumed with a [native app and simulator testing](../ios/verification/2026-11-16.md). The normal website works directly on Leafy and needs no external server. No PCB, BOM, voltage threshold, calibration or climate-command sequence changed today. Nothing was pushed to GitHub.

## What changed

- Dashboard battery percentage first, BMS percentage second, each with its own sample age.
- Readings older than 120 seconds show **Last known** and **stale**. After reboot, missing readings show **waiting for a CAN reading**, not 0%.
- An **Automatic Off request** countdown derived from the existing 15-minute deadline. This does not create or change the timer. An expired timer with uncertain outcome tells the user to verify the heater in the car; no active deadline shows **no timer**.
- Status refresh every five seconds, with a three-second timeout and no overlapping requests. A failed request replaces old readings with **Device unreachable**. Retrying status never retries a heater command.

The existing Save key, Forget and On/Off controls remain. The tested unit retains protected-supply On threshold 11.9 V and ADC correction 0.9820. The public settings template still defaults to CAN writes disabled, threshold 12.2 V and correction 1.0. Actual heater state remains unverified in software; HTTP acceptance and a timer are not physical heater feedback.

## What we learned during testing

1. **Unplugged Heat On works on this vehicle.** This is owner-reported and does not establish every battery/temperature condition. The earlier failed request at approximately 10% traction-battery charge may have involved a vehicle restriction, but neither that root cause nor a precise Nissan threshold has been proven.
2. **BMS and dashboard percentages are different signals.** The first update showed 94.2% BMS while the owner reported 97% on the instrument panel. We added both values rather than applying an arbitrary correction to the BMS reading. Neither reading is battery health/SOH or a percentage inferred from 12 V voltage.
3. **A working website does not imply fresh CAN data.** Initial readings waited for frames after reset. Both arrived after the owner reconfirmed the green READY indicator. This does not mean READY is the only possible source of live data; it was the verified condition in this test. A sleeping bus may supply no fresh frames.
4. **Battery sampling changes the current-consumption test conditions.** Earlier coarse 4–9 mA bench readings preceded this firmware. Repeat parked-current measurements with telemetry enabled rather than treating that observation as a qualified figure for the new image.

## Signals and sampling

Both signals use the existing EV-CAN connection: J1 DB9 pin 7 CAN H and pin 2 CAN L. No cable or bus change was needed.

| Reading | Decoder for this vehicle profile |
| --- | --- |
| Dashboard SOC | Standard, non-RTR, eight-byte `0x1DB`; `data[4] & 0x7f`. Values 101–127 are rejected, including unavailable sentinel 127. |
| BMS SOC | Standard, non-RTR, eight-byte `0x55B`; `((data[0] << 2) | (data[1] >> 6)) / 10.0`. Raw values above 1000 are rejected, including sentinel 1023. |

The dashboard decoder follows the first-generation/2013–2015 profile, **not ZE1**. Both are derived from the [pinned OVMS implementation](https://github.com/openvehicles/Open-Vehicle-Monitoring-System-3/blob/85074a0ae7a983b308c6e2e081185492527ee073/vehicle/OVMS.V3/components/vehicle_nissanleaf/src/vehicle_nissanleaf.cpp); see [credits](../CREDITS.md).

Each value has an independent reception timestamp. An invalid frame preserves the previous valid value and its age; receiving one signal does not refresh the other. Zero and 100% are valid values.

Idle sampling uses listen-only windows of 1.5 seconds every 60 seconds. These send no wake, ACK or error frames. Between windows the transceiver returns to standby and the CAN driver is released for automatic light sleep. Commands preempt the listener; frames received during normal command activity also update telemetry. Leafy does not wake the car merely to refresh a battery value.

The authenticated JSON endpoint `/api/v1/status` retains its BMS field semantics. Dashboard SOC has not been added to the external API bridge; the native app uses the existing BMS-only API. The normal website uses `/api/status` and shows both.

## Installation and live observations

Both website images were built, uploaded with written-data hash verification and manually reset by the owner. The owner confirmed the parked/READY preparation and heater off before the first update. No heater command was sent by the assistant during these updates.

| Checkpoint | Observed result |
| --- | --- |
| First BMS-only website update | Initially waiting for data; after READY confirmation: BMS 94.2%, age 0 seconds, protected supply 13.64 V, reader/command errors 0. |
| Owner instrument reading during that phase | Dashboard 97%; distinct from the BMS signal. |
| Latest dual-value image, initial boot | Both readings waiting; protected supply 12.21 V, reader/command errors 0. |
| Latest image after READY reconfirmation | Dashboard 95%, BMS 92.5%, each age 26 seconds; protected supply 13.70 V, reader/command errors 0; sequence idle, no local heat request/timer. |
| Owner follow-up | “Awesome. Looks good.” Display accepted; an exact simultaneous 95%-versus-instrument comparison was not separately logged. |

The earlier 97% instrument reading preceded the later 95% CAN sample; it is not a simultaneous discrepancy measurement.

## Verification and evidence

- All **48 host checks** passed: 11 core, seven production control-task, ten transport, six diagnostic listener, three authentication, four telemetry/status suites and seven browser-script checks. The four suites each contain multiple assertions but count as one check per suite.
- Coverage includes both decoders, independent ages, invalid frames, unrelated high-bit masking, missing/stale values, 0% and 100%, countdown behavior and status timeout.
- Real-browser Save/On/Off/reload/Forget and display/timeout regressions passed with all requests intercepted. They did not operate the car.
- Latest configured ESP32-C3 build: RAM **29,540 bytes**, flash usage **900,098 bytes** (85.8% of the configured application partition).
- Latest flashed application SHA-256: `c2a314277eaef95fef4d797e4f506920ca4951934244f0d9a81d39370cf33379`.

Records: [latest dual-value installation](../firmware/leaf-heat/verification/dashboard-battery-2026-11-16.json), [preceding BMS website installation](../firmware/leaf-heat/verification/website-battery-2026-11-16.json), and [initial API phase](API-2026-11-16.md). The API phase's 45 firmware/23 server checks and unflashed build are historical; they are not the latest installation status. Earlier source archives remain historical. Configured firmware binaries and private settings contain credentials and must stay private.

## Next physical checks

1. Record a simultaneous instrument-panel/dashboard-CAN comparison and observe both ages refreshing while the bus is awake. Compare BMS SOC with a trusted BMS source if available.
2. Perform a supervised On/Off cycle on the latest firmware, including unplugged Off, recording battery level, ignition/charging state, supply, response and warnings. Confirm the countdown and actual car behavior.
3. Let the bus sleep and observe last-known/stale labels while the website remains reachable with adequate supply. Verify recovery when the bus becomes active again.
4. Observe actual shutdown at the local 15-minute deadline, including loss of Wi-Fi. Distinguish Leafy's Off request from the car's own timeout.
5. Recheck parked current, shutdown/recovery and reconnect behavior with telemetry enabled. Complete the broader [validation checklist](VALIDATION.md) before relying on unattended operation.
