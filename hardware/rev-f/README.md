> **Historical development record.** The current release is [Leafy G.5](../../README.md). Use this file for context, not current ordering or wiring instructions.

# Leaf Heat Rev F — Mouser parts revision

Rev F adapts the 100 × 100 mm, four-layer hand-solder prototype to the available Mouser parts. The only electrical connection changed from Rev E is **U3 pin 5, from 3V3 to GND**, because the replacement CAN chip uses that pin for shutdown. It retains the Wi-Fi controller, CAN standby control, vehicle and programming pinouts, protection components and hand-solder spacing.

| References | Rev F part | Change |
| --- | --- | --- |
| U3 | TI TCAN3404DRQ1 | Automotive CAN chip; SHDN tied low, STB still controlled by GPIO1 |
| J1 | NorComp 182-009-113R561 | Same PCB holes, with fitted 4-40 female screwlocks |
| C5, C6, C7 | KEMET C1210C226K3RAC7210 | Three 22 µF, 25 V, X7R, 10%, 1210 capacitors |

The factory still fits **U1, U2, U4 and L1**. The **37 remaining parts** are hand-soldered; they form **21 shopping lines / 74 individual pieces for two boards**, before spares. “All from Mouser” refers to this hand-parts shopping list; the four factory-fitted components remain in the PCB assembly order.

The [Mouser basket](MOUSER-SHOPPING.md) was updated and verified on 12 September 2026: all 74 hand parts are available, with a displayed merchandise subtotal of **347.53 NOK**, before delivery and any checkout tax. Nothing has been ordered.

## Open and order files

- [KiCad project](leaf-heat-v6.kicad_pro) — open this file, then the PCB or schematic from the project window.
- [PCB layout](leaf-heat-v6.kicad_pcb) and [schematic PDF](exports/schematic.pdf).
- [Hand-parts BOM](exports/BOM-HAND.csv) and [Mouser list for two boards](exports/MOUSER-HAND-TWO-BOARDS.csv).
- [Manufacturing notes](MANUFACTURING-NOTES.md), [design review](DESIGN-REVIEW.md), [hand assembly](HAND-ASSEMBLY.md), [programming](PROGRAMMING.md) and [vehicle wiring](VEHICLE-WIRING.md).
- [Gerbers](deliverables/leaf-heat-rev-f-gerbers.zip), [factory assembly package](deliverables/leaf-heat-rev-f-factory-assembly.zip) and [complete KiCad review package](deliverables/leaf-heat-rev-f-kicad-review.zip).
- [3D preview](exports/board-3d.png), [assembly map](exports/assembly-map.png), [ground plane](exports/ground.png), [power plane](exports/power.png) and [close-up of the CAN change](exports/can-change.png).

Use **Rev F Gerbers and Rev F BOM together**. Old Rev E/JLCPCB/PCBWay saved quotations still contain the previous board files and are not current manufacturing instructions. The two CAN chips are not interchangeable between these two revisions without a wiring change.

Native KiCad electrical, board connectivity and schematic-parity checks pass. Independent checks confirm the intended pin change, preserved unrelated copper, matching part lists and factory-only stencil. This is a verified CAD revision of an **untested prototype**: no heater firmware is supplied, and power, RF, CAN and vehicle operation require the bench/vehicle tests in the guides. A zero CAD report does not establish physical operation.

Rev E is preserved in the adjacent [archive](../rev-e/README.md). Nothing has been purchased or submitted for manufacturing by this revision task.
