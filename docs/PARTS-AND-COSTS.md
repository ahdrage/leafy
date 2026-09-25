# Parts and prototype costs

Use exact MPNs and packages. Saved quantities can reconstruct a basket; stock and prices must be rechecked.

## Factory components

| Ref | Part | JLC code |
| --- | --- | --- |
| U1 | LMR36510ADDAR | C1858393 |
| U2 | ESP32-C3-WROOM-02U-N4 | C2926676 |
| U4 | USBLC6-2SC6 | C7519 |
| U5 | TPS3760A012DYYR | C5218894 |
| U6 | TMUX1511PWR | C2866750 |
| L1 | SRN6045TA-220M | C2044314 |

One of each is installed on each of two assembled boards. Larger procurement quantities may reflect minimum buys/attrition, not extra placements. These parts are not duplicated in the required Mouser hand-parts list.

## Hand-parts and equipment

- [Required two-board CSV](../hardware/rev-g/exports/MOUSER-TWO-BOARDS.csv): 27 hand-part product types plus antenna; 98 soldered parts and two antennas, **100 pieces total**.
- [Complete basket with supplies](../hardware/rev-g/exports/MOUSER-CART-WITH-SUPPLIES.csv): alternative complete import including spares/tools, not an additional list to add on top.
- [Extras breakdown](../hardware/rev-g/exports/MOUSER-CART-EXTRAS.csv).

The antenna is **Molex 1461530300**, flex type with 300 mm lead and matching MHF I / U.FL-class connector. Mount it outside the box on suitable plastic inside the car, away from metal. The entire lead includes the length routed within the case.

Also needed: correct Nissan OVMS cable, soldering iron, meter, current-limited bench supply, print material, four nylon M2.5 × 8 mm screws/nuts for the PCB, four M3 × 10 mm screws/nuts for the case, and a small nylon cable tie per case. The supplies basket includes 3.3 V UART cable, flux, tweezers, braid, solder wire, jumper wires and grabber leads.

## Historical costs

The G.5 order viewed on **25 September 2026** showed:

| Item | USD |
| --- | ---: |
| Five PCBs, specified filled/capped process | 76.50 |
| Two partial Standard assemblies, after displayed coupon | 53.95 |
| Rail removal | 2.32 |
| Merchandise | **132.77** |
| Shipping | 17.17 |
| Displayed duties/taxes | 37.03 |
| Total | **186.97** |

This buys **two partially assembled boards and three bare boards**, not complete devices. The earlier $185.45 view omitted the later rail-removal charge and its tax effect. The earlier $21.06 filling/plating estimate was a process surcharge, not a total quote.

The complete Mouser basket on **14 September 2026** showed 35 product lines, **NOK 1,318.08 merchandise**, with free shipping displayed. It included spares/workshop supplies; checkout tax was not verified in that record. A later saved basket check on 16 September showed NOK 1,305.08 for the same 35 product lines and free delivery, again without verified checkout tax. The owner later reported receiving the parts. This is neither today's price nor a verified final invoice.

Cable, print material, fasteners, bench equipment and currency conversion are not included in a combined kit price. Private receipts/account identifiers are omitted. Main savings came from Wi-Fi, UART, partial assembly and reducing the 150 × 150 mm trial board to 100 × 100 mm; the final exposed-pad process adds manufacturing cost.
