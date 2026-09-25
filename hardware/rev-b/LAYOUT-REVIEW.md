# Layout review — 11 September 2026

Rev A was electrically connected, but that was not sufficient evidence of a good layout. The friend's comments identified real weaknesses. Rev B is a substantial layout revision; it should still be treated as an engineering prototype.

## Response to the feedback

| Feedback | Finding | Rev B response |
|---|---|---|
| “Power should be planes, not tracks” | Too absolute. Copper areas help distribution, but local current loops, sufficient width and sensible routing matter more than the label “plane.” Large copper on a switching node can increase noise. | Internal 3.3 V distribution; local supply copper; wide input routes; compact switching-node routing. Short local tracks remain intentionally. |
| “Ground should be a plane with vias” | Correct as a general strategy here. Rev A had filled ground on both sides, but signal routing cut through those areas. | A dedicated In1.Cu GND reference with no routed tracks; surface ground and 87 separate GND vias. Ordinary pads, via clearances, mounting holes and the antenna keepout remain. |
| “Component placement isn't optimal” | Correct. The regulator and USB placement deserved more deliberate work before routing. | Regrouped regulator capacitors and feedback parts, moved USB protection and resistors, repositioned CAN protection and one mounting hole. |
| “Many different trace widths is bad” | Different widths are normal when their electrical purpose differs. Unexplained narrow escapes were undesirable. | Declared 0.20, 0.25, 0.40, 0.50, 0.80 and 1.00 mm widths. Fine-pitch escapes, signals, local plane connections and supply paths have different needs. |
| “USB isn't differential” | Valid criticism of Rev A's routing. | Intentional pair geometry, matched lengths, a ground reference, close protection and series resistors. Factory impedance confirmation remains necessary. |
| “Where is the ground plane?” | It existed in Rev A; a screenshot with filled zones hidden can obscure it. Its continuity was the larger issue. | The [In1.Cu export](exports/ground.png) shows the dedicated plane directly. |

## Why four layers

For this arrangement of USB, a radio module and a switching supply, four layers provide a predictable adjacent reference plane without complicated surface routing. This is a layout decision, not a universal claim that two-layer boards cannot work. A well-designed two-layer variant is possible, but achieving the same routing/reference geometry would require another layout and a different USB stackup calculation. It is not the preferred revision for this review.

