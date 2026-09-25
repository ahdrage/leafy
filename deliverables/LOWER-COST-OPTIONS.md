# Lower-cost Leaf heater box options

**Superseded by live quotations later on 12 September 2026:** the user requires a custom assembled PCB and has rejected the module route below. The manufacturer minimum batch has now been approved for quotations only. PCBWay files are submitted for review; JLCPCB's actual current-BOM quote has substantial part-loading fees and missing parts. Use the current custom-board comparison (private supplier record omitted), not the preliminary recommendation below.

Researched 12 September 2026. Scope: one or two assembled units, home Wi-Fi, heater on/off. Prices are USD unless marked otherwise. No orders or new requests for quotation were submitted during this research; the PCB design and its manufacturing requirements are unchanged.

## Recommendation

For our **own custom PCB**, JLCPCB Economic assembly is the strongest next candidate to quote for two assembled boards. Its lower setup charge is promising, but a complete component match and checkout quote are needed before calling it cheaper.

For the **lowest hardware cost and least soldering**, return to the original module-based approach: an assembled Waveshare ESP32-S3-RS485-CAN plus the correct Leaf cable and simple wiring. This avoids commissioning a PCB. It remains a development project requiring firmware and vehicle testing, not a ready-to-use Leaf accessory.

## Comparison

| Route | Finished quantity | Price evidence | What remains outside that price |
|---|---:|---|---|
| PCBWay, existing requirements | 1 assembled + 4 blank spares | Previous calculator estimate **$111.75** | Components, VAT/import costs, box and cable |
| PCBWay, without paid impedance-control service | 1 assembled + 4 blank spares | New calculator estimate **$60.16**, with slower Norway shipping and promotion | Same exclusions; also requires an intentional USB manufacturing decision |
| JLCPCB Economic | Minimum 2 assembled | **$8.18 setup**, plus other charges; complete total unknown | PCB fabrication, parts, stencil, component loading, assembly operations, shipping/tax |
| Elecrow | Advertises minimum 1 assembled | Project-specific quotation required | All project costs need pricing |
| Seeed Fusion | Minimum 1 assembled from minimum 5 blanks | Project-specific quotation required | All project costs need pricing |
| Waveshare assembled module | 1 | **$18.99–$19.99** for the module | Leaf cable, wiring/fuse, shipping/tax, firmware and testing |

Manufacturer minimum fabrication batches and the number assembled are different. Only one or two *finished* boards does not necessarily mean only one or two blanks are fabricated. PCBWay's five-board batch has not been approved or submitted.

## What drives PCBWay's price

I compared the same 65 × 50 mm, four-layer, 1.6 mm board in a separate anonymous calculator session. Both configurations used standard lead-free HASL, green mask, white silkscreen, 1 oz outer/inner copper, and normal manufacturing time. Switching off impedance control changed fabrication from **$81.36 to $31.16**, a **$50.20** difference.

The lower comparison then showed:

| Item | Amount |
|---|---:|
| Five blank PCBs | $31.16 |
| Assembly labour for one, promotional | $29.00 |
| PostNL shipping to Norway | $18.83 |
| Discount | −$18.83 |
| **Calculator total, excluding components** | **$60.16** |

