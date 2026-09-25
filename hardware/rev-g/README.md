# Leafy — Rev G.5

**Current manufacturing revision: G.5.** The PCB now says **Leafy**. U1/U2 thermal holes require epoxy filling and copper capping, replacing G.4 mask tents. The new order uses Standard assembly and JLC normal stencil engineering. All components, wiring and mounting geometry remain compatible with the received Mouser parts.

Start with [the order guide](ORDER-G5.md), [change details](FILLED-G5-CHANGE.md), and [current packages](deliverables/README.md).

Rev G adds input damping and independent low-battery shutdown to the 100 × 100 mm, four-layer Wi-Fi/CAN board. It retains the hand-solder layout, Nissan DB9 cable interface and UART programming connector. **Rev F is preserved. This is a checked prototype design, not a vehicle-qualified product.**

- [Open in KiCad](leaf-heat-v7.kicad_pro), [schematic PDF](exports/schematic.pdf), [assembly image](exports/assembly-map.png)
- [Historical G.2 before/after images for Adi](review/leaf-heat-rev-g2-bilder-til-adi.zip)
- [Design review and remaining tests](DESIGN-REVIEW.md)
- [Factory instructions](MANUFACTURING-NOTES.md), [hand assembly](HAND-ASSEMBLY.md)
- [Exact hand-parts and antennas list for two boards](exports/MOUSER-TWO-BOARDS.csv), [verified basket and prices](MOUSER-SHOPPING.md)
- [Vehicle wiring](VEHICLE-WIRING.md), [firmware and programming](../../firmware/leaf-heat/README.md)
- [Updated Blender enclosure](../../enclosure/rev-g-v2/README.md)
- [Manufacturing/review packages](deliverables/README.md)
- [G.5 order guide](ORDER-G5.md), [complete order handoff](ORDER-HANDOFF-G5.json)

The factory now fits **U1, U2, U4, U5, U6 and L1**. U5 is the battery supervisor and U6 isolates the battery measurement when the 3.3 V supply is off; both have fine-pitch pins. You fit **49 other components per board**, using 27 different hand-parts products. The two-board shopping list contains 100 pieces: 98 soldered parts and two plug-in antennas, without spares. U3 and D4 still require careful hand soldering.

The important changes are:

- C15/R21 add a 47 µF / 63 V electrolytic capacitor with a separate 1 Ω damping resistor. The resistor is in the capacitor branch, not the board's main power path.
- U5 controls the regulator's enable pin independently of firmware. Nominal thresholds are approximately **11.67 V off / 12.68 V restart, measured after D1**, with nominal 1.27 s / 12.7 s delays. Actual thresholds and delays require measurement; see the review.
- U6 prevents the live battery divider from feeding an unpowered ESP32 ADC. The powered ADC conversion factor changes to **32.2766**.
- Regulator VCC and feedback routes shorten from 8.50 / 8.75 mm to 3.57 / 4.03 mm. Ground planes and antenna clearance are retained.
- The through-hole buttons change to C&K PTS645SL43-2 LFS, matching the contact geometry and 4.3 mm height.

The firmware is built around continuous Wi-Fi availability: station mode, modem sleep, automatic light sleep and unlimited reconnect attempts with a maximum 30-second retry interval. There is no intentional deep sleep or periodic offline schedule. Use the same non-isolated LAN and reserve the board's IP address in the router. **Low-battery cutoff necessarily makes the board unreachable until charging restores its supply.** Router outages, signal loss and firmware/hardware faults can also interrupt access.

Fresh ERC and DRC report zero errors, unconnected items or schematic mismatches under the configured rules. An independent script checks all 55 purchased components, critical pin connections, assembly ownership, unchanged cable/mount geometry and Rev F hashes. The firmware compiles, and its command/retry logic passes host tests. These checks do not establish real supply ripple, current consumption, RF performance or actual heater behavior.

The user has received the Mouser components. G.5 requires no changes to these parts or quantities; recorded basket exports remain available in the shopping notes. The first G.5 Standard order has reached PCB-file and final-placement review. See the public development history and cost record. Every future order still needs its own review. Before vehicle use, complete the documented bench plan and cable/TCU checks.

## Public project status

The G.5 PCB production files and final six-part assembly placement were reviewed on 25 September 2026. See the current [development history](../../docs/DEVELOPMENT-HISTORY.md) and [validation status](../../docs/VALIDATION.md); earlier order-preparation statements in this document are historical. Physical testing remains outstanding.
