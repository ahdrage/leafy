# Rev G.3 Mouser basket — verified 14 September 2026

G.5 compatibility: all component MPNs and quantities remain unchanged. The user has received the Mouser parts. Leafy branding and the new filled/capped PCB process require no Mouser changes. Existing basket backup and prices remain historical observations.

**The owner's Mouser Norway Chrome basket is complete: 35 product lines covering two Rev G.3 boards, 50 spare components and seven workshop products. Every requested quantity showed “Dispatches Now”; no duplicate products or backordered items remain. Nothing was ordered.**

| Cost | NOK |
| --- | ---: |
| Hand-fitted parts, antennas and 50 spares | 671.59 |
| Seven workshop products | 646.49 |
| Merchandise total | **1,318.08** |
| Selected UPS Worldwide Express Saver delivery | **0.00** |
| Displayed basket subtotal | **1,318.08** |

Checkout taxes were not calculated or verified. The delivery amount is the current basket estimate; the final checkout has not been completed. These prices exclude the PCBs and factory assembly. The baseline remains 49 hand-fitted parts and one plug-in antenna per board; the assembler separately supplies and fits U1/U2/U4/U5/U6/L1. The vehicle cable, enclosure/fasteners, cable ties, soldering iron, meter, magnification and bench power supply are separate. A UART programmer and the small soldering supplies listed below are now included.

## Saved files

- [Complete shopping CSV with spares and supplies](exports/MOUSER-CART-WITH-SUPPLIES.csv)
- [Verified quantities, spare allocations, prices and lifecycle flags](exports/MOUSER-BASKET-WITH-SUPPLIES-VERIFIED-2026-09-14.csv)
- Mouser's original Excel export for the complete basket (private supplier record omitted)
- [Machine-readable comparison and verification record](exports/MOUSER-CART-WITH-SUPPLIES-VERIFICATION-2026-09-14.json)
- [Complete quick-order text for rebuilding an empty basket](exports/MOUSER-QUICK-ORDER-WITH-SUPPLIES.txt)
- [Required board parts and antennas only](exports/MOUSER-TWO-BOARDS.csv)
- [Added spare/supply quantities only — already included above](exports/MOUSER-CART-EXTRAS.csv)

The live Chrome basket was checked line by line. Its downloaded Excel export was independently compared with the required board quantities in `MOUSER-TWO-BOARDS.csv`, `parts.json` and `accessories.json`, plus the explicit spare/supply additions. All 35 exact Mouser SKUs, manufacturer MPNs and quantities agree. There are 157 supplier order units: 100 baseline board parts/antennas, 50 spare components and seven workshop units. A pack or reel counts as one supplier unit; this is not a count of individual wires or clips. Availability was verified separately in the live basket because the Excel export does not contain stock status. The old connector/CAN-chip customer labels now say Rev G.

The backordered untaped capacitor and the obsolete Omron buttons were removed in the earlier board-parts update. C15 remains the specified **EEU-FR1J470H** taped straight-lead version, now quantity four including two spares. The replacement C&K buttons, pulse-resistant R21, precision R22/R23 and remaining protection parts are present. No component substitution, PCB edit or manufacturing-package change was needed for the workshop/spare additions.

## Workshop supplies and spares

| Item | Mouser part number | Quantity | NOK |
| --- | --- | ---: | ---: |
| FTDI 3.3 V UART programming cable, USB-A | 895-TTL-232R-RPI | 1 | 214.05 |
| Chip Quik CQ4LF no-clean flux pen, 10 ml | 910-CQ4LF | 1 | 76.33 |
| Chip Quik fine straight ESD tweezers | 910-CQ-ESD-12 | 1 | 48.21 |
| Chemtronics 1.5 mm desoldering braid | 5878-80-2-5 | 1 | 69.19 |
| Chip Quik SAC305 lead-free solder, 0.5 mm, 1 oz (about 28 g) | 910-SMDSWLF.0201OZ | 1 | 110.15 |
| Adafruit female/female 150 mm jumper wires, pack of 20 | 485-1950 | 1 pack | 18.75 |
| Digilent mini-grabber clips with attached leads, pack of five | 424-240-137 | 1 pack | 109.81 |

The [FTDI cable](https://ftdichip.com/products/ttl-232r-rpi/) has 3.3 V logic and separate ground/TX/RX connectors. It does not power this board. Use the separately powered board and the J3 connections in the [programming instructions](../../firmware/leaf-heat/README.md). Its USB-A plug may need an adapter if the Mac has only USB-C ports; no adapter was added. The [solder datasheet](https://www.chipquik.com/datasheets/SMDSWLF.020%201OZ.pdf) specifies SAC305 alloy and a 2.2% no-clean flux core. The selected [grabber kit](https://digilent.com/shop/mini-grabber-test-clips-with-leads/) includes its leads.

The 50 spares are 46 resistors/capacitors, two F1 fuses, one U3 CAN transceiver and one D4 CAN protection device. They use exactly the already-specified component MPNs. The common 10 kΩ resistors and 100 nF capacitors have larger spare quantities. The allocation CSV records required and added quantities separately. No extra factory-supplied ICs, antenna or connector was added.

## Distributor lifecycle flags

Mouser's 14 September export marks **C1 / GRM32ER72A225KA35L as End of Life** and **D4 / PESD2CAN,215 as NRND (not recommended for new designs)**. Both required quantities were available at that check and remain the exact parts already reviewed for this prototype. These flags concern future sourcing; they do not change the ordered electrical specifications. Revisit their availability and active alternatives before a later production run. Other lifecycle fields were blank, which is not evidence of an “Active” classification.

## If the basket is lost

For an empty basket, enter all 35 part numbers and final quantities from the complete quick-order text or CSV. If a basket still exists, compare quantities before adding anything to avoid duplicates. Do not also import the extras-only list: its quantities are already included in the complete list. The original 28-product/100-piece board-only list and earlier 483.34 NOK supplier export remain preserved as history. Use cut tape/bulk quantities for the components; no full component reels or paid MouseReel service are needed. Stock and prices are a snapshot, so recheck when placing an order.

The historical JLCPCB quotation (private supplier record omitted) included the six factory parts. Use the [Leafy G.5 order guide](ORDER-G5.md) for the new Standard assembly order with filled and capped thermal holes. Its price and production-file approval must be obtained for the new order. The Mouser parts have already been received; this basket backup does not require another purchase.

Rev G.3 update: two Molex 1461530300 antennas (Mouser 538-146153-0300) added at 35.38 NOK each, 70.76 NOK total. All prior hand parts remain unchanged. U2 is factory-supplied by JLCPCB as ESP32-C3-WROOM-02U-N4/C2926676, so it is deliberately absent from this basket. The antenna needs no soldering or separate cable adapter. One small nylon cable tie per enclosure joins the existing list of mechanical supplies to obtain separately.
