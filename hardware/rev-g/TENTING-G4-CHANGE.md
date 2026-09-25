# G.4: component-side thermal-hole tents and controlled paste

G.4 supersedes G.3 for manufacturing. This is a **fabrication/assembly process revision**, retaining every electrical pad, trace, via, drill, connection, component MPN, placement and case interface. The factory still fits U1/U2/U4/U5/U6/L1 on two boards. Mouser quantities and all hand parts are unchanged.

The original G.3 project, outputs and quotation records are preserved in `history/rev-g3-before-tenting.zip`. Do not order the old G.3/Y9 fabrication entry as G.4. The schematic and BOM footprint identifiers now point to the two G.4 local footprints.

## Implemented geometry

Both thermal-hole groups remain unfilled plated through holes. **TOP / component-side mask covers the holes; the bottom ends remain open.** No epoxy filling, copper cap or bottom-only tenting is claimed. The drawings are positive solder-mask openings: the covered hole regions are absent from the exported top mask. A general website “Tented” choice cannot substitute for this geometry.

| Feature | U1, LMR36510ADDAR | U2, ESP32-C3-WROOM-02U-N4 |
| --- | --- | --- |
| Existing holes retained | Six, nominal 0.33 mm | Twelve, nominal 0.30 mm |
| Top mask cap | 0.65 mm square; outer rows connect to pad-edge mask | 0.62 mm diameter; circular polygons, outer caps connect to edge mask |
| Nominal radial hole-edge coverage | 0.160 mm minimum | About 0.1596 mm minimum |
| Overall thermal mask envelope | 2.71 × 3.40 mm | 2.70 × 2.70 mm within existing 2.90 mm copper |
| Top paste | Two 2.71 × 1.55 mm openings, 0.30 mm central web | Nine 0.60 × 0.60 mm openings on existing 1.10 mm pitch |
| Nominal stencil thickness requested | 0.125 mm | 0.125 mm |
| Geometric paste area / wet volume | 8.401 mm² / 1.0501 mm³ | 3.240 mm² / 0.4050 mm³ |

The U1 mask keeps 6.484 mm² exposed within the 9.214 mm² envelope (70.37%). The U2 round caps avoid the narrow diagonal mask connections that square caps would create on its staggered grid. Actual areas and hole coverage are measured from the final plotted Gerbers in `exports/tenting-g4-audit.json`, not inferred from a viewer checkbox.

U1 follows the current DDA0008B mask envelope. Its two stencil windows deliver 91.18% of the nominal paste volume of TI's single 2.71 × 3.40 mm opening at 0.125 mm thickness, allowing a central release/venting web. Some paste deliberately prints over the mask tents and should coalesce onto adjacent exposed copper during reflow. **The tents must survive processing.** These dimensions are an engineering proposal requiring assembler acceptance, not a claim that JLCPCB has approved the process.

U2's central paste drops from nine 0.70 mm squares to nine 0.60 mm squares to suit the reduced exposed area and avoid lifting the module. The eighteen perimeter pads and their paste are unchanged. Espressif permits the central EPAD to remain unsoldered; when it is soldered, paste volume must not compromise the outer joints. G.4 retains central soldering and thermal copper, but its actual thermal performance and joint quality still require inspection/testing.

Do not assume a website quote's default stencil thickness matches this design. Ask JLCPCB to confirm **0.125 mm**, or provide its proposed thickness, final apertures and resulting paste volume for review. At 0.125 mm, the thermal-aperture area ratios exceed 0.66; this does not prove transfer efficiency. No automatic blanket stencil enlargement, merged thermal apertures, or mask enlargement is authorized.

## Required supplier response before production approval

1. Confirm that the supplied **solder-mask-defined** U1/U2 geometry will be preserved, including every top-side tent. Do not convert the thermal PTHs into exposed component holes or apply a global via rule that overrides the plots.
2. Confirm mask registration, finished-hole dimensions and survival of the 0.30/0.33 mm hole tents through HASL/reflow. Nominal artwork allows over 0.076 mm radial coverage even with +0.13 mm hole diameter, considered separately; the factory must evaluate its combined drilling/registration process tolerances.
3. Confirm stencil thickness, U1/U2 aperture patterns, transfer/reflow process and exposed-pad inspection. Review U1 solder coverage/voiding and all U2 perimeter joints. If this process is unavailable, propose the required change and extra cost **before** production.
4. Return processed PCB Gerbers and final placement/stencil data for customer approval. Disable automatic PCB/placement confirmation. Do not power or program the incomplete partial assembly.

## Verification and limits

- Fresh KiCad ERC and DRC include copper refill, all track errors and schematic parity under existing rules.
- Native geometry comparison checks all copper pads, tracks, planes, holes, outline and component locations against archived G.3.
- Independently parsed manufacturing plots verify all eighteen top hole covers, open bottom ends, mask areas and stencil apertures. Four copper Gerbers and both drill files match G.3 after header normalization.
- All 55 component MPNs, the six-part assembly scope, corrected JLC rotations, hand BOM and Mouser basket quantities remain unchanged.
- The G.3 enclosure/firmware remain compatible because mechanical and electrical geometry are unchanged. Existing enclosure renders retain their G.3 provenance.

Static verification cannot establish physical mask adhesion, solder joints, heat transfer, powered circuit behavior or vehicle qualification. This revision resolves the missing mask artwork; **supplier process acceptance and physical prototype tests remain**.

## Sources checked 15 September 2026

- [TI LMR36510 Rev B, package pages 38–39](https://www.ti.com/lit/ds/symlink/lmr36510.pdf): DDA0008B mask envelope, tent/fill/plug guidance and stencil-thickness examples.
- [TI PowerPAD SLMA002H, §2.4–3.1](https://www.ti.com/lit/an/slma002h/slma002h.pdf): component-side mask caps, via size, paste/assembly and inspection guidance.
- [Espressif ESP32-C3-WROOM-02/02U, §9](https://documentation.espressif.com/esp32-c3-wroom-02_datasheet_en.pdf): optional central EPAD soldering and excess-paste lifting risk.
- [JLCPCB via covering](https://jlcpcb.com/help/article/pcb-via-covering): via finish does not automatically apply to component PTH pads.
- [JLCPCB solder-mask-defined pads](https://jlcpcb.com/help/article/how-to-order-boards-with-solder-mask-defined-pads): explicit PCB remark and production-file review to prevent mask enlargement.
- [JLCPCB stencil process](https://jlcpcb.com/help/article/opening-process-standard-of-stencil): default aperture optimization and use of remarks for custom patterns.
