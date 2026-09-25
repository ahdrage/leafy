# Rev G Leaf heat firmware

Buildable ESP32-C3 prototype for the **Rev G custom board, including the current G.5**. It serves a local Heat on/Off page and stays associated with the home Wi-Fi using modem sleep and automatic light sleep. It retries indefinitely at 1, 2, 4, 8, 16, then 30-second intervals. It does not use scheduled deep sleep, deliberately disconnect Wi-Fi, or replay Heat on after reconnect/reboot.

**CAN writing is disabled by default.** No firmware has been flashed or tested in the car. Successful compilation and host tests do not validate the CAN hardware, current draw or heater response.

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

The web page requires the configured key on every control request. Commands use a custom HTTP header, accept no request body and expose no CORS permission. HTTP is unencrypted: use only the trusted home LAN, with no port forwarding. This is not an Internet-facing service.

On wakes the 2013–2015 EV-CAN profile, sends 24 climate requests 100 ms apart and the OVMS completion frame at approximately 3.3 seconds. Off cancels an outstanding On sequence. The command queue retains at most one request; delayed On requests expire after one second. CAN remains in hardware standby while idle, and the TWAI driver is released to allow automatic light sleep. After taking the transceiver out of standby, firmware waits 100 µs before transmitting, independently of the scheduler's tick rate.

Transmissions use normal CAN arbitration/retries and require a bus acknowledgement. Each frame has a **40 ms transmit-result wait**; on timeout or a terminal error the firmware puts the transceiver in standby and stops/uninstalls the driver, cancelling any pending transmission. Scheduling delays can extend the time before this cancellation executes; this is not a hard real-time deadline. Off can preempt the remaining sequence once the current bounded send returns. A failed command is not automatically replayed. A CAN ACK is **not** a confirmation that the heater started.

A local 15-minute timer requests Off even if Wi-Fi is lost. A low/invalid voltage reading blocks On; low voltage during a heat request triggers an early Off attempt after 10 seconds. Every admitted On starts a fresh low-voltage interval and re-arms this protection, including an On whose wake transmission fails and leaves the outcome uncertain. Rejected requests do not reset it. A failed early Off is not repeatedly sent during the same low-voltage episode. U5 can cut power sooner in a deep voltage dip. Loss of power, failed CAN transmission, a reset, or the car ignoring a request can prevent Off. Confirm the car's own timeout and test these cases. The page reports requests and errors, never an invented actual heater state.

The cutoff protects the 12 V battery even if firmware hangs. It also makes Wi-Fi unavailable until charging restores the board's input above its recovery threshold. This exception is unavoidable for a battery-powered always-listening device. Actual connected and disconnected-router current must be measured.

## Verification

The host suite contains **25 behavioral tests**: 10 for the real command/retry core, six for the production battery/control task, and nine for the production CAN transport. The latter two compile verbatim functions extracted from `src/main.cpp` against simulated SDK boundaries. They exercise the actual task and transport decisions, but do not execute ESP-IDF itself or validate electrical behavior. The runner rejects missing or ambiguous source boundaries.

Coverage includes repeated heat sessions after partial battery recovery, an uncertain On following failed transmission, rejected requests, bounded CAN contention, missing ACK, bus-off, pending-frame cancellation, and standby timing at 100/1,000 Hz. Existing tests cover command timing, Off preemption, 100,000 capped Wi-Fi retries, no boot/idle replay, the local timeout and authentication.

`verification/review-fixes-red.txt` records seven behavioral failures before the fixes; `review-fixes-green.txt` records the final 25 passing tests. The original `host-red.txt`/`host-green.txt` remain historical records. `verification/build.log` records the normal ESP32-C3 commissioning build; `can-enabled-build.log` records a separate temporary compile/link check with CAN enabled and empty Wi-Fi credentials, without flashing. See [fix details and bench checks](verification/REVIEW-FIXES.md). The earlier `integration_contract.py` source-string experiment is retained as scratch work and is not behavioral test coverage or a release check.

```sh
python3 firmware/leaf-heat/tests/run_host_tests.py
```

Hardware SDK behavior was additionally inspected for TWAI queue requirements and power-management locks. There has been no device runtime, RF, CAN or vehicle test. Perform the [Rev G prototype test plan](../../hardware/rev-g/DESIGN-REVIEW.md).

Protocol source: [pinned OVMS implementation](https://github.com/openvehicles/Open-Vehicle-Monitoring-System-3/blob/85074a0ae7a983b308c6e2e081185492527ee073/vehicle/OVMS.V3/components/vehicle_nissanleaf/src/vehicle_nissanleaf.cpp). See `OVMS-NOTICE.txt` for the upstream license. Power strategy follows [Espressif's sleep guidance](https://docs.espressif.com/projects/esp-idf/en/stable/esp32c3/api-reference/system/sleep_modes.html); modem sleep plus automatic light sleep maintains Wi-Fi association, whereas explicit sleep entry does not.

G.3 antenna compatibility: ESP32-C3-WROOM-02U-N4 retains the same GPIOs and 4 MB flash. No firmware code change is needed. Connect the specified external antenna before enabling Wi-Fi. All 25 host tests were rerun successfully after the hardware substitution; physical RF testing remains outstanding.
