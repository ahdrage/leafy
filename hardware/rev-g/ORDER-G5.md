# Order Leafy G.5

This is the replacement design for a **new Standard PCBA order**. Do not reuse the G.4 cart/order. Check that the previous order cancellation/refund is resolved before paying for a replacement; no cancellation has been performed or verified by this file.

## Upload these three files

1. PCB: `deliverables/leafy-rev-g5-gerbers.zip`.
2. Assembly BOM: `exports/BOM-FACTORY-JLCPCB.csv`.
3. Placement: `exports/CPL-FACTORY-JLCPCB.csv`.

Attach `deliverables/leafy-rev-g5-factory-assembly.zip` as supporting engineering documentation if requested. It contains the fabrication notes and thermal-hole location drawing/CSV. Do not upload the hand BOM, full-reference BOM or native-angle CPL as the production BOM/CPL.

## Settings

| Setting | Selection |
| --- | --- |
| Finished single PCB | 100 × 100 mm, four layers |
| PCB quantity | 5 |
| Assembly type/quantity/side | Standard / 2 / Top |
| Material/thickness | FR-4 / 1.6 mm |
| Outer / inner copper | 1 oz / 1 oz |
| Mask / silk | Green / white |
| Surface finish | Lead-free HASL |
| Via covering | Epoxy Filled & Capped |
| Via plating method | Horizontal Electroless Copper Plating |
| Edge rails / fiducials | Added by JLCPCB; finished board outline unchanged |
| Depanel / remove rails before delivery | Yes |
| Special stencil | No |
| Programming / function test | No; assembly is incomplete |
| PCB production-file / parts-placement confirmation | Manual confirmation |
| Components | Exactly U1/U2/U4/U5/U6/L1 from the BOM |

Use normal JLC component handling/reflow/inspection. No custom stencil, extra paste printing, coating, functional testing or optional photo report is required. JLC's normal required charges may apply.

## PCB remark to paste

Leafy G.5: EPOXY FILL + PLANARIZE + COPPER CAP all thermal PTHs under U1 (6 x 0.33 mm) and U2 (12 x 0.30 mm), 18/PCB. Include 0.33 mm despite the default <=0.30 mm rule. See FABRICATION-NOTES.txt and THERMAL-FILL-LOCATIONS.csv. Top thermal pads have continuous mask openings; no mask tents. Bottom mask exposes copper caps, NOT open barrels. Preserve pad/copper/mask geometry and solid thermal connections. Component-lead/test/mounting holes remain open. 1 oz inner and outer copper. Manual production-file confirmation.

## Assembly remark to paste

Leafy G.5: STANDARD PCBA, fit ONLY U1/U2/U4/U5/U6/L1 TOP on 2 boards. Use supplied JLC CPL angles ONCE. Normal JLC component-library stencil engineering accepted; Special stencil=No. Paste Gerber is reference only; no fixed thickness/exact apertures, step stencil or paste on unpopulated parts. Solder U1 thermal pad; normal controlled U2 EPAD paste. Add temporary rails/fiducials and remove before delivery; preserve 100x100 mm finished outline. Manual placement confirmation. Do NOT power/program incomplete boards. ANT1 customer plug-in.

## Before payment / production

Check the new quote's total, exact six matched catalogue parts and orientations. Ensure the 0.33 mm holes are included in the filled/capped process through the explicit remark/map. Check the processed top mask has no tents and that JLC has preserved the finished outline. A normal library stencil is accepted; do not add an exact-stencil requirement again.

USD 21.06 was the estimated filling/plating surcharge for the prior discussion. It is not a complete Standard assembly quote. The old Economic price and shipping are historical. No new order or payment is created by this package. No Mouser changes are required.
