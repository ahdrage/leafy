# Commissioning progress — 15 November 2026

**Historical checkpoint:** this record ends on 15 November. See the [16 November follow-up](WEBSITE-BATTERY-2026-11-16.md) for unplugged Heat On and the installed dual-battery display, and [current validation](VALIDATION.md) for outstanding tests.

**Milestone: the owner confirmed that Leafy started and stopped the car's climate system with the charging cable connected.** This is a supervised functional result on one Rev G.5 board and one 2015 Leaf, not complete vehicle qualification.

This record consolidates the progress reported in the commissioning conversation through 15 November (Europe/Oslo). Earlier assembly and bench observations are carried forward below; their individual dates were not recorded. Today's firmware/CAN evidence has dated verification files. Physical measurements and heater response are owner-reported; software tests, upload checks and HTTP/serial observations are recorded separately.

## Assembly and bench results carried into this session

- G.5 PCBs and factory assemblies arrived. The design has 55 soldered components: six factory fitted, 49 hand positions. The test unit has 48 hand-fitted parts, with D6 status LED omitted; the external antenna is a separate plug-in part. This is an assembly exception, not a BOM change.
- Soldering was practised on a spare bare PCB before the real board. The owner measured fitted practice 10 kΩ resistors at approximately 10 kΩ.
- A poor R3 joint was repaired after ESP_EN measured about 1 V despite a valid 3.3 V rail. The owner then observed processor current draw. UART wiring was also corrected before successful serial communication.
- J1/DB9 joints were reworked; the owner reported solid continuity results. Continuity does not establish CAN signal integrity or every possible short circuit.
- Bench power used a Joy-IT JT-RD6006. Positive went to TP2 / CAR_12V, negative to TP1 / GND. The user's blue lead was positive, black negative; identify nets rather than relying on colours. Initial current limit was 0.1 A. Do not connect the bench supply and vehicle power together.
- Raw/protected input and regulated 3.3 V were measured. TP4 was approximately 3.3–3.33 V. A multimeter cannot establish ripple or fast startup/load transients.
- Initial low-voltage tests gave inconsistent results (board still on at low input and an anomalous C17 reading). Following rework and repeat testing, TP4 fell to 0 V at approximately **TP3 = 11.66 V**, then recovered at approximately **TP3 = 12.25 V** (bench display approximately 12.5 V). The owner confirmed repeat shutdown/restart operation. The exact cause of the initial anomaly was not conclusively isolated; delays, temperature dependence and fast dips were not measured.
- The supply display showed roughly **4–9 mA** during connected Wi-Fi operation. This is a coarse observation, not a measured peak, time-averaged parked-current specification or shutdown-current result.
- External antenna connected; local web access, reboot and reconnection worked. No 24-hour soak, router-loss current or RF-range test is recorded.

## Firmware, programming and web fixes

The FTDI **TTL-232R-3V3** uses black GND → J3 pin 1, orange adapter TX → J3 pin 2/RX, yellow adapter RX → J3 pin 3/TX. Its red power lead is not connected; 3.3 V describes the UART logic, not permission to power the board from that lead. The board has separate input power. Serial communication is 115200 baud. Download mode requires holding BOOT, pressing/releasing RESET, then releasing BOOT; RESET alone starts the application after upload.

Recorded non-secret settings for the tested unit:

| Setting | Tested value | Meaning |
| --- | --- | --- |
| `LEAF_ADC_CORRECTION` | `0.9820f` | Adjusted from a web reading of 13.91 V versus meter 13.66 V at TP3; subsequent displayed readings were close. One-point calibration only. |
| `LEAF_MIN_HEAT_VPWR` | `11.9f` | Owner-selected software threshold, reduced from 12.2 V; applies at VPWR after D1, not directly to battery terminals or traction-battery charge. |
| `LEAF_CAN_WRITE_ENABLED` | `true` | Enabled only for the supervised vehicle test after the receive-only stage. |
| `LEAF_CAN_LISTEN_ONLY` | `false` | Receive-only diagnostic disabled in the final heater-test image. |

Hardware cutoff was not changed. The public example retains CAN writes disabled, ADC correction 1.0 and the 12.2 V software threshold; the tested values are private unit-specific configuration, not silently changed defaults. Wi-Fi credentials and the control key are excluded from this record.

