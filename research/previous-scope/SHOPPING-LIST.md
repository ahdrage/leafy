# Nissan Leaf box shopping list

**Recommended first build: assembled OVMS 4G, with GPS disabled and Wi-Fi retained for setup/recovery.** Prices checked 11 September 2026. Quantities are for one car. Listed GBP prices exclude VAT, delivery and installation.

## Core order

| Qty | Product | Price | Order condition |
| --- | --- | --- | --- |
| 1 | [OVMS v3.3 4G kit](https://shop.openenergymonitor.com/open-vehicle-monitoring-system-ovms-wifi-4g-sim-ant-included/) | £195.99 | In stock when checked; enclosure, modem, antennas and SIM included |
| 1 | [Nissan ZE0/e-NV200 cable](https://shop.openenergymonitor.com/nissan-ze0-e-nv200-obd2-ovms-cable/) | £9.94 | Applicable older Leaf only; select with kit OR buy separately |
| Instead of older cable | [ZE1 gateway harness](https://community.openenergymonitor.org/t/ovms-ze1-40kwh-64kwh-2018-nissan-leaf-can-tap-cable-available/29798?page=2) | Obtain quote | 2018+ ZE1: supplier announced a tested cable and batch order on 2 September; retail availability and any additional adapter unconfirmed |
| 1 if needed | Micro-USB data cable | Allow £3-8 | Reuse an existing data cable |
| 1 set | Mounting ties/pads, loom protection | Allow £5-15 | Local purchase; allowance, not quoted product price |
| As required | TCU isolation/activation materials | Vehicle-specific | Finalize after identifying model year and TCU |

Older-Leaf core subtotal: **£205.93**. With the two accessory allowances: **£213.93-228.93**, excluding shipping, taxes, labor and TCU work. No ZE1 total is given until the harness is priced.

For home-only connectivity, substitute the [Wi-Fi-only OVMS module](https://shop.openenergymonitor.com/wifi-only-open-vehicle-monitoring-system-ovms/) at **£159.99**. The older-Leaf core subtotal becomes **£169.93**. The car needs dependable internet-connected Wi-Fi where it parks.

Do not buy a separate modem, GPS module, CAN board, enclosure or new SIM for the assembled kit. Check the included SIM's account/profile before activation: [new Hologram self-service pricing](https://www.hologram.io/pricing/) is $1/month + $0.03/MB, but an included legacy SIM can have different rates.

## If we choose to develop our own electronics

This is a separate route, not an additional order for the assembled kit. **Prove the Leaf firmware adaptation before paying for custom PCB assembly.**

| Qty | Item | Purchase reference |
| --- | --- | --- |
| 1 | LILYGO T-Call A7670E H700 | [$26.52, exact LTE variant](https://lilygo.cc/products/t-call-v1-4?variant=43440642719925); confirm V1.0/V1.1 PCB revision |
| 1 assembled | Rev B OVMS carrier | [Production files and BOM](https://github.com/zbchristian/OVMS-Lilygo-based-Module/tree/70e1453b1129fc43690fc2d55066e0693363bb0d/eagle/JLCPCB); allow $40-100, subject to a real assembly quote |
| Included in assembly | 2 × TCAN330DR; 1 × MCP2515T-I/SO; 16 MHz crystal; LMR51610XDBVR supply and passives | Match [schematic](https://github.com/zbchristian/OVMS-Lilygo-based-Module/blob/70e1453b1129fc43690fc2d55066e0693363bb0d/eagle/schematic_revB.pdf); not separate purchases if assembled |
| 1 set | DB9 connector, headers and remaining top-side parts | Allow $10-25; published bottom-side BOM is incomplete for the whole assembly |
| 1 | Printed enclosure | Allow $10-25; use [project case files](https://github.com/zbchristian/OVMS-Lilygo-based-Module/tree/70e1453b1129fc43690fc2d55066e0693363bb0d) |
| 1 | Data SIM | $3 for a new Hologram SIM, or suitable existing SIM |
| 1 | Correct vehicle harness | Same model-year decision as above |

Development hardware allowance: **$89.52-179.52 before harness, delivery, taxes, tools and labor**. Minimum PCB order quantities may increase this. The carrier's README explicitly excludes Leaf support; sections 6-7 of the full report explain the required changes and electrical checks.

The lower-cost ZE1 Wi-Fi experiment and its separate parts are in section 8 of the [full research report](../../LEAF-BOX-RESEARCH.md). It needs software and power-management work before unattended use.

## Information needed to finalize the order

Record the car's model year, platform (ZE0/AZE0/ZE1), market/trim, battery size and original TCU. Confirm whether it must work away from home. Those answers determine the harness and whether the modem is necessary.