Espressif recommends a four-layer structure with a complete second-layer ground plane, parallel matched USB traces, 90 Ω differential impedance ±10%, and minimized layer changes. Its module guidance also favors an antenna overhang. These are the relevant module/base-board recommendations; bare-chip crystal/RF matching recommendations are not added as extra parts to this integrated module. [Espressif layout guidance](https://docs.espressif.com/projects/esp-hardware-design-guidelines/en/latest/esp32c3/pcb-layout-design.html).

| Layer | Purpose |
|---|---|
| F.Cu | All components, main USB route, local power circuitry and most signals |
| In1.Cu | GND reference; zero tracks |
| In2.Cu | 3.3 V distribution and GND; zero tracks |
| B.Cu | A few control routes, supply copper, ground and USB-C contact bridges |

The internal ground plane has holes and clearances, as every practical plane does. It is not split into separate analog/digital islands. No main USB track crosses a void in its adjacent reference plane.

## Power and placement

C2 now bypasses U1's VIN and GND with short local connections. C3 and C4 sit near VCC and BOOT/SW. R1/R2 sit beside feedback, with output sensing from C7. The inductor/output capacitor copper remains separate from the input bypass copper. Thermal-pad ground connections and vias are retained. C12 sits near the CAN transceiver supply; protection D4 lies between the car connector and transceiver.

These changes follow TI's emphasis on short bypass loops, nearby local capacitors, a compact switching node, quiet feedback routing, thermal vias and a ground layer. TI recommends four layers and preferably 2 oz outer copper; this proposal uses its permitted minimum of 1 oz outer copper to contain cost. Thermal and load behavior have not been measured. [LMR36510 datasheet, sections 8.3–8.5](https://www.ti.com/lit/ds/symlink/lmr36510.pdf).

The USBLC6 protection is oriented for direct channel routing close to USB-C. Its ground and VBUS connections are short. [ST USBLC6-2 datasheet](https://www.st.com/resource/en/datasheet/usblc6-2.pdf).

## USB geometry and impedance

The main pair runs on F.Cu above In1.Cu. Its long coupled sections use **0.25 mm width / 0.15 mm edge gap**. Fanouts at the USB-C connector, ESD device, series resistors and module necessarily change the local coupling. A copper-pour clearance corridor keeps nearby top-layer ground from crowding the long pair; ground remains beneath it. The short USB-C duplicated-pin bridges use 0.20 mm escapes on F/B layers, four data vias, and ground return vias nearby.

Copper route lengths, excluding the physical lengths inside components:

| Path | D+ | D− |
|---|---:|---:|
| Main connector contact to resistor | 37.937 mm | 37.937 mm |
| Resistor to module | 3.053 mm | 3.053 mm |
| Main total | 40.991 mm | 40.991 mm |

The less-than-0.001 mm mathematical difference is a CAD result, not manufacturing accuracy. A small offset at the ESD fanout compensates the difference introduced by the main pair's bends. Both mirrored-contact bridge routes also have matched total copper lengths. These are USB full-speed programming lines; package parasitics and the assembled interface still need testing.

KiCad 10.0.6 Calculator Tools → Coupled Microstrip Line, at 0.1 GHz, with Er=4.74, H=0.1855 mm, copper=0.035 mm, W=0.25 mm and S=0.15 mm gives **Zodd=47.8068 Ω and Zd=95.6222 Ω**. This is an uncoated model. Mask, actual etching, roughness and material tolerances are not validated. A simpler formula gave a materially different answer for an earlier geometry; that geometry was rejected. Inputs and results are recorded in [impedance-estimate.json](exports/impedance-estimate.json).

The prepreg/core proposal comes from [PCBWay's published stackups](https://www.pcbway.com/multi-layer-laminated-structure.html). PCBWay must confirm the final stack and the **90 Ω ±10%** requirement. Specifying “four layers, 1.6 mm” alone does not control impedance.

## What was checked

- Native ERC: zero violations. Native DRC with refill and schematic comparison: zero violations, zero unrouted connections, zero mismatches. No DRC exclusions.
- All main USB path centers and edges sampled at intervals of at most 0.05 mm: adjacent ground present throughout.
- 6,111 samples across all USB tracks: 264 absent-ground samples are confined to expected clearance holes around the four local data vias; no unexplained gaps.
- Long parallel pair sections measured independently from saved track coordinates: approximately 0.15 mm gap; main copper lengths matched within 0.1 mm.
- Both internal copper layers contain zero routed tracks. The antenna copper keepout is applied to all copper layers and sampled at the board edge.
- All component references are retained and the netlist matches the schematic. BOM remains 47 parts / 29 unique MPNs. Updated placement data and all four Gerber copper layers were generated.

Evidence: [DRC](exports/drc-final.json), [ERC](exports/erc.json), [geometry audit](exports/layout-audit.json).

The critical power and USB routes were laid out explicitly before routing remaining control signals. The control router was a tool, not the acceptance criterion. Native checks and inspection of the actual filled copper determined acceptance.

A deliberately incorrect global pair-gap rule was detected by KiCad. A spatially scoped pair-gap rule did not trigger in CLI probes, so it is not relied upon: the final global rule accommodates component fanouts and the independent geometric audit checks the long pair more tightly. Intermediate diagnostic copies are outside the review ZIP.

## Remaining engineering work

Before production release, obtain factory confirmation of the stackup/impedance, footprint and assembly review, particularly exposed-pad soldering and the DB9 mechanical fit. Reflow and thermal-via solder wicking need assembly-provider review. Tent settings alone do not guarantee a filled/capped via process.

Then test an assembled board: current-limited supply startup and load behavior, ripple during Wi-Fi transmission, regulator temperature, USB enumeration/programming in both connector orientations, CAN standby/communication and parked-current behavior. Vehicle use additionally needs verified cable continuity, the correct Leaf/TCU configuration, firmware stop behavior and observed heater operation. No physical board has yet been built or tested.

This revision addresses the layout criticism. It does not establish automotive certification, a working heater-control product or a universally optimal design.