The displayed shipping time was 11–33 business days. Promotions and shipping eligibility can change when the components are added. This is an online estimate, not a reviewed factory quotation. The $51.59 difference from the previous total includes both the fabrication reduction and a small net shipping reduction. [PCBWay calculator](https://www.pcbway.com/orderonline.aspx)

This is **not permission to manufacture the existing files without their requirements**. Rev B specifies a 90 Ω ±10% USB differential pair. Removing the service removes assurance of that controlled result. We would need to review the actual standard stackup and USB geometry, revise the procurement requirements deliberately, and test the resulting hardware. Alternatively, a future revision could remove USB and use an external serial programmer.

## JLCPCB: the best next custom-board quote

JLCPCB advertises two-board minimum prototype assembly and supports four-layer boards, small surface-mount parts and mixed assembly. Our general size and package classes appear compatible, subject to its actual design and component review. [Prototype assembly capabilities](https://jlcpcb.com/solutions/pcb-prototype-assembly)

Its current detailed fee table lists Economic setup at **$8.18**, stencil at **$1.53**, and loading at **$3.07 per distinct extended component**. There are additional placement, possible inspection and manual-soldering charges. Ten charged extended part types, for example, would add $30.70 before buying any parts; this is an illustration, not a count for our board. [Assembly pricing](https://jlcpcb.com/help/article/pcb-assembly-price)

Our BOM has 47 components across 29 manufacturer part numbers. Matching ordinary resistors and capacitors to suitable Basic or Preferred Extended catalog parts could avoid loading fees. Ratings, footprint, tolerance, temperature range and capacitor performance must still match. [Component categories and assembly FAQ](https://jlcpcb.com/help/article/pcb-assembly-faqs)

Three critical exact parts are listed for Economic and Standard assembly:

| Existing part | JLCPCB catalog entry |
|---|---|
| ESP32-C3-WROOM-02-N4 Wi-Fi module | [C2934560](https://jlcpcb.com/partdetail/ESP32-C3-WROOM-02-N4/C2934560) |
| LMR36510ADDAR power regulator | [C1858393](https://jlcpcb.com/partdetail/TexasInstruments-LMR36510ADDAR/C1858393) |
| TCAN3403DRQ1 CAN transceiver | [C31086109](https://jlcpcb.com/partdetail/TexasInstruments-TCAN3403DRQ1/C31086109) |

All three are listed as Extended. Catalog presence does not reserve stock or establish the final procurement price. The remaining BOM, especially the exact DB9 connector, still needs matching.

JLCPCB's published free impedance testing is **±20%**; precision testing is chargeable. That does **not** satisfy Rev B's **±10%** requirement by itself. A different manufacturer's stackup also requires a USB geometry review. [Standard laminated structures](https://jlcpcb.com/help/article/multi-layer-pcb-standard-laminated-structures)

## Other manufacturers

**Elecrow** advertises a one-piece PCBA minimum, turnkey sourcing and mixed surface-mount/through-hole assembly. Its full quotation includes PCB, stencil, parts and assembly, with flashing/testing if requested. It normally responds to an RFQ within about a working day. Its unconfigured $1 service listing is not a price for our assembled board. [Elecrow service](https://www.elecrow.com/maker/assembly/index), [capabilities and quotation details](https://static-cdn.elecrow.com/pcb-assembly.html)

**Seeed Fusion** permits one assembled board from a minimum five-board fabrication batch. Its FAQ advertises free PCBA shipping, but eligibility and our final component procurement costs must be verified in a real quote. It is a backup candidate, not a demonstrated saving yet. [Seeed ordering FAQ](https://support.seeed.cc/portal/en/kb/articles/seeed-fusion-pcb-assembly-service-quick-questions)

## Buying an assembled module instead

The Waveshare ESP32-S3-RS485-CAN is advertised at **$18.99–$19.99**, depending on antenna selection. It combines Wi-Fi, isolated CAN, a 7–36 V input supply, screw terminals and a case. The extra RS485 function can remain unused. [Manufacturer product page](https://www.waveshare.com/product/iot-communication/short-range-wireless/esp32-s3-rs485-can.htm)

Example additional hardware:

| Item | Price evidence |
|---|---|
| Correct Nissan ZE0 / e-NV200 OVMS cable | [£9.94 excluding VAT](https://shop.openenergymonitor.com/nissan-ze0-e-nv200-obd2-ovms-cable/) |
| Assembled male DB9 screw-terminal adapter | [$2.95](https://www.adafruit.com/product/3123) |
| Inline fuse, holder and short wires | $6–$13 planning allowance, not a supplier quote |

Allow roughly **$45–$60 for prototype hardware before shipping/tax**, including some allowance for small accessories. This is a budget estimate across currencies and suppliers, not a checkout total; separate shipping charges could be significant. Reuse a USB cable if available. The screw-terminal approach avoids fine-pitch soldering.

The advertised input-voltage range does not establish automotive transient qualification. Firmware, parked battery consumption and power robustness still need verification before permanent installation. Use the Leaf-specific EV-CAN wiring and do not add a CAN termination resistor to the car's existing bus. Both our custom board and this module route still require working heater-control software and vehicle tests.

## Changes worth considering only if we keep a custom PCB

1. First quote two units at JLCPCB with our existing circuit and suitable catalog parts. Avoid redesigning before knowing the real savings.
2. Keep the four-layer ground-plane layout and the power/CAN protection. They are not the first places to cut cost.
3. If USB remains a significant fabrication or assembly cost, consider a revision with a simple programming header instead. This requires a proper reset/boot and power arrangement.
4. If sourcing or assembling the DB9 is disproportionately expensive, price factory assembly of all small parts with only that large connector soldered locally. Compare the actual saving before choosing this compromise.

The immediate decision is therefore whether owning a custom PCB matters more than minimizing the price of the first working prototype. For custom fabrication, obtain a complete JLCPCB two-unit quote. For the cheapest prototype, develop and test around the assembled module.
