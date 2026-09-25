> **Historical development record.** The current release is [Leafy G.5](../../README.md). Use this file for context, not current ordering or wiring instructions.

# Leaf Heat — Rev B

**Current engineering design. Four layers, 65 × 50 mm, 47 components. Not yet released for manufacture or vehicle installation.**

Open [leaf-heat-v2.kicad_pro](leaf-heat-v2.kicad_pro) in KiCad 10, then open PCB Editor. This revision replaces the two-layer Rev A layout. The circuit and heater-control purpose are unchanged; USB nets have been renamed to identify the differential pairs.

The board receives a command over home Wi-Fi and communicates with the Leaf through CAN. It does not carry heater power. Firmware, an enclosure and a tested Nissan ZE0 cable are still required.

## See the copper

Select **In1.Cu** in the PCB Editor's Layers panel and use **Show filled areas in zones**. Press **B** to refill after edits. That layer is the ground reference; there are no routed tracks on it. Copper is intentionally absent below the antenna and around non-ground holes/vias.

- [Top copper and components](exports/top.png)
- [Dedicated ground layer](exports/ground.png)
- [Internal power layer](exports/power.png)
- [Bottom copper](exports/bottom.png)
- [Component placement drawing](exports/placement.png)

## What changed

- Ground now has a dedicated internal layer plus connected surface copper. There are 87 separate ground vias, in addition to the thermal holes incorporated into footprints.
- Supply distribution uses copper areas and the internal power layer. Short, deliberately sized tracks still connect local parts.
- The regulator's bypass, bootstrap, local supply and feedback components have been regrouped. The feedback sense route comes from the output capacitor bank and stays away from the switching node.
- USB uses a parallel pair, short protection-device connections and resistors close to the controller. Both main copper paths measure approximately 40.991 mm. The main connector-to-controller paths have no vias; the USB-C duplicated-contact bridges have four local data vias and nearby ground return vias.
- Trace widths are selected by purpose. Making every trace the same width would make this design worse.

Read the [point-by-point review](LAYOUT-REVIEW.md) for the evidence and remaining limitations.

## Verification

KiCad 10.0.6 reports **0 electrical-rule violations, 0 layout-rule violations, 0 unconnected items and 0 schematic mismatches**. No DRC exclusions were added. The separate geometry audit confirms ground beneath the main USB route, matched copper lengths, main-pair spacing and no routed tracks on either internal layer.

The USB target is **90 Ω differential ±10%**. The proposed 0.25 mm traces and 0.15 mm gap calculate to **95.62 Ω in KiCad's uncoated coupled-microstrip model**. The actual solder mask, etched copper and factory stackup must be checked by the manufacturer before production. This is not measured impedance.

## Files for review

The native project, schematic, board, `.kicad_dru`, local symbols and local footprints must stay together. [BOM](exports/BOM-PCBWay.csv) and [placement coordinates](exports/placements.csv) are updated for Rev B. `exports/fabrication-review/` contains all four copper layers and drill files. See [manufacturing notes](MANUFACTURING-NOTES.md).

The existing PCBWay price was for Rev A. **It is not a price for this four-layer board.** Ordering remains paused while the design is reviewed. A four-layer board can cost more; it adds no components or wiring to the finished box.

This review does not demonstrate USB operation, power stability, parked-battery consumption, automotive transient immunity or successful heater control. Those require an assembled prototype and the bench/vehicle checks in [LAYOUT-REVIEW.md](LAYOUT-REVIEW.md). The earlier development-board plan uses different pin assignments.

## Custom-board firmware connections

| Signal | ESP32-C3 GPIO | Notes |
|---|---:|---|
| CAN TX / RX | 4 / 5 | Internal TWAI controller; intended Leaf profile 500 kbit/s |
| CAN standby | 1 | High = standby, pulled high by R10 |
| Battery sense | 0 | ADC; VPWR × 47/1047, measured after input diode |
| USB presence | 3 | ADC; half VBUS, use hysteresis |
| Status LED | 7 | High lights LED |
| USB D− / D+ | 18 / 19 | Native programming interface |
| Boot straps | 2, 8, 9 | Pulled high; BOOT button pulls GPIO9 low |

Start firmware with CAN in standby. Do not replay a heat request after reset. Implement a stop deadline, bus-error handling and a tested low-battery sleep policy. There is no independent hardware battery cutoff. USB and vehicle grounds are common; disconnect the vehicle during initial bench programming.
