# Rev E — partial factory assembly, quotation/prototype files

**100 × 100 mm. Use Rev E files only. Fit exactly U1, U2, U4 and L1 on the top.** All other component positions are intentionally left empty for the customer to hand solder. This is an incomplete engineering prototype; do not energize or claim functional test of the delivered partially assembled circuit.

Quote one and two partially assembled boards. A minimum of five blank boards is acceptable for a quotation. These files do not authorize purchase, paid procurement or manufacturing.

## PCB fabrication

- Four layers, nominal 1.6 mm FR-4, standard factory stack. No controlled impedance.
- Order: F.Cu components/local routing, In1.Cu GND reference, In2.Cu supply distribution, B.Cu signals and ground pour.
- 1 oz copper on all four layers, green solder mask, white silkscreen, lead-free HASL.
- Routed trace minimum 0.25 mm, design minimum copper clearance 0.20 mm. Use actual Gerbers and drill files as the authority.
- Ordinary through vias and plated thermal holes. No blind/buried vias.
- Hand-solder pads have thermal reliefs. Preserve them; do not change them all to direct plane connections.
- Seven 3 mm test pads with 1.5 mm plated holes are bare PCB features. Do not install components in them.
- Wi-Fi antenna and DB9 overhang the PCB. Respect antenna keepout on every copper layer. Do not put panel tabs, metal clamps or copper under the antenna.
- Native dielectric dimensions are nominal visualization values, not a custom laminate request.

## Factory assembly: four components only

| Ref | Manufacturer | Exact MPN |
| --- | --- | --- |
| U1 | Texas Instruments | LMR36510ADDAR |
| U2 | Espressif | ESP32-C3-WROOM-02-N4 |
| U4 | STMicroelectronics | USBLC6-2SC6 |
| L1 | Bourns | SRN6045TA-220M |

Use `BOM-FACTORY-PCBWay.csv` or `BOM-FACTORY-JLCPCB.csv` and the corresponding **factory-only** placement file. The full hand-parts shopping list and full circuit drawings are references, not additional assembly instructions. No substitutions or additional placements without review.

The top paste Gerber contains apertures only for these four parts. Do not regenerate paste for the hand-solder parts. Review U1/U2 exposed pads, stencil aperture coverage and thermal-hole solder wicking. Thermal holes are not specified as filled/capped; the radio's thermal holes have mask openings on both surfaces. Agree a suitable reflow/thermal-hole process and report any extra fabrication requirement/cost before manufacturing. Tenting alone must not be represented as filled vias.

All 37 remaining components, including J1, J3 and both switches, are customer-fitted. Do not buy or fit them as part of this factory assembly quote. Quote setup, stencil, four components, sourcing/MOQ/attrition, soldering, inspection and shipping/taxes separately. No firmware programming or finished-product functional test is included. Optical/X-ray inspection of the four fitted parts can still be quoted.

Placement/drill origin is the lower-left board corner (0,100 mm in KiCad). CSV X is right, Y is up. Rotations are KiCad values; review the vendor placement preview. The ESP32 and inductor geometry/orientation must be checked against the drawings. Do not automatically confirm placement.

The hand-parts value table is printed on the back. J1 has more body overhang than Rev D; its printed outline is clipped to the board edge, while its pads and physical footprint remain unchanged. The complete native project shows every final component for circuit and mechanical review. The generic DB9 3D model is approximate and is not an enclosure specification.
