# Leafy G.5 — current order files

Use this revision for the new JLC **Standard** order. The board name is Leafy. All received Mouser parts remain compatible; no new components are required.

Upload `leafy-rev-g5-gerbers.zip`, then the separate `BOM-FACTORY-JLCPCB.csv` and `CPL-FACTORY-JLCPCB.csv` from `../exports`. Exact settings and copyable remarks: [order guide](../ORDER-G5.md).

- **leafy-rev-g5-gerbers.zip**: four-layer fabrication data, drills, explicit 18-hole fill/cap map and notes.
- **leafy-rev-g5-factory-assembly.zip**: fabrication, six-part BOM/CPL, pin-one coordinates, drawings and normal-process assembly notes.
- **leafy-rev-g5-hand-assembly.zip**: unchanged hand BOM, received-parts shopping backup, assembly/wiring instructions.
- **leafy-rev-g5-kicad.zip**: editable native board/schematic/libraries and verification reports.
- **leafy-rev-g5-review-images.zip**: current schematic, board layers, assembly and thermal-hole map plus KiCad 3D render.

The factory fits U1/U2/U4/U5/U6/L1 on two of five boards. Select Epoxy Filled & Capped and Horizontal Electroless Copper Plating; explicitly include all six 0.33 mm U1 holes and twelve 0.30 mm U2 holes. Special stencil = No; JLC normal stencil engineering is accepted.

Package manifests verify every contained file. Artwork checks do not establish physical filling, solder joints or vehicle function. JLC must review the new order and process the specified holes. The old G.4 order is not the new release; cancellation/refund has not been verified. New Standard pricing and live placement review remain order-time steps.

All previous G.4 files/packages are preserved under `../history`. The internal native filename remains `leaf-heat-v7` for project/library continuity; its title and PCB silkscreen identify Leafy G.5.
