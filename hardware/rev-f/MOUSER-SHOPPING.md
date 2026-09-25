# Rev F — Mouser hand-solder shopping list

Use [MOUSER-HAND-TWO-BOARDS.csv](exports/MOUSER-HAND-TWO-BOARDS.csv) for **two boards: 21 product lines, 74 pieces, no spares**. The simple [quick-order text](exports/MOUSER-QUICK-ORDER-TWO-BOARDS.txt) contains `Mouser number|quantity`. This list covers all 37 hand-fitted PCB components per board. U1, U2, U4 and L1 are supplied and fitted by the assembly factory and are intentionally excluded. The vehicle cable, enclosure, programming adapter, tools and consumables are separate accessories, not included in this PCB-component list.

## Changes to the previous basket

| Remove old part | Add Rev F part | Mouser number | Quantity for two boards |
| --- | --- | --- | ---: |
| NorComp 182-009-113R531 | NorComp 182-009-113R561 | 636-182-009-113R561 | 2 |
| TI TCAN3403DRQ1 | TI TCAN3404DRQ1 | 595-TCAN3404DRQ1 | 2 |
| Murata GRM32ER71E226KE15L | KEMET C1210C226K3RAC7210 | 80-C1210C226K3R7210 | 6 |
| Previously absent D3 | Littelfuse SMBJ24CA | 576-SMBJ24CA | 2 |

The other 17 lines remain as listed in the CSV. The basket has now been updated; do not bulk-add the entire CSV again, because that would duplicate its existing items. Small surface-mount quantities use cut tape where shown, without a paid MouseReel service.

Live Mouser product pages inspected on 12 September 2026 showed stock of 157 TCAN3404 chips, 1,671 replacement connectors, 1,182 replacement capacitors and 10,842 SMBJ24CA diodes. The existing basket showed the required quantities of the other 17 lines as “Dispatches Now.” Stock is time-dependent and the site separately displayed an order-processing delay notice.

Sources: [CAN chip](https://no.mouser.com/en/ProductDetail/Texas-Instruments/TCAN3404DRQ1?qs=VVKQmw408U%252B21737r85FWg%3D%3D), [connector](https://eu.mouser.com/en/ProductDetail/NorComp/182-009-113R561?qs=q2eLhcXmQbik7hG6NHalhA%3D%3D), [capacitors](https://no.mouser.com/en/ProductDetail/KEMET/C1210C226K3RAC7210?qs=u4fy%2FsgLU9NvY46kfG%2F43g%3D%3D), [D3](https://no.mouser.com/en/ProductDetail/Littelfuse/SMBJ24CA?qs=JJML70Qc14u3Wc4gmMep1w%3D%3D), [basket](https://no.mouser.com/en/cart/).

## Verified basket — 12 September 2026, 22:38 Oslo

The basket in the user's Chrome profile contains exactly **21 matched lines / 74 pieces**, all showing the complete required quantity as **Dispatches Now**. There are no unmatched entries or backorders. Every catalog number, manufacturer part number and quantity was compared with the Rev F shopping CSV. See the [saved line-by-line basket record](exports/MOUSER-BASKET-VERIFIED-2026-09-12.csv).

| Displayed amount | NOK |
| --- | ---: |
| Components for two boards | **347.53** |
| Selected delivery, UPS Worldwide Express Saver | 280.00 |
| Basket subtotal with that delivery | 627.53 |

This is the basket's displayed merchandise/delivery subtotal, not a final tax-inclusive checkout quote. No tax line was shown or verified. PCB manufacture, the four factory-fitted parts, their assembly and accessories are separate. Nothing has been ordered. The basket is in the existing browser session; it has not been saved as a signed-in Mouser project.

These substitutions are specific to **Rev F**. In particular, its CAN pin-5 wiring differs from Rev E. See [DESIGN-REVIEW.md](DESIGN-REVIEW.md) for the datasheet checks and physical tests still required.
