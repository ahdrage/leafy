# Rev E design review — 12 September 2026

See also the later [fresh recheck](RECHECK-2026-09-12.md) and [Rev E vehicle wiring guide](VEHICLE-WIRING.md). The first-power guide now distinguishes static divider tolerances from light-load PFM regulation; 3.22–3.41 V below is not a complete acceptance window.

Rev E is a **100 × 100 mm** revision of the 150 × 150 mm hand-solder board. The circuit, ratings, footprints' pad geometry and factory/hand ownership are retained. The later recheck corrects D1's ordering code to B1100-13-F; the other 40 MPN entries remain unchanged. The changes are placement, routing, copper-zone outlines and printed labels. J1's printed outline is shortened where its housing overhangs the edge; its pads and body dimensions are unchanged.

## What changed and why

Most noncritical hand-fitted parts now use more of the available board surface. The output capacitor spacing increases from 7 to 9 mm, R1/R2 from 5 to 8 mm, R3/C8 and R18/R19 from 6 to 9 mm, R5/R6 from 10 to 13 mm, R9/D6 from 9 to 12 mm and the buttons from 15 to 19 mm. These are centre-to-centre distances; exact values are recorded in `exports/independent-audit.json`.

U1, C1, C2, C3, C4 and L1 retain their Rev D positions and orientations. This keeps the input switching loop, bootstrap circuit and VCC bypass local while other parts gain space. The feedback divider stays below the regulator, and its output-sense route goes around the output capacitor bank, away from the switch node. This follows the layout priorities in [TI's LMR36510 datasheet, section 8.5](https://www.ti.com/lit/ds/symlink/lmr36510.pdf). The selected component values remain those of our preceding revision; the retained 100 kΩ / 43.2 kΩ divider gives about 3.315 V nominal.

The 3.3 V supply and protected-input distribution remain copper planes on In2.Cu. The protected-input region includes a diagonal branch to R7's battery-sense feed. R6 uses a short bottom-layer connection to a 3.3 V via outside that protected-input region. All supply-plane connections were checked after refilling. In1.Cu remains a dedicated ground reference with no signal routes; there are 107 separate ground vias. Both internal layers contain no routed tracks.

C9/C10 still bypass the module supply. The antenna extends beyond the top edge; the existing copper keepout applies to all four copper layers, and sampled points in its interior contain no poured copper. The module's internal RF circuitry is unchanged. Reference: [Espressif layout guidance](https://docs.espressif.com/projects/esp-hardware-design-guidelines/en/latest/esp32c3/pcb-layout-design.html).

CAN-H and CAN-L run through D4 between the connector and transceiver. There is still no added CAN termination. UART protection remains at J3, with its short external path and local C14 bypass. J3 still has GND, board RX and board TX only. No USB circuitry, modem, extra choke or firmware functionality was added.

The front carries component references and connector/test-point labels. The 21-row hand-parts value table is on the back. Factory paste exists only at U1/U2/U4/L1, and all other component pads have hand-solder thermal reliefs. Factory reflow pads retain their direct thermal connections.

## Verification results

| Check | Result |
| --- | --- |
| Native KiCad 10.0.6 schematic ERC | 0 reported violations |
| PCB DRC, all severities and all track errors | 0 reported violations |
| Unconnected items | 0 |
| PCB versus schematic parity | 0 issues |
| Per-item DRC exclusions | None |
| Exact outline / placement origin | 100 × 100 mm / lower-left (0,100) |
| Original circuit pins | All retain their Rev D nets |
| Purchasing part numbers | 40 retained; D1 corrected to B1100-13-F |
| Factory BOMs, placements and paste | U1/U2/U4/L1 only |
| Hand BOM quantities | 37 for one board; 74 for two, before spares |
| Manually placed critical copper | All 246 items present with unchanged geometry, nets and sizes after routing |
| SMD placement side | All top |
| Bare features | Seven plated test holes, four mounting holes |
| Rev D native source | Preserved byte for byte against the recorded baseline |

The independent audit passes 894 assertions, many of them per-pin or per-route comparisons. This is software verification, not 894 physical tests. Final board SHA-256: `67d27bb2c23a13823af77b201cde4d57e32b49e7daecb8776d972c66934cc482`. Schematic SHA-256: `ee9ef8680a679b36ade1f558a5db0452def9f0172447a49d82466f9788d12518`.

Reports: `exports/drc-final.json`, `exports/erc.json`, `exports/independent-audit.json` and `exports/manufacturing-audit.json`. Gerber/drill hashes and exact factory placement membership are checked again when packaging. Intermediate router files are excluded from manufacturing packages; the final refilled native KiCad board is the authority.

The inherited DRC ignores footprint type mismatch for SMT parts with plated thermal holes and unused tuning-profile geometry. ERC retains the preceding project's ignores for one-off global labels, four-way junctions, simulation models and footprint filters. No shorts, clearance violations, missing electrical connections or schematic-parity errors were waived. Native footprint-library matching remains checked.

## What these checks cannot establish

The factory fits U1/U2/U4/L1, leaving the circuit incomplete until the remaining 37 parts are soldered. Follow `HAND-ASSEMBLY.md`: inspect joints, verify orientation and shorts, then use a current-limited 12 V bench supply with the radio held in reset to verify the rail before programming. The static tolerance estimate remains approximately 3.220–3.412 V; startup, ripple, load steps and thermal behaviour need measurement.

Thermal holes are ordinary plated holes, not filled/capped vias. The assembler must review U1/U2 stencil coverage, solder wicking and exposed-pad inspection. U2 thermal holes remain mask-open on both surfaces. Do not assume tenting equals filled vias. The 3D preview lacks the F1 fuse body and uses an approximate DB9 model; it is not an enclosure specification. Both the module antenna and DB9 housing overhang the board.

The B3F-1000 buttons retain their −25 to +70 °C range and non-washable construction. They are fitted after cleaning. Larger ceramic capacitors still require controlled heating during hand soldering. This prototype has not been qualified for cold parked-car operation, vibration, automotive transients or EMC. The 65 V regulator rating is not a continuous-input rating for the complete board.

Firmware, Wi-Fi/UART/CAN bench tests, parked-current measurements, low-battery handling and the actual Leaf heater sequence remain unimplemented or untested. Use the exact Nissan cable pinout and verify the applicable car/TCU configuration before a vehicle test. CAD connectivity does not prove cabin heating. The smaller PCB may reduce bare-board cost, but the total assembled price requires a new quote.
