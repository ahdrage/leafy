# Rev B — manufacturer engineering review

This supersedes the Rev A two-layer layout. Quote/review only; **do not fabricate before stackup and assembly details are approved**.

- Four layers, 65 × 50 mm, nominal 1.6 mm FR-4, minimum 1 oz finished outer copper and 1 oz inner copper. Lead-free HASL, green solder mask, white silkscreen. No blind/buried vias.
- Layer order: F.Cu / In1.Cu GND / In2.Cu power+GND / B.Cu. Gerbers contain all four layers. Do not substitute a two-layer build.
- Minimum routed trace is 0.20 mm. Nominal closest differential track gap is 0.15 mm. Standard vias: 0.65 mm land / 0.30 mm drill. Check the supplied drill table for footprint-specific holes and slots.
- Review for one assembled board; BOM 47 components, 29 MPNs, 46 surface-mount components plus one through-hole DB9. Other bare-board quantity is a quoting choice.

## Stackup and USB

Required differential impedance: **90 Ω ±10%** on the long F.Cu USB pair above In1.Cu GND. Proposed trace width 0.25 mm; edge spacing 0.15 mm. Copper pours are kept clear of the long pair. Local connector/component fanouts differ.

Starting material proposal from PCBWay's published regular 4-layer, 1.6 mm, 70% inner-copper stack: 0.1855 mm laminated 7628 RC46 prepreg (Er 4.74) above/below a 1.030 mm dielectric core (Er 4.6); four 0.035 mm copper layers. These published dielectric/copper values total 1.541 mm. The CAD model assumes 0.020 mm mask per side, so its modeled thickness is 1.581 mm; the procurement class remains nominal 1.6 mm. Mask properties and finished dimensions are assumptions to be replaced by the factory's actual proposal, not an approved custom stackup.

KiCad's uncoated coupled-microstrip calculation gives 95.62 Ω at 100 MHz. Confirm with the actual pressed dielectric, etched trace profile, finish and solder mask. Supply the proposed stackup and any required width/gap adjustment for approval before fabrication. Do not treat this calculation as measured or controlled production impedance.

## Assembly and mechanical details

Use BOM MPNs; flag unavailable parts before substitution. All components mount on the top. Coordinate origin for Gerbers, drilling and placement is the lower-left board origin. J1's library origin is signal pin 1, **not its body centroid**; the assembler must interpret its placement accordingly.

Review the exposed-pad regulator and ESP32 module land/paste patterns, thermal-hole treatment, solder wicking, and assembly support around the overhanging antenna and DB9 connector. The two connectors extend outside the rectangular board. J1's 3D body model is approximate; use its exact manufacturer drawing for mating/enclosure checks. H3 moved to board coordinates (46,32) mm in this revision.

For the automotive cable, at the board's male DB9: pin 9 = +12 V, pin 3 = GND, pin 7 = CAN-H, pin 2 = CAN-L; shell = GND. Use the specified Nissan ZE0 OVMS cable, not a generic OBD-to-DB9 lead. No bus termination is fitted. These are cable-review details, not factory functional-test instructions.

No firmware, credentials, vehicle identifiers or customer address are in this review package. No manufacturing order has been placed for Rev B.
