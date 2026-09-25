# Rev F verification and proposed Rev G plan

Reviewed 13 September 2026. **Plan only: no PCB, schematic, BOM, manufacturing package or enclosure was changed.**

I recommend a focused Rev G before ordering: improve the input supply and local regulator layout, add independent low-battery protection, and resolve exposed-pad assembly with the manufacturer. Keep the 100 × 100 mm board, mounting holes, Wi-Fi module, single CAN interface and hand-solder approach. The supplied audit is substantially correct; its open concerns are not evidence that the existing board is certain to fail.

## What I verified

Fresh KiCad ERC returned zero violations. Fresh DRC with copper refill, all-track reporting and schematic parity returned zero violations, unconnected items or parity issues. Re-running the existing static audit passed all **1,627 checks**. All 41 components, the four factory placements (U1/U2/U4/L1), 37 hand placements and all five manufacturing/review package hashes still agree. The PCB and schematic hashes remain identical to the released Rev F files. No additional rule exclusions were introduced.

These are CAD checks under the configured rules. They do not measure electrical operation. The first sandboxed DRC process aborted without a report; the successful rerun produced the retained report. The supporting files are [verification summary](verification-summary.json), [ERC](erc.json), [DRC](drc.json) and [existing audit rerun](independent.json).

| Supplied concern | Verification and decision |
| --- | --- |
| Input damping and transient survival | Confirmed design gap. C1 = 2.2 µF/100 V and C2 = 220 nF/100 V, both ceramic. No separate input damping branch is present. The path is J1 → F1 → D1 → VPWR, with D3 across VPWR/GND. Improve this before ordering. |
| Parked battery drain | Confirmed. U1 EN is tied to VPWR; R7/R8 measure VPWR after D1; there is no independent battery cutoff. Add hardware protection and a measured firmware power budget. |
| Regulator placement | Confirmed by summing actual routed pad-centre paths: U1.6 → C3.1 **8.500 mm**, U1.5 → R2.1 **8.747 mm**. U1.7 → C4.1 is also **5.621 mm**. Revise the small regulator cluster rather than increasing every component gap. |
| Exposed-pad assembly | Confirmed unresolved process requirement. U1 has six 0.33 mm plated thermal holes; U2 has twelve 0.30 mm holes. Existing manufacturing notes already request process review. These holes are not automatically a defective footprint. |
| Buttons | Confirmed environmental limit. The exact B3F-1000 specification is −25 to +70 °C, with no icing/condensation. Prefer a better-temperature through-hole replacement while retaining easy manual BOOT/RESET. |
| Vehicle profile and bus | Confirmed limitation. J1 pins 2/7 connect to EV-CAN; 4/5 are unconnected. Registration year alone does not establish the actual model-year/TCU arrangement. Verify the car and cable before locking the next release. |

