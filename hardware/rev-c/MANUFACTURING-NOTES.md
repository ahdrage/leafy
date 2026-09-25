# Leaf Heat Rev C — quotation and prototype assembly

**Use Rev C files only. This is an untested engineering prototype, not a vehicle-qualified production release.**

Request prices for one and two fully assembled boards. A supplier's minimum batch of five blank boards is acceptable for quotations only. No purchase, paid procurement or manufacturing authorization accompanies these files.

## Fabrication

- Rectangular PCB: **65 × 50 mm**, four layers, nominal **1.6 mm FR-4**.
- Layer order: F.Cu / In1.Cu GND / In2.Cu 3.3 V + GND / B.Cu.
- **Standard factory stackup; controlled impedance: NO.** There are no USB data pairs or board-level RF feedlines. The Wi-Fi antenna and matching are inside the purchased module. The old Rev B 90 Ω ±10% USB requirement is superseded for this revision.
- Copper: **1 oz outer and 1 oz inner**, retained from Rev B. Do not substitute thinner inner copper without a separate design decision. Standard green mask, white silkscreen and lead-free HASL.
- No blind or buried vias. Standard signal/ground vias are 0.65 mm diameter with 0.30 mm drill. The drill report also contains package-specific 0.33 mm thermal holes and connector/mounting holes.
- Routed track minimum: 0.20 mm. Global minimum clearance: 0.15 mm; normal net-class clearance: 0.20 mm. Copper-to-board-edge minimum: 0.30 mm. Use the supplied design and drill files, not these summary numbers to reconstruct geometry.
- The CAD dielectric dimensions are nominal visualization values, **not a request for a custom laminate**. Preserve layer order and nominal overall thickness. Report any DFM adjustments before fabrication.

## Assembly

**Fit all 41 BOM components on the top: 39 SMT plus J1 and J3 through-hole connectors.** No DNP components are included. No hand soldering is expected from the customer. Three mechanical mounting holes have no purchased parts.

Use exact manufacturer part numbers. Report unavailable parts and proposed substitutions before purchasing them. JLCPCB catalogue IDs are intentionally blank until exact MPN matching is performed; do not reuse the old Rev B auto-matches or manufacture with missing components.

J1 is NorComp **182-009-113R531**, male DB9. J3 is Harwin **M20-9990346**, three contacts on 2.54 mm pitch, 0.64 mm square pins. J3's finished plated-hole nominal diameter is 1.00 mm. It uses ground thermal reliefs for soldering. Both connectors must be installed from the top.

U4 retains the part number **USBLC6-2SC6** but now protects **UART signals**. It is not a USB controller or a reason to quote impedance control. C14 is now **100 nF**, MPN GRM188R71C104KA01D; do not populate the old 1 µF part from Rev B.

Review exposed-pad soldering and solder wicking at the regulator and ESP32 module. Their footprint thermal holes are plated but not specified as filled/capped via-in-pad; normal tenting does not guarantee filling. Confirm an appropriate stencil/reflow process and report if extra processing is required. Do not silently add a costly via-fill process to the quote.

The radio antenna and DB9 body overhang the board. Keep the antenna area free of panel tabs, fixtures and conductive enclosure material; allow for overhang during assembly support. The DB9 3D model is approximate. Confirm mechanical dimensions with the exact part drawing before an enclosure is finalized.

## Coordinates and files

Gerber, drill and placement origin is the **lower-left board corner**. Placement X increases right; Y increases up. All rotation values come from the saved KiCad board.

**J1 and J3 footprint origins are at pin 1, not their body centroids.** Interpret these two placement rows using the assembly drawing and exact connector drawings. Component rotations and polarized parts must be reviewed in the manufacturer's placement preview before confirming assembly. The CSV is not a promise that every vendor's rotation convention will match automatically.

- `leaf-heat-rev-c-gerbers.zip`: four copper layers, mask, silkscreen, paste, outline and separate plated/non-plated drills.
- `BOM-PCBWay.csv` or `BOM-JLCPCB.csv`: exact purchasing list, 25 MPN groups / 41 placements.
- `placements.csv` or `CPL-JLCPCB.csv`: 41 component positions; mounting holes excluded.
- `placement.png`, `schematic.png`: assembly/circuit review drawings.
- `leaf-heat-v3-ipc2581.xml`: supplementary native manufacturing export, not a replacement for the agreed Gerber/BOM workflow.

No firmware, Wi-Fi credentials, customer address, vehicle identifiers or factory functional-test program is included. Quote assembly, all components, sourcing/MOQ/attrition, stencil/setup, both through-hole connectors, shipping to Norway, and taxes separately. A quote for bare PCBs or assembly labour alone is incomplete.
