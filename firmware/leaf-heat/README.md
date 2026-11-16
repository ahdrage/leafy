# Rev G Leaf heat firmware

Buildable ESP32-C3 prototype for the **Rev G custom board, including the current G.5**. It serves a local Heat on/Off page and stays associated with the home Wi-Fi using modem sleep and automatic light sleep. It retries indefinitely at 1, 2, 4, 8, 16, then 30-second intervals. It does not use scheduled deep sleep, deliberately disconnect Wi-Fi, or replay Heat on after reconnect/reboot.

**CAN writing is disabled by default in the public template.** On 15 November 2026 the explicitly enabled test unit was flashed, booted and used for owner-confirmed climate On/Off with the charging cable connected. Receive-only testing and bench observations are recorded in the [commissioning log](../../docs/COMMISSIONING-2026-11-15.md). On 16 November the owner also reported successful unplugged Heat On, and the subsequent dual-battery website image was flashed and received both signals. Unplugged Off, latest-image heater regression, physical timeout/fault tests and long-term reliability remain unverified. See [the follow-up record](../../docs/WEBSITE-BATTERY-2026-11-16.md).

Use the current source tree for the November firmware. Older firmware ZIPs are historical snapshots, not the current build.

For a fresh portable setup, see [the build guide](../../docs/BUILD-GUIDE.md). The commands below also document the original local tool layout.

## Configure, build and flash

1. Copy `include/settings.example.hpp` to `include/settings.hpp`. Enter the home's 2.4 GHz Wi-Fi SSID/password and a separate control key of at least 12 characters. Keep this local file private. The control key is entered on the web page and is not embedded in its HTML. Credentials are stored in the firmware image, so keep configured binaries private too.
2. Keep `LEAF_CAN_WRITE_ENABLED false` through assembly, supply/current checks and initial network commissioning. Set the ADC correction from meter measurements at VPWR. The nominal divider multiplier is **32.2765957447**, different from Rev F.
3. Build from the repository root:

   ```sh
   PLATFORMIO_CORE_DIR="$PWD/tools/platformio" tools/firmware-venv/bin/pio run -d firmware/leaf-heat
   ```

   The project pins PlatformIO Espressif32 **6.12.0**, with ESP-IDF. The bundled local environment has PlatformIO 6.1.18. A default build uses empty Wi-Fi credentials and therefore cannot join a network until configured; it is a compile-check image.
4. Power the fully assembled board from a current-limited 13.5–14 V bench supply through J1. Use a **3.3 V logic** UART adapter: TX → J3 pin 2/RX, RX → pin 3/TX, GND → pin 1. Leave the adapter's power lead insulated. Connect adapter only after board power is present; disconnect it before removing board power. There is no USB socket or UART power input.
5. Hold BOOT, press/release RESET, release BOOT. Run `pio run -d firmware/leaf-heat -t upload --upload-port /dev/cu.YOUR_ADAPTER` using the same `PLATFORMIO_CORE_DIR` and executable as above. Choose the actual adapter port, not a guessed one. The build generates the correct bootloader/partition/application offsets; do not flash the application alone at address zero.
6. Read the 115200-baud serial log for the IP address. Reserve that IP in the router and bookmark `http://ADDRESS/`. Hostname is `leaf-heat`, but `.local` discovery is not implemented. Both phone/computer and car must be on the same LAN without guest/client isolation. The page has no cloud or Internet dependencies.
7. Only after the wiring, TCU and bench CAN checks in the hardware guide pass, explicitly enable CAN writing, rebuild and flash. Test beside the car before relying on remote heating.

## Behavior and limits

### Temporary receive-only commissioning

Set `LEAF_CAN_LISTEN_ONLY true` in private `include/settings.hpp`, keeping
`LEAF_CAN_WRITE_ENABLED false`. A compile-time guard rejects enabling both.
This diagnostic runs the legacy TWAI driver at 500 kbit/s in hardware listen-only
mode, with no transmit queue. It does not send data, ACKs or error frames.
The normal heater/control task is not started. HTTP commands remain locked.
The web status and five-second UART reports show received-frame count, last ID,
controller bus errors, dropped frames and listener errors. Counts are since boot;
the last ID is not a decoded vehicle state. An idle/sleeping vehicle may produce
no frames. Successful reception does not validate the transmit path.

This is temporary test firmware: the running CAN controller can prevent normal
light sleep, so do not treat its current draw as the normal parked-current result
or leave it installed for unattended use. Restore `LEAF_CAN_LISTEN_ONLY false`
and rebuild/flash after the diagnostic. Do not enable CAN writes merely because
receive counters increase.

The host runner checks six receive-only behaviours against SDK doubles using
the actual extracted listener functions, as part of the current 48-check suite.

