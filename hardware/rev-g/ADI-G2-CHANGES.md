# Rev G.2 — Adi's layout review, 14 September 2026

Historical G.2 change record. Current manufacturing revision is **G.3**; see [external antenna update](ANTENNA-G3-CHANGE.md). The statements below describe G.2. This revision changes routing, two via positions and the silkscreen. Use the new `rev-g2` manufacturing ZIPs together. The saved G.1 JLCPCB quotation contains older fabrication data and must be replaced before ordering; adding an attachment alone does not replace its original Gerber upload.

## Changes

| Reviewed area | G.2 result |
| --- | --- |
| U1/C2 enable via | Verified connected on both layers. BUCK_EN copper is unchanged. C2's reference is moved clear of the crowded area. |
| C10/U2 3.3 V | Removed the redundant triangular route. The supply runs through C10's positive pad to U2 pin 1; existing power-plane vias remain. |
| R19 UART_RX via | Moved from (87.1531, 52.9642) to (89.45, 56.0) mm. Clearance to the adjacent PROG_TX trace increases from 0.2017 to 2.4986 mm. Both layers reconnect. |
| D4 CAN_H test-point via | Moved from (24.95, 82.5) to (26.5, 79.635) mm, directly on the existing CAN_H diagonal route. Clearance to D4's ground pad increases from 0.2406 to 2.0060 mm. The bottom route to TP5 is updated; no extra top-layer branch is introduced. |
| Silkscreen | All 141 visible texts are at least 1.0 mm high with at least 0.15 mm strokes. All 296 silk shapes use at least 0.15 mm strokes. Crowded component references, the LED cathode label and UART labels are repositioned. Both board faces and the schematic identify G.2; the schematic header now lists all six factory parts. |
| Manufacturing rules | Enforce 0.15 mm silkscreen clearance, 1.0 mm text height and 0.15 mm text stroke. Electrical clearance remains 0.20 mm. No new DRC exclusions. |

Dimensions are KiCad coordinates, X right / Y down. They are not CPL coordinates.

JLCPCB publishes the above legend minimums in its [rigid PCB capabilities](https://jlcpcb.com/capabilities/pcb-capabilities). The actual Gerbers subtract solder-mask openings from silkscreen, and the native DRC checks printing clearance before that clipping step.

## Verification

- Fresh copper refill and KiCad DRC with all track errors, all severities and schematic parity: zero violations, unconnected items or mismatches. ERC: zero violations.
- [Independent 55-component electrical audit](exports/independent-audit.json) and [G.1-to-G.2 comparison](exports/adi-g2-audit.json).
- All 66 footprint cores (55 purchased components, seven test points and four mounting holes), pads, models, circuit connections, board outline, zone definitions and antenna keepouts agree with G.1. Only the specified 3V3/UART_RX/CAN_H routes and two via positions change.
- Factory BOM, Mouser hand BOM, shopping quantities, all native placement coordinates and corrected JLCPCB CPL are unchanged. Six factory parts and 49 hand parts per board; two-board hand basket remains 27 SKUs / 98 pieces. No component substitution or new purchase is required.
- Gerbers, drill files, schematic drawings, assembly images and packages are regenerated from G.2. Package manifests identify and verify their source hashes.
- Existing enclosure geometry remains compatible because component/pad/model positions, outline and mounting holes are unchanged. Original renders retain their original provenance; moved copper/vias and silkscreen are not depicted in the older Blender reference.

The earlier silkscreen-check crash came from KiCad accessing macOS display services during a board commit. Running the local KiCad check with the required access completed successfully. No manufacturing rule was weakened to obtain a pass.

These are static checks. Assembler approval of U1/U2 exposed-pad/unfilled-hole soldering and powered supply, transient, parked-current, Wi-Fi, CAN and vehicle heater tests remain outstanding. No purchase or production approval has been made.

## Sources and reproduction

`history/rev-g1-before-adi-g2.zip` preserves the G.1 source, exports, documents and packages. `apply_adi_g2.py` is a one-time migration requiring that exact PCB hash; do not rerun it on G.2. `audit_adi_g2.py` compares against the archive. See `BUILD-REPRODUCTION.md` for validation/export order.
