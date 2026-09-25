> **Historical development record.** The current release is [Leafy G.5](../../README.md). Use this file for context, not current ordering or wiring instructions.

# Leaf Heat — Rev C

**Current custom-board revision: UART programming, 41 components, four layers, 65 × 50 mm. Engineering prototype; not physically tested.**

Open [leaf-heat-v3.kicad_pro](leaf-heat-v3.kicad_pro) in KiCad 10, then open PCB Editor or Schematic Editor. Rev B is preserved in `../rev-b/`.

The board receives heater commands over home Wi-Fi and communicates with the Leaf over CAN. It carries no heater current. Firmware, a verified vehicle cable, an enclosure, and prototype testing are still required.

## What changed

- Replaced USB-C programming with **J3, a three-pin serial programming header**. Pin 1 is ground, pin 2 receives data from the adapter, and pin 3 sends data to the adapter.
- Removed USB power input, USB voltage detection, CC resistors, USB data resistors and their unused wiring/copper.
- Retained ESD protection, repurposed for the UART lines. Added two 1 kΩ series resistors and a 10 kΩ receive-line pull-up. These resistor types already exist in the BOM.
- Retained RESET and BOOT buttons, the protected vehicle power input, the CAN circuit, the antenna clearance, the ground plane and the mounting-hole positions.
- **No controlled-impedance service is required for Rev C.** Use the standard four-layer construction described in [manufacturing notes](MANUFACTURING-NOTES.md).

There are **41 parts / 25 distinct MPNs**, compared with Rev B's 47 / 29. All components are on top: 39 SMT and two through-hole connectors. The connector must be included in factory assembly.

Programming now needs a **3.3 V logic USB-to-UART adapter and a separate 12 V bench supply**, connected through J1. J3 has no power pin. Follow the [programming instructions](PROGRAMMING.md); do not use a 5 V logic or RS-232 adapter.

## Verification and files

Native KiCad electrical and layout checks pass with zero reported violations, unconnected items and schematic/PCB mismatches. A separate saved-file audit checks the pin map, preserved circuit connections, copper net assignments, power tolerances and BOM/placement consistency. The [design review](DESIGN-REVIEW.md) records the scope, one documented KiCad check limitation and the remaining physical tests. Passing CAD checks does not establish a working or automotive-qualified product.

- [3D preview](exports/board-3d.png), [schematic](exports/schematic.png), [programming circuit](exports/programming-schematic.png)
- [Top copper](exports/top.png), [ground plane](exports/ground.png), [power distribution](exports/power.png), [bottom copper](exports/bottom.png), [assembly drawing](exports/placement.png)
- [PCBWay BOM](exports/BOM-PCBWay.csv), [JLCPCB BOM](exports/BOM-JLCPCB.csv), [placement coordinates](exports/placements.csv), [JLCPCB placement file](exports/CPL-JLCPCB.csv)
- [Electrical check](exports/erc.json), [layout check](exports/drc-final.json), [independent audit](exports/independent-audit.json), [manufacturing audit](exports/manufacturing-audit.json)

The native project, `.kicad_dru`, `Leaf.kicad_sym`, `Leaf.pretty/` and both library tables belong together. The Gerbers in `exports/fabrication/` are for Rev C only. Existing PCBWay/JLCPCB quotation requests contain **Rev B**, so their files and totals must not be treated as Rev C quotes.

## Firmware connections

| Function | ESP32-C3 GPIO | Behavior |
|---|---:|---|
| CAN transmit / receive | 4 / 5 | Internal TWAI controller |
| CAN standby | 1 | High = standby; external pull-up retained |
| Battery sense | 0 | ADC reads VPWR × 47/1047 after the input diode |
| Status LED | 7 | High lights LED |
| UART receive / transmit | 20 / 21 | Bootloader download and serial log |
| Reset / enable | EN | RESET button and 10 kΩ / 1 µF startup network |
| Boot straps | 2, 8, 9 | Pulled high; BOOT pulls GPIO9 low |
| Unused former USB pins | 3, 18, 19 | Explicit no-connect; no USB-presence detection |

Start with CAN in standby, require a fresh authenticated heat request after every reset, and implement a bounded heating interval, explicit stop handling, bus-error handling and low-battery behavior. Wi-Fi updates and recovery/rollback must be implemented in firmware; they are not provided by this hardware revision. The earlier development-board plan uses different GPIO assignments.
