> **Historical development record.** The current release is [Leafy G.5](../../README.md). Use this file for context, not current ordering or wiring instructions.

# Leaf Heat Rev D — 150 × 150 mm hand-solder prototype

Rev D is the large first-test version. Open `leaf-heat-v4.kicad_pro` in KiCad. Rev C remains preserved.

The factory fits **U1, U2, U4 and L1 only**. You fit the other **37 components**. Seven bare plated test holes are part of the PCB and require no purchased components. The incoming board is incomplete and must not be powered until hand assembly and inspection are complete.

## Why four factory parts?

| Reference | Part | Reason |
| --- | --- | --- |
| U1 | LMR36510ADDAR power regulator | Its underside thermal pad needs reflow soldering. |
| U2 | ESP32-C3-WROOM-02-N4 Wi-Fi module | Underside ground pad and many connections. |
| U4 | USBLC6-2SC6 UART protection | Six small, closely spaced leads. |
| L1 | SRN6045TA-220M inductor | Factory fit as requested; its termination access is less convenient with an iron. |

U3 is an eight-pin SOIC with visible leads and extended outer pads. D4 has three visible leads and a hand-solder footprint. These are the most demanding remaining parts; practice on spare parts first. The board still involves surface-mount soldering.

## Changes from Rev C

- Board enlarged from 65 × 50 mm to **150 × 150 mm**. Functional sections are separated for access.
- All 0603 resistors become **1206** with extended hand-solder pads. Resistance values and 1% tolerance are retained.
- Small capacitors become **1206 X7R**; the existing larger 1210 input/output capacitors keep their exact MPNs and receive extended pads. Capacitor voltage ratings are retained or increased.
- Status LED becomes 1206. Reset and boot buttons become Omron B3F-1000 through-hole switches.
- U3 receives wider exposed pad toes. D4 uses KiCad's hand-solder footprint.
- Hand-fitted parts use thermal-relief plane connections. The regulator and radio retain direct thermal-pad connections.
- Seven labelled bare test holes expose ground, incoming 12 V, protected input, 3.3 V, CAN-H, CAN-L and reset/enable.
- Factory paste apertures exist only for the four factory components. Hand-fitted parts are present electrically in the design but have no stencil apertures.

Four layers, ground reference, power distribution, input protection, CAN protection, GPIO assignments, UART programming and the lack of CAN termination are retained. There is no USB socket, cellular modem or controlled-impedance fabrication requirement. No extra common-mode choke is added.

The larger board may cost more to fabricate than Rev C. Fitting only four components should reduce assembly/sourcing work, but the total saving requires a new quote. A factory cannot functionally test this incomplete circuit as a finished product.

## Files

- `deliverables/leaf-heat-rev-d-gerbers.zip`: upload for the bare-PCB quotation.
- `deliverables/leaf-heat-rev-d-factory-assembly.zip`: factory-only BOMs, placements, fabrication files and instructions.
- `deliverables/leaf-heat-rev-d-kicad-review.zip`: editable KiCad project with local libraries and review documents.
- `deliverables/leaf-heat-rev-d-hand-assembly.zip`: hand shopping list, instructions and placement drawings.
- `deliverables/leaf-heat-rev-d-review-images.zip`: images to share with a reviewer.
- `HAND-ASSEMBLY.md`: tools, orientation and assembly/inspection sequence.
- `MANUFACTURING-NOTES.md`: exact partial-assembly scope.
- `PROGRAMMING.md`: 3.3 V UART and separate 12 V bench power.
- `DESIGN-REVIEW.md`: verified checks and physical-test limitations.
- `exports/`: factory-only purchasing/placement files, separate hand-parts list, drawings, Gerbers and reports.

Firmware and Wi-Fi updates have not been implemented. CAD checks do not demonstrate heater operation, automotive transient immunity, radio performance or parked battery consumption. Bench tests precede connecting this prototype to the car.
