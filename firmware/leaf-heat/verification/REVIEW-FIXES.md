# Firmware review fixes — 14 September 2026

These are firmware-only changes for the Rev G family, including the current G.2 board. The PCB, schematic, parts lists, supplier files and hardware manufacturing packages are unchanged. The default source still has CAN writing disabled and empty Wi-Fi credentials. Nothing was flashed.

## Fixes

1. **Low-battery protection per heating session.** The control task resets both its low-voltage timestamp and early-Off latch before each admissible On request. Admission requires CAN enabled, sufficient measured voltage, no active command sequence and an unexpired request. Reset happens before attempting the wake frames because a failed transmission still leaves an uncertain heat request in `Control`. Rejected requests cannot postpone an existing stop interval.
2. **Bounded normal CAN retries.** Single-shot mode is disabled so ordinary arbitration loss does not abort the command. The controller retries the current frame while the task waits up to 40 ms for its result. A missing ACK, timeout or terminal failure returns an error and invokes standby/driver cleanup, cancelling pending transmission. TX queue length remains zero, so no backlog of On frames can accumulate. A bus-off/failure alert takes priority over a simultaneous success alert; failed alert setup prevents transmission entirely. This is a scheduler timeout, not a guaranteed hard real-time cancellation deadline.
3. **Transceiver standby exit.** A 100 µs ROM delay replaces a 1 ms task delay that became zero ticks under the project's 100 Hz scheduler. The fitted TCAN3404's maximum standby-to-normal time is 30 µs. This wait is for standby exit; it does not replace supply-ramp or cold-start validation.

## Evidence

- Initial regression run: 10 existing tests passed; seven of 14 added tests failed on the reported defects and related CAN error handling. The captured red log predates an additional busy-request regression and a refinement of the bus-off simulation.
- Final regression run: **25 passed, zero failures** (10 core, six control-task, nine CAN-transport tests).
- The tests compile the current production task/transport functions verbatim with small SDK doubles. They verify software decisions and simulated timing, not the physical controller or bus. The control core is compiled directly.
- The default commissioning configuration and a temporary CAN-enabled configuration both compile/link for ESP32-C3 using pinned Espressif32 6.12.0 / ESP-IDF 5.5.0. The latter uses empty Wi-Fi credentials and is not a flash/release image.
- G.2 native PCB/schematic hashes and all five hardware package hashes are checked against the existing hardware manifest. No hardware regeneration is needed.

The installed ESP-IDF 5.5.0 legacy TWAI implementation maps `ss == 0` to unlimited controller retries while active, acquires a power-management lock for the driver lifetime, and clears pending transmission state on stop. The firmware's result timeout and stop/uninstall path therefore provide the software bound. ESP32-C3 frequency-switch code also updates the ROM delay calibration. [Espressif legacy TWAI documentation](https://docs.espressif.com/projects/esp-idf/en/v5.4.4/esp32c3/api-reference/peripherals/twai.html#message-fields-and-flags) describes single-shot arbitration behavior; the installed 5.5.0 source was used to confirm this project's exact API implementation.

The standby timing requirement is from the [TI TCAN3404-Q1 datasheet](https://www.ti.com/lit/gpn/TCAN3404-Q1), switching characteristics §6.9 (`tMODE`, maximum 30 µs). The configured RTOS tick rate is 100 Hz, and FreeRTOS `pdMS_TO_TICKS` uses integer division.

## Remaining bench checks

Before vehicle transmission, use an isolated bench CAN setup with correct termination and another ACK-capable node:

- Measure STB falling edge to first TXD activity; confirm at least 30 µs on each standby exit.
- Introduce competing traffic and verify a request succeeds after arbitration loss. Remove ACK / induce a bus fault and verify bounded abort, standby return and no delayed On replay.
- Exercise two heat requests with supply recovery only to about 12.3 V between them, then a drop below 12.2 V. Check a fresh approximately ten-second low-voltage interval and early Off for each request. Repeat with a failed wake transmission. Values are measured after D1 and require ADC calibration.
- Retain the hardware guide's supply, cutoff, current-draw and wiring checks. Confirm real heater behavior beside the car after commissioning.

Compilation and these simulations cannot establish physical timing, RF availability, current draw, vehicle acceptance or successful heater shutdown. Wi-Fi behavior and the independent hardware battery cutoff are unchanged.
