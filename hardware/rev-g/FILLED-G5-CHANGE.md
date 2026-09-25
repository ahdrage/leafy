# Leafy G.5 — filled thermal holes and simpler assembly instructions

G.5 replaces the unfilled, top-tented U1/U2 thermal-hole process with epoxy fill, planarization and copper capping. The product name printed on the PCB is now **Leafy**. The preserved input is `history/rev-g4-before-filled-g5.zip`, with a per-file SHA-256 baseline manifest.

## What changes

- Remove the small solder-mask tents and their fragmented mask polygons under U1/U2. Use one continuous top mask opening: U1 2.71 × 3.40 mm and U2 2.70 × 2.70 mm.
- Require all six 0.33 mm U1 holes and twelve 0.30 mm U2 holes to be epoxy-filled and copper-capped. The unchanged drill artwork is accompanied by a coordinate CSV and location drawing. Merely selecting the global filling option is insufficient for U1's 0.33 mm holes and thermal PTH-pad classification.
- Retain the bottom mask artwork; those openings expose the finished capped annuli. They no longer mean physically open holes.
- Use Standard assembly and JLC's normal stencil engineering. Retain native paste as a reference, without requiring its exact apertures or a fixed stencil thickness. Select Special stencil = No.
- Replace the printed LEAF HEAT name with Leafy and revision G.5. Update native titles and U1/U2 footprint identifiers to identify the process.

## What remains compatible

All 55 component MPNs/values, 49 hand-fitted parts, six factory-fitted parts, antennas, pin nets, copper geometry, drills, solid thermal connections, connector positions, mounting holes and finished outline are unchanged from G.4. The hand BOM, Mouser shopping files and JLC placement coordinates/angles remain unchanged. The user has received the Mouser parts; no additional parts are required for this revision. The compatibility audit checks the saved supplier quantities, not the physical delivered bags.

No firmware change or enclosure geometry change is required. Existing enclosure renders show earlier artwork and are not relabelled as G.5 renders. Native KiCad renderers still show drilled holes because physical resin fill/capping is a fabrication operation; the fabrication notes and hole map control that process.

## Verification

`audit_filled_g5.py` checks native copper/stackup/drill/mechanical equivalence, schematic net equivalence, all component identities, saved Mouser quantities, placement files and final Gerber mask geometry against the preserved baseline. It checks actual plotted top-mask openings over all 18 thermal holes. Four copper Gerbers, drill files, bottom mask and reference paste must be unchanged after header normalization. Fresh KiCad ERC and DRC include zone refill and schematic parity.

These are artwork/compatibility checks. Actual filling/capping, normal assembly process acceptance and prototype measurements remain fabrication/bench tasks. Do not manufacture the newly exposed thermal holes without filling/capping.

## Sources and supplier correspondence

- JLC email: epoxy fill requires Horizontal Electroless Copper Plating; estimated combined surcharge USD 21.06; default holes <= 0.30 mm, special sizes must be remarked.
- Swee's assembly review: Standard assembly recommended; JLC uses its component-library stencil process. The user chose a new Standard order with normal stencil engineering.
- [JLC via covering](https://jlcpcb.com/help/article/pcb-via-covering): filling/capping and thermal-hole identification.
- [JLC SMT stencil workflow](https://jlcpcb.com/help/article/smt-stencil-data-prepared-for-smt-orders): assembler-generated stencil data.
- [TI LMR36510 datasheet](https://www.ti.com/lit/ds/symlink/lmr36510.pdf): DDA pad/mask and assembly-site stencil guidance.
- [Espressif module datasheet](https://documentation.espressif.com/esp32-c3-wroom-02_datasheet_en.pdf): EPAD paste quantity must not compromise perimeter joints.
- [JLC rails/fiducials](https://jlcpcb.com/help/article/how-to-add-edge-rails-fiducials-for-pcb-assembly-order): temporary tooling for Standard assembly.
