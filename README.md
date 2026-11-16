# Leafy — DIY Wi-Fi Climate Controller for Nissan Leaf

**A DIY Nissan Leaf climate On/Off controller for home Wi-Fi.**

Leafy combines a custom ESP32-C3 board, a local web page and a printable enclosure. It requests climate operation over CAN; it does not carry or switch heater power. The intended profile is the **2013–2015 Leaf EV-CAN implementation**, subject to checking the actual vehicle and TCU configuration.

**Status — 16 November 2026: Rev G.5 works in the car; the website now displays both dashboard and BMS battery percentages.** Supervised On/Off with charging connected and owner-reported Heat On without charging have succeeded. The latest dual-percentage firmware is flashed and receiving both signals; the owner confirmed the display looks good. Unplugged Off, heater regression on this latest image, automatic shutoff and long-term reliability still need testing. CAN transmission remains disabled in the public configuration template; the tested unit was explicitly enabled. See [today’s record](docs/WEBSITE-BATTERY-2026-11-16.md) and [validation status](docs/VALIDATION.md).

![Leafy G.5 PCB render](hardware/rev-g/exports/leafy-g5-3d.png)

## Start here

| Goal | Documentation |
| --- | --- |
| Understand the project | [How it works](docs/OVERVIEW.md) |
| Build one | [Build guide](docs/BUILD-GUIDE.md) |
| Understand the decisions | [Development history](docs/DEVELOPMENT-HISTORY.md) |
| Inspect the current circuit | [G.5 design](hardware/rev-g/README.md), [schematic PDF](hardware/rev-g/exports/schematic.pdf), [KiCad project](hardware/rev-g/leaf-heat-v7.kicad_pro) |
| Buy components | [Parts and costs](docs/PARTS-AND-COSTS.md) |
| Order the PCB / partial assembly | [G.5 order guide](hardware/rev-g/ORDER-G5.md) |
| Build or test firmware | [Firmware instructions](firmware/leaf-heat/README.md) |
| Run the iPhone app / use the API | [iOS app and simulator setup](ios/README.md), [local API server](server/README.md) |
| Print the case | [Blender and STL files](enclosure/rev-g-v2/README.md) |
| Check the evidence | [Validation status](docs/VALIDATION.md) |

Latest website update: [dashboard and BMS battery percentages, sample ages and Off-request countdown](docs/WEBSITE-BATTERY-2026-11-16.md). The owner has also reported successful Heat On without the charging cable; unplugged Off remains to be recorded. A native [iOS app](ios/README.md) has subsequently been built and exercised in the simulator against a fake car; physical iPhone/vehicle validation remains outstanding.

Earlier progress: [bench observations, firmware fixes and successful in-car On/Off test](docs/COMMISSIONING-2026-11-15.md). The tested unit omits D6, so it has 48 hand-fitted parts plus six factory-fitted parts; the full BOM still specifies 49 hand parts.

## Deliberately small scope

- **Heat on / Heat off** from a browser on the same home network.
- Optional local API bridge for an iOS app, with voltage and battery-SOC support. SOC reception is now demonstrated on the normal website; comparison, parked-current and new-image heater regression checks remain. The native app is simulator-tested; see [app setup and limits](ios/README.md).
- Wi-Fi only, external antenna, no SIM, subscription or cloud service.
- One CAN channel and the specified Nissan OVMS cable pinout.
- A 100 × 100 mm, four-layer PCB with generous hand-solder spacing.
- Factory assembly of **U1/U2/U4/U5/U6/L1**; **49 other components per board** are hand-soldered and the antenna plugs in.
- Independent low-battery cutoff, input damping and protected power/CAN interfaces.

Normal operation keeps Wi-Fi associated and retries after outages. **Battery protection cuts the board's power when voltage is too low**, so it becomes unreachable until the supply recovers. Availability also depends on the router and signal. Before battery sampling was installed, the bench supply displayed roughly 4–9 mA during connected operation. Current must be remeasured with the new receive windows; average/peak, shutdown and router-loss current and long-term reliability remain unqualified.

The commands request the vehicle's climate function, not a particular heater element or temperature setpoint. The page reports requests, not independently verified heating.

## Thanks to OVMS

Leafy was inspired by the [Open Vehicle Monitoring System (OVMS)](https://www.openvehicles.com/). Its Leaf wake-up/climate sequence and dashboard/BMS percentage decoding are **derived from the OVMS Nissan Leaf implementation**, pinned to revision `85074a0ae7a983b308c6e2e081185492527ee073`.

Thank you to the OVMS authors and contributors for making this work available. The original MIT notice is retained in [OVMS-NOTICE.txt](firmware/leaf-heat/OVMS-NOTICE.txt). [Credits and provenance](CREDITS.md) explain the relationship and other sources. Leafy is an independent prototype, with no claimed OVMS or Nissan endorsement.

## Repository map

- `hardware/rev-g/`: current G.5 CAD, BOMs, manufacturing files, reviews and audit tools. The internal filename `leaf-heat-v7` is intentional.
- `firmware/leaf-heat/`: ESP-IDF firmware, settings template, 48 host checks and an isolated real-browser regression.
- `enclosure/rev-g-v2/`: Blender source, STLs, renders and G.5 compatibility. Case renders retain their G.3 artwork provenance.
- `server/` and `ios/`: authenticated local API bridge, OpenAPI specification, native SwiftUI app, Xcode project and simulator fixture. No cloud deployment or physical iPhone validation yet.
- `docs/`: project history, construction, costs, validation and publication notes.
- Earlier revisions and research: development history, **not current manufacturing instructions**. Always use matching G.5 files.

The public snapshot excludes personal supplier records, credentials, configured firmware images, downloaded toolchains and unrelated projects. Originals remain local. See [publication scope](docs/PUBLICATION.md).

## Licences

See [LICENSE.md](LICENSE.md) for the project licence boundaries and retained third-party notices.
