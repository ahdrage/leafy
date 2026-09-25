# Development history

This records engineering decisions and outcomes, not private conversations. Earlier documents retain their historical context and must not be used as G.5 manufacturing instructions.

| Stage | Change and reason |
| --- | --- |
| Research | Compared complete OVMS, 4G modules and custom approaches; established that the vehicle integration is more than a modem |
| Narrowed scope | Home Wi-Fi, climate On/Off only, because Wi-Fi reaches the parking location |
| A | Initial compact two-layer custom board with USB programming |
| B | Four-layer placement/plane/routing revision after layout review |
| C | Replaced USB-C/power with three-pin UART to reduce complexity/cost; separate programmer and supply required |
| D | 150 × 150 mm board, larger passives and accessible pads; four difficult parts factory fitted |
| E | 100 × 100 mm, more useful hand-solder spacing; corrected D1 purchasing code |
| F | Mouser-compatible CAN chip, DB9 and output capacitors; U3 pin 5 changed to ground for TCAN3404 |
| G | RC input damping, independent battery cutoff, powered-off ADC isolation, closer regulator components and different buttons |
| G.1 | Stocked TPS3760A012DYYR supervisor; documented the lost automotive qualification/earlier overvoltage allowance |
| G.2 | Routing and silkscreen cleanup after Adi's review |
| Firmware review | Fixed low-battery protection re-arming, bounded normal CAN retries and transceiver startup timing; expanded to 25 host tests |
| G.3 | External-antenna module, Molex antenna and enclosure cable exit/strain relief; GPIOs unchanged |
| G.4 | Explicit top-side mask tents and custom paste discussion to address thermal-hole solder wicking |
| G.5 | Epoxy-filled/planarized/copper-capped thermal holes, normal library stencil, Standard PCBA and Leafy branding |

## Manufacturing decisions

The final factory scope is **U1/U2/U4/U5/U6/L1**, with 49 other components per board hand-fitted. U3 and D4 still need careful soldering; this is not a through-hole-only beginner kit.

Selecting “Tented” in a quote did not by itself cover holes represented as through-hole pads. G.4 defined mask coverage explicitly, but the supplier could not guarantee the large one-sided tents and warned about ink entering the holes and solder wicking.

G.5 instead requires filling and copper capping **all 18 thermal holes: six 0.33 mm at U1, twelve 0.30 mm at U2**. The 0.33 mm exception must be explicit. Component, test and mounting holes stay open; solid thermal copper connections are intentional.

We removed the exact 0.125 mm stencil and exact-aperture requirements. G.5 accepts JLC's normal component-library stencil engineering, with Special stencil = No. The order uses Standard PCBA. Old tenting, mask-cap-survival and exact-stencil instructions are superseded.

## Review reached on 25 September 2026

Processed PCB artwork was compared with G.5: original drill locations, copper connectivity, continuous thermal-pad mask openings, all eighteen fill locations and temporary rails. The CAM record explicitly included the 0.33 mm holes. Finished size remains 100 × 100 mm after rail removal.

The final engineer-adjusted assembly viewer was reviewed separately. All six exact parts, centres and pin-one directions matched. A uniform +5 mm Y translation corresponds to the panel rail, not a relative placement error. The order specifies two partial assemblies out of five fabricated boards. The owner confirmed the PCB file; the assistant left final assembly approval to the owner after reviewing it.

This does not claim delivery, solder quality, first power-up, RF range or successful heater operation.

## Deferred work and constraints

No common-mode choke was added; this does not establish EMC performance. Low-battery protection takes precedence over Wi-Fi availability. G.5 preserves the already received Mouser part identities. Printed case fit, antenna performance and real supply/CAN/vehicle behavior remain to be tested.

Detailed G.1–G.5 change notes, earlier CAD and firmware review records are preserved. See [validation](VALIDATION.md) for the remaining physical work.