The web page requires the configured key on every control request. **Save key for
this tab** validates it using the read-only `/api/auth` endpoint, then stores it
in browser `sessionStorage`. Saving never queues a heater command. Reloading the
same tab restores the key without replaying a command. **Forget key** removes
it; rejected keys are not saved. Session storage is not a password vault and a
browser may restore sessions, so use Forget on a shared device. The key is not
embedded in the page or placed in URLs. Responses show HTTP acceptance/rejection
separately from CAN status; a network failure is an unknown outcome, never an
automatic command retry. Commands use a custom HTTP header, accept no request
body and expose no CORS permission. HTTP is unencrypted: use only the trusted
home LAN, with no port forwarding. This is not an Internet-facing service.

The host runner now also runs three HTTP-auth checks and seven browser-script
checks (48 checks total). Browser-script checks use Node.js to execute the
actual embedded JavaScript against mocked DOM, storage and HTTP boundaries.

Run `node firmware/leaf-heat/tests/web_buttons_browser_test.cjs` from the repo
root with Playwright installed and Chrome available for the real-browser click
regression. All requests are intercepted at `http://leafy.test`; this test never
contacts a board. It reproduces the native `HTMLButtonElement.command` collision
that prevented the original inline Heat On/Off handlers from running, and verifies
the script-bound listeners, displayed HTTP result, session restore and no replay.

On wakes the 2013–2015 EV-CAN profile, sends 24 climate requests 100 ms apart and the OVMS completion frame at approximately 3.3 seconds. Off cancels an outstanding On sequence. The command queue retains at most one request; delayed On requests expire after one second. With telemetry enabled, idle CAN has a 1.5-second listen-only window each minute. Between windows the transceiver remains in hardware standby and the TWAI driver is released to allow automatic light sleep. Commands preempt the passive window. With telemetry disabled, CAN stays in standby throughout idle time. After taking the transceiver out of standby, firmware waits 100 µs before transmitting, independently of the scheduler's tick rate.

Transmissions use normal CAN arbitration/retries and require a bus acknowledgement. Each frame has a **40 ms transmit-result wait**; on timeout or a terminal error the firmware puts the transceiver in standby and stops/uninstalls the driver, cancelling any pending transmission. Scheduling delays can extend the time before this cancellation executes; this is not a hard real-time deadline. Off can preempt the remaining sequence once the current bounded send returns. A failed command is not automatically replayed. A CAN ACK is **not** a confirmation that the heater started.

A local 15-minute timer requests Off even if Wi-Fi is lost. A low/invalid voltage reading blocks On; low voltage during a heat request triggers an early Off attempt after 10 seconds. Every admitted On starts a fresh low-voltage interval and re-arms this protection, including an On whose wake transmission fails and leaves the outcome uncertain. Rejected requests do not reset it. A failed early Off is not repeatedly sent during the same low-voltage episode. U5 can cut power sooner in a deep voltage dip. Loss of power, failed CAN transmission, a reset, or the car ignoring a request can prevent Off. Confirm the car's own timeout and test these cases. The page reports requests and errors, never an invented actual heater state.

The cutoff protects the 12 V battery even if firmware hangs. It also makes Wi-Fi unavailable until charging restores the board's input above its recovery threshold. This exception is unavoidable for a battery-powered always-listening device. Actual connected and disconnected-router current must be measured.

## Verification

The dated JSON files under `verification/` are chronological snapshots, not interchangeable firmware releases. `dashboard-battery-2026-11-16.json` identifies the latest flashed image; `website-battery-2026-11-16.json` records the preceding BMS-only website update; `button-fix-2026-11-15.json` identifies the preceding vehicle-tested button fix. Earlier reports/source archives remain historical and were not regenerated by the documentation update. Configured images contain secrets and must stay private.

The tested unit uses `LEAF_ADC_CORRECTION 0.9820f`, `LEAF_MIN_HEAT_VPWR 11.9f`, writes enabled and listen-only disabled. Public template defaults remain correction 1.0, threshold 12.2 V and writes disabled. Hardware cutoff is unchanged; do not copy unit-specific calibration without measurement.

The current host suite contains **48 checks**: 11 for the real command/retry core, seven for the production battery/control task, ten for the production CAN transport, six for the receive-only listener, three for HTTP authentication, seven for browser-script behaviour, and four additional suites for SOC decoding, passive CAN scheduling, JSON status and normal website status. The last four suites each contain several assertions and are counted as one check per suite. The battery/control and CAN transport checks compile verbatim functions extracted from `src/main.cpp` against simulated SDK boundaries. They exercise the actual task and transport decisions, but do not execute ESP-IDF itself or validate electrical behavior. The runner rejects missing or ambiguous source boundaries.