The U3 SHDN pin is correctly grounded, and standby is pulled high during reset. Its pin functions agree with [TI's TCAN340x-Q1 datasheet](https://www.ti.com/lit/gpn/TCAN3404-Q1). The nominal regulator output is **3.3148 V**. I found no new confirmed connectivity error in these checks. The project still has no runnable heater application.

## 1. Improve input protection and damping

TI describes cable/ceramic resonance, recommends additional damped input capacitance, and asks for close local bypass and feedback placement. Its EN input also supports an external undervoltage divider. These recommendations support the proposed changes; they do not establish that Rev F will fail. See [LMR36510 §§7.3.2, 8.4–8.5](https://www.ti.com/lit/ds/symlink/lmr36510.pdf).

Add a through-hole aluminium electrolytic across protected VPWR/GND, near the regulator input. **47 µF, 63 V, 105 °C** is an initial component-selection target, not an approved part or final electrical rating. Retain C1/C2. Select the final capacitor using its ESR versus temperature, ripple rating, lifetime, physical height and the calculated clamped waveform. Provide an optional series-resistor position in the added capacitor branch so damping can be adjusted without putting resistance in the board's entire power path. The final resistor/capacitor values must follow the cable/input model and measurements.

Review F1, D1 and D3 as one protection circuit: allowable steady input, positive and negative pulses, source impedance, pulse duration, current path, diode surge limits, fuse clearing and TVS energy/temperature. A TVS wattage or the regulator's voltage rating alone cannot settle this. Define the test envelope for this Leaf's low-voltage supply rather than assuming a generic alternator load-dump requirement. [TI's input-protection reference design](https://www.ti.com/tool/TIDA-01167) illustrates why system-level conditions matter; it is not evidence that this board meets those conditions.

Deliverable before release: a short protection calculation with component margins and a bench-test specification. If the existing TVS/diode/fuse cannot meet that envelope, revise them before exporting Rev G. Do not label the board automotive-qualified based on this calculation.

## 2. Rework only the regulator cluster

Place C1/C2, C3, C4 and R1/R2 around U1 to shorten their connections and ground returns. Aim for a few millimetres of direct connection where practical, especially C3 and the FB divider; this is a design target, not a manufacturer-specified universal length limit. Keep the switch-node area compact and route feedback away from it. Retain the existing internal ground reference and intentional track widths for different current paths.

Keep 1206/1210 hand pads and enough iron access. There is no benefit in moving an essential bypass farther away merely to give it the same spacing as unrelated components. If a satisfactory local layout needs closer packing than is comfortable to solder, obtain an optional assembly price for these six local passives. The default remains hand fitting wherever the revised geometry allows it.

Deliverable: an annotated regulator close-up showing the input-current loop, VCC return, bootstrap loop and feedback path, followed by the full CAD checks. Physical startup, ripple and load-step tests remain necessary after assembly.

## 3. Add independent low-battery protection

Use a low-current voltage monitor, powered from the protected input, to hold U1 EN low on a low-battery condition. Give it deliberate hysteresis and delay so removing the load does not make it repeatedly reboot as battery voltage rebounds. It must work without the ESP32 or Wi-Fi firmware running. This disables the main regulated load; it does not eliminate every leakage path or physically isolate the complete box from the battery.

The [TPS3762-Q1 family](https://www.ti.com/lit/gpn/tps3762-q1) is one candidate for a high-voltage, low-current supervisor. Its variants differ in thresholds, hysteresis, delays and latching; no exact ordering code is selected by this plan. Choose the variant and surrounding circuit together. This small IC should be factory fitted if used, increasing the factory list from four to at least five parts. Confirm sourcing and setup cost before fixing the BOM.

A two-resistor divider on the existing EN pin is cheaper, but the datasheet's 1.157–1.300 V rising-threshold range, divider error and D1 drop make it a comparatively coarse cutoff. I would use that only if a worst-case calculation proves its entire operating window acceptable; I would not present it as a precise battery protector.

Set the actual cutoff/restart voltages after confirming the fitted 12 V battery chemistry and the car's resting/charging voltages. The voltage used for protection must represent battery voltage with a documented error budget. A dedicated protected sense divider ahead of D1 is one option; simply moving the ESP32 ADC connection to the raw input is not sufficient protection.

Review the existing R7 ADC path during shutdown: VPWR can still feed BAT_SENSE when the 3.3 V rail is off. Gate or otherwise redesign that path as needed to meet the MCU's unpowered-input limits. Check all other potential back-power paths as well. Include monitor current, divider current, regulator shutdown current, TVS leakage and temperature effects in the off-state budget.

Normal low battery should give firmware a chance to send Off before the hardware threshold is reached. **Turning off the box's power is not the same as sending Heat off to the car.** Verify the car's own climate timeout and failure behaviour; never claim that this power cutoff alone guarantees the heater stops.

## 4. Keep Wi-Fi reachable without wasting battery

Deep sleep disconnects Wi-Fi. For normal operation at home, implement modem sleep plus automatic light sleep, which Espressif documents as preserving the connection. Deep sleep can be reserved for an explicit offline condition, with bounded timed reconnect attempts. [Espressif sleep documentation](https://docs.espressif.com/projects/esp-idf/en/latest/esp32c3/api-reference/system/sleep_modes.html).

Initial engineering goals: **at most 2 mA average at the 12 V input while idle and reachable on home Wi-Fi**, and **at most 100 µA from the battery after hardware shutdown**, both to be checked over the intended temperature range. These are targets, not measured results. A continuous 2 mA load consumes 1.44 Ah in 30 days, in addition to the car's own consumption; acceptability depends on the battery and parking duration.

Measure with good Wi-Fi, weak Wi-Fi, the router off, repeated reconnects and sustained operation. Use bounded reconnect/backoff and watchdog recovery. Keep CAN in standby when idle and avoid periodic wake/poll frames that prevent the car's ECUs from sleeping. Test reset, brownout and lost Wi-Fi without replaying a stale On command. Serialize On/Off requests and validate the actual end-to-end heater behaviour, not merely successful CAN transmission.

## 5. Resolve assembly and the buttons

Ask the selected assembler to review both exposed pads, paste apertures, stencil thickness, thermal holes, reflow and inspection. Agree the process before manufacturing. Prefer an accepted standard small-via process if it meets the package requirements; obtain a separate price if filled/capped holes are required. Tenting is not equivalent to filling. TI explains solder loss and the interaction of via and stencil dimensions in its [PowerPAD layout guidance](https://www.ti.com/lit/an/sloa120/sloa120.pdf). Do not delete thermal connections merely to make fabrication cheaper.

Keep manual BOOT and RESET useful for a beginner. Review a through-hole **C&K PTS645** option as a replacement for SW1/SW2: the current [series datasheet](https://www.ckswitches.com/media/1471/pts645.pdf) gives −40 to +85 °C. Confirm the exact variant's hole pattern, internally connected pin pairs, actuator height, signal-current suitability and Mouser stock before substitution. This improves the temperature range; the series is not automotive-qualified and does not establish condensation protection. The [current Omron specification](https://components.omron.com/sites/default/files/datasheet_pdf/A070-E1.pdf) supports the original audit's limitation.

If sourcing or cost prevents the upgrade, make the switches optional service components and document operation using a removable programming jig. They are not required for normal Heat on/off operation.

## 6. Confirm the car, then release a coherent revision

Verify build/model year, fitted TCU and the numbered cable contacts. The current [OVMS guidance](https://docs.openvehicles.com/en/latest/components/vehicle_nissanleaf/docs/index.html#remote-climate-control) separates pre-2016 EV-CAN remote commands from later CAR-CAN configurations and gives different TCU instructions. Retain the one-transceiver design if the intended earlier profile is confirmed. Resolve any different profile explicitly before committing the next PCB; software cannot connect an unconnected DB9 pin.

For Rev G, preserve the board outline, mounting-hole coordinates, J1 position, radio position and antenna keepout. Recheck the new bulk capacitor and any new parts against the Blender enclosure; a taller capacitor may require a shorter part, a different placement, or a case change. Refresh its board reference and rerun case-fit checks after the hardware revision. The current enclosure is tied to Rev F's exact board hash.

Regenerate the schematic, PCB, complete BOM, hand-shopping list, factory BOM, placements, factory-only stencil, Gerbers, diagrams and all packages as a matched Rev G set. Recheck source-to-export parity, assembly ownership, sourcing, dimensions and hashes. Keep Rev F as an archive. Reprice using the actual final parts and assembly process; this plan does not claim the current quotation or Mouser cart covers the changes.

## Order and test sequence

1. Confirm the vehicle profile and choose the battery-protection behaviour.
2. Complete the protection calculations, regulator relayout, supervisor circuit and button selection in Rev G.
3. Finish assembler DFM review, all static checks, the enclosure check and updated quotations.
4. Order one or two prototypes, with the difficult parts factory fitted.
5. After hand assembly, bench-test current-limited startup, rail accuracy, hot-plug ringing, radio load steps, hardware cutoff/recovery, off-state leakage and CAN reset/standby behaviour. Apply defined transient tests with suitable equipment. Verify component ratings and the ESP32 supply limits throughout.
6. Validate the firmware on a terminated bench CAN network. Check the cable, begin vehicle testing in receive-only mode, then test bounded Heat on/off operation on the confirmed profile. Measure car sleep/current and closed-case Wi-Fi/temperature before leaving it connected unattended.

The purchasing decision comes after step 3. The decision to leave the unit in the car comes after step 6. A prototype order is not a claim of proven vehicle operation.
