# Rev G.1 — U5 availability substitution

Historical change record: the statements below describe G → G.1. Current layout/manufacturing files are **G.3**, with additional routing and silk changes documented in [ADI-G2-CHANGES.md](ADI-G2-CHANGES.md). The accepted U5 part and its qualification limits remain the same. Run the G.1 equivalence audit only against its archived source; use `audit_antenna_g3.py` and `audit_rev_g.py` for the current board.

The current build uses **Texas Instruments TPS3760A012DYYR, JLCPCB C5218894**, replacing TPS3760A012DYYRQ1 / C5218886. The user approved this prototype substitution on 13 September 2026 after reviewing the qualification and transient-specification differences.

**This is a BOM revision on the unchanged Rev G PCB layout.** Native filenames remain `leaf-heat-v7`; the physical board still says Rev G. Current ordering ZIPs say `rev-g1`. Use the six-part Rev G.1 factory BOM. The superseded Rev G release, BOMs and ZIPs are preserved in `history/rev-g-before-u5-g1.zip`.

The DYY 14-pin footprint, pinout, non-latching undervoltage action, 0.8 V reference, 2% internal hysteresis, open-drain output and relevant timing/threshold specifications match. There are no changes to routing, planes, pads, component positions, the hand BOM, firmware pin map or enclosure. The 11.67 V cutoff / 12.68 V restart estimates after D1 and nominal 1.27 s / 12.7 s delays remain unchanged. Firmware cannot maintain Wi-Fi while the hardware low-battery cutoff removes power.

The replacement is **Catalog grade and is not AEC-Q100 qualified**. Its specified operating supply maximum is 65 V; 70 V is an absolute maximum, not the Q1 part's additional 70 V / 50 ms operating-transient allowance. The swap does not establish vehicle transient robustness. Sources: [TI TPS3760 datasheet](https://www.ti.com/lit/ds/symlink/tps3760.pdf), [TI TPS3760-Q1 comparison](https://www.ti.com/lit/ds/symlink/tps3760-q1.pdf).

`audit_u5_g1.py` compares the entire parsed native PCB, schematic and symbol library with the archived release, allowing only this exact identity/datasheet replacement. It also checks all 55 component records and the unchanged hand BOM and native placement file, plus the explicit JLC rotation offsets. Fresh ERC/DRC and the independent electrical audit are separate checks; their JSON reports are in `exports/`.

The manufacturer fits U1/U2/U4/U5/U6/L1. Mouser still supplies 27 SKUs / 98 pieces for two boards; U5 must not be added to that hand-parts cart. The existing Rev G enclosure remains applicable through the full geometry-equivalence check; its original render provenance is retained, with a separate G.1 compatibility record.

## JLCPCB placement review

The revised BOM matched all six exact parts, including U5 C5218894. The user approved the catalogue rotation corrections, which were visually checked against the pads and pin-one markings and saved in the JLCPCB draft on 13 September 2026. Final JLC angles are U1/U5/U6 270°, U4 0°, and U2/L1 0°. All centres and PCB geometry remain unchanged.

`exports/CPL-FACTORY-JLCPCB.csv` now contains those JLC-specific angles, and the exporter preserves them. `exports/CPL-NATIVE-REFERENCE-ONLY.csv` and `placements-FACTORY.csv` retain native KiCad angles for independent reference and other suppliers. Do not apply the JLC offset a second time. `exports/FACTORY-PIN1-REFERENCE.csv` gives independent pad-one coordinates. See [the placement check](JLCPCB-PLACEMENT-CHECK.md) and `quotations/2026-09-13/rev-g1-status.json` for order preparation status. Final manufacturer placement approval remains required. [JLCPCB rotation convention](https://jlcpcb.com/help/article/pick-place-file-for-pcb-assembly), [catalogue orientation differences](https://jlcpcb.com/help/article/pcb-assembly-faqs-part-2).

Before manufacturing approval, obtain the assembler's decision on the U1/U2 exposed-pad thermal holes and stencil process. Before car use, perform the supply/transient/current, CAN, Wi-Fi and heater bench/vehicle tests in `DESIGN-REVIEW.md`. No powered validation or purchase is implied by the static checks.