Coverage includes repeated heat sessions after partial battery recovery, an uncertain On following failed transmission, rejected requests, bounded CAN contention, missing ACK, bus-off, pending-frame cancellation, and standby timing at 100/1,000 Hz. Existing tests cover command timing, Off preemption, 100,000 capped Wi-Fi retries, no boot/idle replay, the local timeout and authentication.

`verification/review-fixes-red.txt` records seven behavioral failures before the fixes; `review-fixes-green.txt` records the final 25 passing tests. The original `host-red.txt`/`host-green.txt` remain historical records. `verification/build.log` records the normal ESP32-C3 commissioning build; `can-enabled-build.log` records a separate temporary compile/link check with CAN enabled and empty Wi-Fi credentials, without flashing. See [fix details and bench checks](verification/REVIEW-FIXES.md). The earlier `integration_contract.py` source-string experiment is retained as scratch work and is not behavioral test coverage or a release check.

```sh
python3 firmware/leaf-heat/tests/run_host_tests.py
```

Hardware SDK behavior was additionally inspected for TWAI queue requirements and power-management locks. Device boot, local Wi-Fi, CAN reception and supervised plugged-in climate On/Off have since been demonstrated. The [15 November record](../../docs/COMMISSIONING-2026-11-15.md) distinguishes owner observations from captured evidence. Complete the remaining [Rev G prototype tests](../../hardware/rev-g/DESIGN-REVIEW.md); these results do not establish RF range, transient immunity or unattended reliability.

Protocol source: [pinned OVMS implementation](https://github.com/openvehicles/Open-Vehicle-Monitoring-System-3/blob/85074a0ae7a983b308c6e2e081185492527ee073/vehicle/OVMS.V3/components/vehicle_nissanleaf/src/vehicle_nissanleaf.cpp). See `OVMS-NOTICE.txt` for the upstream license. Power strategy follows [Espressif's sleep guidance](https://docs.espressif.com/projects/esp-idf/en/stable/esp32c3/api-reference/system/sleep_modes.html); modem sleep plus automatic light sleep maintains Wi-Fi association, whereas explicit sleep entry does not.

G.3 antenna compatibility: ESP32-C3-WROOM-02U-N4 retains the same GPIOs and 4 MB flash. No firmware code change is needed. Connect the specified external antenna before enabling Wi-Fi. All 25 host tests were rerun successfully after the hardware substitution; initial local Wi-Fi operation is now demonstrated, while RF range and environmental testing remain outstanding.

## API and main-battery telemetry — 16 November 2026

`GET /api/v1/status` returns authenticated JSON using the same `X-Leaf-Key`
header as commands. Existing browser routes are unchanged. The Node server in
[`server/`](../../server/README.md) translates this into the iOS-facing API and
supports older installed firmware with voltage-only status.

`LEAF_TELEMETRY_ENABLED true` enables passive SOC sampling (also the fallback
when older private settings omit this macro). This decodes EV-CAN 0x55B as
`((byte0 << 2) | (byte1 >> 6)) / 10.0`, rejecting values above 100%.
Frames must be standard, non-RTR and eight bytes. Sample age is measured from
reception, and no value is supplied until a valid frame arrives. This is BMS SOC,
not necessarily the dashboard figure. It does not confirm climate state.

Sampling is receive-only for 1.5 seconds per minute while idle; it does not wake
the car or ACK frames. Normal heater commands retain their existing behavior and
collect received frames while active. Both dashboard and BMS SOC have now been received from the vehicle and displayed.
A simultaneous numeric comparison with the instrument display, parked current with
the new schedule, and heater operation after switching between modes remain
vehicle acceptance tests. The initial API image was built without flashing. The subsequent normal-website
update was flashed on 16 November; see the website record below for live validation.
See [API acceptance record](../../docs/API-2026-11-16.md).

## Normal website battery display

The installed 16 November website update shows dashboard and BMS battery percentages with separate sample ages/staleness, plus a countdown from the existing automatic Off deadline. It uses the existing `/api/status` route and needs no external server. Status refresh is bounded to three seconds and does not overlap. The [native iOS app](../../ios/README.md) was subsequently built and simulator-tested; it uses the existing BMS JSON endpoint and requires the home server. No additional firmware change or flash was needed for the app. See [website change and vehicle-check record](../../docs/WEBSITE-BATTERY-2026-11-16.md).

The dashboard/BMS follow-up displays both values, dashboard first, with independent sample ages. Dashboard decoding uses `0x1DB` byte 4 masked with `0x7f` for the 2013–2015 profile; 101–127 are invalid. It does not change the BMS field in the JSON interface. Both signals were received after READY confirmation: dashboard 95%, BMS 92.5%, both aged 26 seconds, protected supply 13.70 V and reader/command errors 0. The owner accepted the display; an exact simultaneous instrument-panel comparison was not separately logged. See [latest installation evidence](verification/dashboard-battery-2026-11-16.json).
