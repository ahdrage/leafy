# Rev F sourcing and electrical review — 12 September 2026

## Result and scope

The revision uses in-stock Mouser candidates for the three unavailable hand-part groups, while retaining the existing design requirements and all 41 circuit components. Native KiCad ERC, DRC, connectivity and schematic parity pass. The independent review checks the actual native CAD and exports against an explicit circuit pin map and the preserved Rev E files. These results do not establish physical performance; the limitations and bring-up tests below remain applicable.

## U3 — automotive CAN transceiver

**TCAN3403DRQ1 → TCAN3404DRQ1.** Both are members of TI's automotive 3.3 V TCAN340x-Q1 family in the same SOIC-8 package. The selected replacement retains the AEC-Q100 qualification, ±58 V bus-fault rating, ±30 V common-mode range, CAN/classical-CAN support, undervoltage behaviour, dominant-timeout and thermal protection relevant to this circuit. These are component ratings, not a qualification of the assembled board. See the [combined TI datasheet](https://www.ti.com/lit/gpn/TCAN3404-Q1), especially pin functions and operating-mode tables.

The material difference is pin 5. On the old chip it supplies the digital I/O interface; on the new chip it is active-high SHDN. Rev F connects it to the ground plane through the existing short trace and via. It must never remain on the 3.3 V rail. Three obsolete segments between C13 and pin 5 are removed. C13 retains its independent 3.3 V plane connection and remains an additional rail bypass. C12 remains the short local VCC bypass. No signal or switching-power path is rerouted.

| Circuit state | U3 SHDN / pin 5 | STB / pin 8 | Intended behaviour |
| --- | --- | --- | --- |
| MCU reset / programming | LOW, hardwired | HIGH through existing R10 | CAN standby; transmitter disabled |
| Normal CAN operation | LOW | LOW from GPIO1 | CAN transmit/receive enabled |
| CAN inactive | LOW | HIGH from GPIO1 | Same low-power standby control used by the existing design |

The old chip's separate low-voltage I/O supply was tied to 3.3 V, so its variable-voltage capability was not used. The replacement's additional shutdown mode is also not used: grounding SHDN keeps the existing STB-controlled normal/standby behaviour. GPIO4 TX, GPIO5 RX, GPIO1 STB and the cable contacts are unchanged. No firmware GPIO change is introduced.

## J1 — connector

**182-009-113R531 → 182-009-113R561.** NorComp's [manufacturer drawing, revision 16](https://content.norcomp.net/rohspdfs/Connectors/18Y/182/182-yyy-113Ryy1.pdf) gives a common PCB pattern. Both options use fork boardlocks; option 53 has flush 4-40 inserts, while 56 includes 4-40 female screwlocks. Contact count, gender, shell/contact materials, plating, current/voltage and temperature ratings remain in the same family.

The native footprint was independently checked for 2.77 mm contact pitch, 2.84 mm row spacing, 1.385 mm row stagger, 24.99 mm anchor centres and 3.2 mm anchor holes. Contact holes remain 1.2 mm, matching the drawing's approximately 1.19 mm recommendation. No PCB pad or drill change is required. The project-local footprint has been renamed to the actual purchased variant, including its schematic filter and purchasing fields.

The fitted screwlocks extend outward, beyond the board edge. Allow clearance in the enclosure and verify that the actual Nissan cable seats fully and its screws engage freely. The inherited generic DB9 3D body is approximate and does not prove enclosure or cable fit; use the manufacturer's drawing and the physical connector for that check.

## C5–C7 — output capacitors

