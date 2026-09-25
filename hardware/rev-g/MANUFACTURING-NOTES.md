# Leafy G.5 — fabrication and Standard partial assembly

Use only the matching `leafy-rev-g5` packages. Order **five PCBs and two Standard top-side assemblies**. The finished board remains 100 × 100 mm, four layers, 1.6 mm FR-4, 1 oz outer **and inner** copper, green mask, white silk, lead-free HASL.

## Fabrication

Select **Epoxy Filled & Capped** and **Horizontal Electroless Copper Plating**. The 18 mandatory filled/capped thermal holes are six 0.33 mm under U1 and twelve 0.30 mm under U2 on every PCB. U1's 0.33 mm holes must be included explicitly. The exported hole-location CSV and drawing identify them independently of KiCad's PTH-pad classification. Other eligible signal vias can follow JLC's normal fill process. All component-lead, connector, test and mounting holes must remain open.

Retain the plated barrels and solid ground connections; epoxy filling does not replace the conductive barrel. Both ends are capped; the top is a flat solderable pad. The bottom mask opening exposes a capped annulus, not an open barrel. Preserve the top solder-mask-defined pad boundaries (U1 2.71 × 3.40 mm; U2 2.70 × 2.70 mm). G.5 removes the G.4 local mask tents. No solder-mask cap survival requirement remains. Do not add thermal-relief spokes to the thermal pad/via heat paths.

## Assembly

Factory-fit exactly these parts; quantities are one each per assembled board:

| Ref | MPN | JLC/LCSC |
| --- | --- | --- |
| U1 | LMR36510ADDAR | C1858393 |
| U2 | ESP32-C3-WROOM-02U-N4 | C2926676 |
| U4 | USBLC6-2SC6 | C7519 |
| U5 | TPS3760A012DYYR | C5218894 |
| U6 | TMUX1511PWR | C2866750 |
| L1 | SRN6045TA-220M | C2044314 |

**Special stencil: No.** JLC's normal engineering process selects stencil thickness and apertures using its component library, the actual revised PCB pads and component assembly guidance. Native/exported paste is reference geometry only. There is no required 0.125 mm thickness, exact aperture pattern, user-specified stencil file, step stencil, or paste printing for the 49 unpopulated hand-fitted parts. U1's exposed thermal pad must be soldered. U2 paste volume must avoid lifting the module and compromising perimeter joints. Use normal JLC inspection; no special report is requested.

Use the exact BOM without substitutions. `CPL-FACTORY-JLCPCB.csv` already contains the catalogue rotation corrections: do not apply them twice. Verify the new order's six placements against the pin-one coordinate CSV and assembly drawing. A historical G.4 viewer check is not approval of the new order.

Choose JLC-added temporary assembly rails/fiducials and rail removal before delivery. The finished outline must remain 100 × 100 mm; component/connector locations and mounting holes are unchanged. Let JLC determine its panel tooling, preserving all finished-board clearances. Review the processed board and placement preview before release.

The customer solders the other 49 components per board and plugs in ANT1. Do not populate bare test/mounting holes, supply substitutes or power/program the incomplete assembly.

## Status

The files are prepared for a new Standard order. They do not prove physical hole filling, solder-joint quality or vehicle operation. The supplier performs fabrication/assembly review; bench testing follows hand assembly. Old order PRIVATE-RECORD-REMOVED cancellation/refund has not been verified here. Do not reuse the old G.4 order files.
