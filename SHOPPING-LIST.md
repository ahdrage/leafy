> **Historical development record.** The current release is [Leafy G.5](README.md). Use this file for context, not current ordering or wiring instructions.

# Shopping list: homemade Leaf Wi-Fi heater control

**Selected build: 2015 Leaf, home Wi-Fi, Heat on / Heat off only.** This replaces the earlier OVMS-kit and 4G shopping list. One programmable development board plus a passive vehicle cable forms our own controller; no OVMS module is being purchased.

| Qty | Buy | Price checked 11 September 2026 |
| --- | --- | --- |
| 1 | [Waveshare ESP32-S3-RS485-CAN](https://www.waveshare.com/product/iot-communication/short-range-wireless/esp32-s3-rs485-can.htm), onboard-antenna version | $18.99-19.99 manufacturer listing across antenna options; allow $20. Includes enclosure, Wi-Fi, CAN and power conversion. Checkout stock not verified. |
| 1 | [Nissan ZE0/e-NV200 OBD-to-DB9 cable](https://shop.openenergymonitor.com/nissan-ze0-e-nv200-obd2-ovms-cable/) | £9.94 ex-VAT; listed in stock. Choose the Nissan-specific cable. |
| 1 | [DB9 male screw-terminal breakout, Adafruit 3123](https://www.adafruit.com/product/3123) or equivalent locally | $2.95; listed in stock. Includes connector housing. |
| 1 | Inline fuse holder with 1A fuse | Allow $3-6 equivalent locally; confirm against startup draw/wire rating. |
| 1 set | Short stranded wires, heat-shrink, mounting ties/pads | Allow $3-7 equivalent locally. Keep the CAN pair twisted. |
| 0-1 | USB-C data cable | Reuse one, or allow $3-6. |

**Published core subtotal: $21.94-22.94 + £9.94.** With accessories: **$30.94-41.94 + £9.94**, excluding freight, taxes, tools and labor. Allow approximately $45-60 equivalent for the hardware; this is not a delivered-price quote. Consolidate the small parts locally where possible to avoid separate shipping charges.

No separate ESP32, CAN transceiver, MCP2515 board, power converter or main enclosure is needed with this board. Its unused RS485 interface stays unused.

## Wiring reference

For the specific Nissan cable above, connect its DB9 breakout terminals as follows:

| DB9 terminal | Destination |
| --- | --- |
| 9 | Board power positive through fuse |
| 3 | Board power negative |
| 7 | Board CAN H |
| 2 | Board CAN L |

These correspond to OBD pins 16, 4, 13 and 12 respectively, per the cable supplier's mapping. Continuity-test with the cable unplugged. Leave CAN termination disconnected. **Unplug the car cable before USB programming:** [Waveshare warns against powering from USB and the terminal block together](https://www.waveshare.com/wiki/ESP32-S3-RS485-CAN).

The initial 2013-2015 climate profile needs the original TCU unplugged if fitted. Check the actual TCU/build generation before enabling commands; registration year alone does not resolve late-year model changes. A later TCU would change the CAN pair and protocol, not the board order.

See the [current build and firmware plan](LEAF-HEAT-WIFI-PLAN.md) for the sequence, local web controls and parked-power tests. Hardware and firmware are not yet tested on the car.
