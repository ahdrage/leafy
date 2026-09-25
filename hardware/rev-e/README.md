> **Historical development record.** The current release is [Leafy G.5](../../README.md). Use this file for context, not current ordering or wiring instructions.

# Leaf Heat Rev E — 100 × 100 mm hand-solder prototype

Open `leaf-heat-v5.kicad_pro` in KiCad. The earlier 150 × 150 mm Rev D remains preserved.

Rev E reduces the PCB to **100 × 100 mm**, 56% less area, while increasing the spacing between several hand-fitted components. The parts are distributed across the usable surface instead of leaving a large empty centre. Critical input, bootstrap and regulator-bypass components remain close to the regulator. The hand-parts value table moves to the back of the PCB.

The factory still fits **U1, U2, U4 and L1 only**. You fit the remaining **37 parts**, using the same large 1206/1210 pads and through-hole buttons as Rev D. The later electrical recheck corrects D1's purchasing code to **B1100-13-F**, retaining its 100 V / 1 A SMA diode function and existing pads. All other purchasing codes and every electrical net remain unchanged. There are seven bare plated test holes and four mounting holes.

| Example spacing, component centres | Rev D | Rev E |
| --- | ---: | ---: |
| Output capacitors C5/C6 and C6/C7 | 7 mm | 9 mm |
| Feedback resistors R1/R2 | 5 mm | 8 mm |
| R3/C8 and UART resistors R18/R19 | 6 mm | 9 mm |
| Boot resistors R5/R6 | 10 mm | 13 mm |
| Reset/boot buttons | 15 mm | 19 mm |

These are selected, independently checked centre spacings, not a promise that every component gap increased. Local bypass capacitors still need to remain near their ICs. U3 and D4 are the most demanding hand-fitted parts, with accessible leads and extended pads.

Native electrical, PCB layout, connectivity and schematic-parity checks report zero issues under the project rules. The full independent audit verifies the pin nets, part numbers, factory/hand split, clearances, manufacturing coordinates and preserved critical routing. This is an **untested engineering prototype**; firmware and bench/vehicle verification are still required.

## Files

- `RECHECK-2026-09-12.md`: fresh electrical review, corrected instructions and remaining physical tests.
- `VEHICLE-WIRING.md`: exact Rev E cable pinout, firmware GPIOs and vehicle-profile restriction.
- `HAND-ASSEMBLY.md`: parts orientation, soldering and first-power checks.
- `PROGRAMMING.md`: 3.3 V UART programming with separate 12 V bench power.
- `MANUFACTURING-NOTES.md`: exact four-part factory scope and fabrication specification.
- `DESIGN-REVIEW.md`: checks, layout decisions and limitations.
- `exports/BOM-HAND.csv`: quantities for one and two boards, excluding spares.
- `exports/BOM-FACTORY-PCBWay.csv` and `exports/BOM-FACTORY-JLCPCB.csv`: four factory parts only.
- `deliverables/leaf-heat-rev-e-gerbers.zip`: bare-PCB quotation upload.
- `deliverables/leaf-heat-rev-e-factory-assembly.zip`: fabrication, factory BOMs and placements.
- `deliverables/leaf-heat-rev-e-kicad-review.zip`: editable native project and local libraries.
- `deliverables/leaf-heat-rev-e-hand-assembly.zip`: hand-parts shopping and assembly pack.
- `deliverables/leaf-heat-rev-e-review-images.zip`: current board and schematic images.

Use Rev E files together. Do not combine Rev D placement files with Rev E Gerbers. No new quotation, order or paid manufacturing is included.