**GRM32ER71E226KE15L → C1210C226K3RAC7210.** All three remain installed. The selected KEMET part retains 22 µF, 25 V, X7R, ±10% and the 1210 case size. The [KEMET data](https://search.kemet.com/component-documentation/download/specsheet/C1210C226K3RAC7210) gives 3.2 × 2.5 mm body dimensions and −55 to +125 °C operation. The maximum stated height is 2.8 mm; allow this when choosing an enclosure. “7210” is reel packaging, and Mouser supplies small cut-tape quantities.

The same nominal 66 µF bank, 22 µH inductor, regulator, feedback divider and copper remain. TI's [LMR36510 datasheet](https://www.ti.com/lit/ds/symlink/lmr36510.pdf), table 8-1, recommends three nominal 22 µF capacitors for a 3.3 V / 400 kHz design. The table explicitly labels these as rated capacitances; it must not be misread as guaranteeing 66 µF after DC bias.

KEMET's supplied model graph was inspected: near 3.3–3.6 V, the typical loss is roughly 10–15%, giving about 56–59 µF for the bank at room temperature before tolerance/aging. Applying −10% capacitance tolerance and −15% X7R temperature allowance to the 15%-bias-loss estimate gives about **42.9 µF before aging**. This is an engineering estimate from a typical model, not a guaranteed minimum or a loop-stability test. Model graphs and source PDFs are retained in `references/`.

The substitution meets the nominal electrical/package selection and retains TI's recommended three-capacitor bank. It does not establish identical ESR, aging or transient curves across manufacturers. TI requires load-transient/loop validation for production; verify startup, ripple, load steps, temperature and capacitance derating on the assembled prototype. Do not reduce the bank to two parts merely because TI also lists a size-constrained option.

## Verification completed

- Fresh KiCad 10.0.6 schematic ERC: no reported violations.
- Fresh DRC with copper refill, all-track reporting and schematic parity: no violations, unconnected items or parity issues.
- Explicit datasheet-based pin map checked for the power regulator, ESP32 module, CAN chip, UART protection, cable/header, diodes, switches, passives and test holes.
- The only schematic-net difference from Rev E is U3.5. Every remaining trace/via outside the three removed segments and two regrounded items retains its geometry and electrical net.
- All footprints retain their actual pad sizes, drills, locations and orientations. Four layers, the dedicated ground plane, supply regions, antenna keepout and hand-solder thermal rules remain.
- All 41 components, four factory placements, 37 hand placements, 21 hand-shopping lines and 74 pieces for two boards checked. Factory-only paste and placement coordinates verified.
- Fresh Gerbers, separate plated/nonplated drills, schematic PDF, native KiCad files and package contents hashed and cross-checked. Rev E source files remain byte-identical.

Reports: `exports/erc.json`, `exports/drc-final.json`, `exports/independent-audit.json`, `exports/manufacturing-audit.json` and `deliverables/manifest.json`. No new design-rule ignores or individual exclusions were added. The inherited DRC ignores footprint-type mismatch for SMT parts with plated thermal holes and unused tuning-profile geometry. ERC retains the preceding project's ignores for one-off global labels, four-way junctions, simulation models and footprint filters. No shorts, clearance violations, missing electrical connections or schematic-parity errors are waived. The actual rule settings are compared directly to Rev E.

## Remaining physical tests and inherited limitations

This review preserves the existing design; it does not convert it into a qualified automotive product. There is still no runnable heater firmware. The car's model-year/TCU arrangement, cable mapping and actual On/Off sequence need confirmation as described in [VEHICLE-WIRING.md](VEHICLE-WIRING.md).

Complete the four-part factory assembly and all hand soldering, then follow [HAND-ASSEMBLY.md](HAND-ASSEMBLY.md). Check polarity and shorts before a current-limited 12 V bench start with the MCU held in reset. Specifically check that U3 pin 5 connects to ground. Verify the 3.3 V supply stays within 3.0–3.6 V during startup, radio activity and load steps. Check CAN standby during reset and programming, then prove communication on a terminated bench network before connecting the car.

The prior requirements for input hot-plug/ringing measurement, thermal-hole solder-wicking review, parked-current/low-battery handling, cold/vibration/transient/EMI testing and actual vehicle verification remain. There is no hardware low-voltage disconnect, added damped input bulk capacitor or common-mode choke. The B3F buttons retain their −25 to +70 °C limit and must be fitted after cleaning. These are inherited prototype limitations, not newly removed protections.

The 65 V regulator limit is not a 65 V continuous-input rating for the complete board. Do not order or manufacture from old saved Rev E quotations when assembling this Rev F BOM. No purchase or manufacturer submission was made in this revision task.