- Build/upload completed with flash-data hash verification and manual RESET afterward; boot, Wi-Fi and HTTP were observed.
- Added **Save key for this tab** and **Forget key**. Read-only `GET /api/auth` validates the key before session storage; saving/reloading does not send a heater command. Correct/incorrect-key responses and session restoration were checked.
- Diagnosed the Heat buttons doing nothing: inline `command()` resolved to the browser's native `HTMLButtonElement.command` string property. Reproduced `command is not a function` in Chrome; replaced inline handlers with `addEventListener` callbacks.
- The updated page shows explicit accepted/rejected HTTP outcomes. The owner subsequently received **HTTP 202 / Request submitted**. This means Leafy accepted a queued command, not that the vehicle acknowledged climate operation.
- **41 host checks passed**, plus an isolated real-Chrome click/Save/Forget/reload regression with all HTTP traffic mocked. Those browser tests did not send vehicle commands.
- Latest flashed application SHA-256 at the end of 15 November, from the button-fix record: `fa9d045d211e34ad6b5c82ef6157e08d3612bbf5a5ba9acdfb38b33a6ae8f523`. This identifies the tested image; do not publish the configured binary. Historical source ZIPs/build reports are not a release of today's firmware.

## Vehicle tests on 15 November

1. Owner explicitly confirmed original TCU disconnected and no new dashboard warnings during the listening test.
2. Receive-only firmware at 500 kbit/s initially saw no traffic with the car off. After the owner confirmed green READY, reception reached **64,223 frames**, zero reported drops. Nine controller bus errors occurred near traffic onset and did not increase during the subsequent approximately 80-second active observation. Their cause remains unconfirmed.
3. No second CAN device was available, so the planned two-node bench CAN fault tests were **not performed**. Supervised in-car listening preceded enabling writes; it does not substitute for arbitration, missing-ACK, bus-off or cancellation testing on hardware.
4. CAN-enabled firmware was flashed and verified; the owner operated the web buttons. The assistant's recorded live HTTP checks were read-only and did not initiate heating.
5. After the button fix, one accepted On request did not produce observed heating. The owner reported the traction battery at approximately **10%**. Subsequent idle/error-zero status alone cannot determine whether a command completed, the board reset, or protection/another event intervened.
6. The owner connected the charging cable and reported **Heat On worked**. The owner then explicitly confirmed **Heat Off worked in the same test**. Exact ignition state, charge percentage at success, charging power, response latency and temperature were not recorded. Do not backfill them from earlier instructions.

**Conclusion:** manual On and Off now have an owner-observed functional pass with the charging cable connected. Operation without the charging cable is still unverified. Low traction-battery charge is a plausible explanation for the earlier failure, but charging changed the test conditions and the cause has not been isolated. Leafy's 11.9 V gate concerns the separate 12 V supply; it does not measure traction-battery percentage.

Nissan lists low vehicle battery charge as a possible reason for remote climate failure in its [support FAQ](https://www.nissan.ca/services/apps/nissan-connect/support-faqs.html). The [2015 owner's manual, page 4-27](https://www.nissanusa.com/content/dam/Nissan/us/manuals-and-guides/leaf/2015/2015-Nissan-LEAF-owner-manual.pdf) says remote climate starts with the vehicle switched OFF and describes operation during normal charging. These sources describe Nissan's system; they do not establish the cause of this Leafy attempt or a precise percentage cutoff for this car.

## Next tests

- [ ] Charge above approximately 30%, disconnect charging, leave the car fully OFF, and repeat one supervised On/Off cycle while capturing status/serial output. **30% is a practical test target, not a documented Nissan threshold.** Record actual SOC, ignition state, TP3 voltage, response and warnings.
- [ ] Verify the local 15-minute Off request against actual climate operation, then repeat with Wi-Fi unavailable. Do not assume the car's own timeout proves Leafy's timer worked; correlate logs.
- [ ] Verify repeated sessions, reset/reconnect without stale On replay and the car's own shutdown behaviour if Leafy loses power/communication.
- [ ] Complete hardware CAN fault/standby tests when suitable equipment is available; investigate the initial nine receive errors if they recur.
- [ ] Measure startup/load ripple, input hot-plug/transient behaviour, cutoff/recovery delays, powered-off isolation and shutdown current with suitable instruments.
- [ ] Run at least a 24-hour network/power soak, including router restart, DHCP renewal, weak signal and current measurement under each condition.
- [ ] Finish physical enclosure fit, mounting, cable and antenna strain relief, and environmental checks.

The UI still says **Actual heater state: unverified** because there is no CAN telemetry decoding that independently confirms climate state. A human-observed successful test does not change that firmware limitation. No automotive transient, EMC, environmental or unattended-use qualification is claimed.

## Evidence and publication

- [Receive-only capture summary](../firmware/leaf-heat/verification/receive-only-2026-11-15.json)
- [Initial CAN-enabled image](../firmware/leaf-heat/verification/heat-enabled-2026-11-15.json)
- [Session-key update](../firmware/leaf-heat/verification/session-key-2026-11-15.json)
- [Button fix, latest flashed image](../firmware/leaf-heat/verification/button-fix-2026-11-15.json)

These are chronological snapshots: an earlier file saying transmit/heating was untested remains accurate for that stage. This document records the later owner-confirmed On/Off result. No new CAD, BOM, Gerber, purchase or enclosure revision was required by today's firmware and commissioning progress. Documentation changes remain local; GitHub publication has not been requested for this update.
