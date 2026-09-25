> **Historical development record.** The current release is [Leafy G.5](README.md). Use this file for context, not current ordering or wiring instructions.

# A minimal connected box for the Nissan Leaf

**Earlier, broader research. The selected build is now a homemade Wi-Fi box for heating on/off only on the 2015 Leaf. Use the [current build plan](LEAF-HEAT-WIFI-PLAN.md) and [current shopping list](SHOPPING-LIST.md). The assembled-OVMS recommendation below has been superseded by that narrower scope.**

## 1. Recommendation

**For one box that works with the least engineering, use an assembled OVMS v3.3 module, the correct Leaf cable, and existing OVMS software. Choose its 4G version if remote access away from home matters. Use Wi-Fi for setup, then disable it during normal operation if desired.** This is the recommended first build. Designing a new circuit board reduces some component cost but adds firmware, power-supply, assembly, and vehicle testing work.

The first version should show battery percentage, charging state, cabin temperature when available, 12V battery voltage, and when the readings were last updated. Its controls should be heating/cooling on and off, plus start charging. Leave door locks, GPS tracking, cell-level charts, charge limits, and charge-stop automation outside the first acceptance test. This is a proposed minimum scope, rather than a claim that all OVMS features are reproduced.

The assembled 4G unit is currently listed at **£195.99 before tax**, including its modem, enclosure, cellular antenna, GPS antenna, and a Hologram SIM. A separate pre-2018 Leaf cable is **£9.94 before tax**. Together that is **£205.93 before shipping and import charges**. The Wi-Fi unit plus that cable totals **£169.93**, a saving of £36.00. Do not buy the cable twice if it is selected as a kit option.[^4][^5][^6]

| Route | Appropriate use | Main trade-off |
| --- | --- | --- |
| Assembled OVMS, 4G | Recommended for everyday access away from home | Small SIM bill; vehicle-specific installation |
| Assembled OVMS, Wi-Fi | Recommended if the parked car has dependable home Wi-Fi | Unreachable outside known Wi-Fi coverage |
| T-Call A7670E + custom carrier | Our own lower-cost 4G hardware | Existing design needs Leaf firmware adaptation and electrical validation |
| T-2CAN + Leaf-only firmware | Low-cost Wi-Fi experiment on a confirmed ZE1 | Smaller software, but less mature and incomplete protection against misuse |

**The key unresolved input is the car, not the radio:** model year, ZE0/AZE0 versus ZE1, market/trim, battery size, and original telematics unit. This report assumes a personal prototype in Norway and remote heating as a useful first feature. It gives conditional cable choices rather than guessing a vehicle pinout. Pricing and availability were checked on 11 September 2026; no hardware was ordered or tested on a car.

The documented system is Open Vehicles' OVMS3. Implementation findings refer to upstream revision `85074a0ae7a983b308c6e2e081185492527ee073`, dated 4 September 2026. That is a development revision; the first installation should use an appropriate released build.

## 2. What must be replicated

OVMS is a complete system: an embedded controller, vehicle-network interfaces, protected power input, connectivity, and software on both the device and phone/server. A cellular modem alone cannot perform the vehicle integration. The existing platform already includes mobile apps, a local web interface, and MQTT integration.[^3]

Source inspection confirms that the Leaf implementation opens **two independent CAN interfaces at 500 kbit/s**. It uses different wake-up paths for cars through 2012, 2013-2015, and 2016 onward. Remote commands go to different interfaces depending on that configuration. Commands are repeated through timers rather than sent as one arbitrary message. Charge stop modifies and retransmits battery message `0x1DB`; it is more involved than charge start.[^2]

That leads to a useful engineering rule: **reuse the Leaf behavior before reducing the surrounding software**. A bare ESP32, modem, and a generic OBD adapter are not a replacement for the existing wake-up and command handling. For broad OVMS Leaf behavior, keep both CAN channels. A one-channel device can be a valid narrower experiment for a particular car and connection point, but it is not equivalent to the full integration.

| First-version function | Required behavior we should test |
| --- | --- |
| Battery and charging display | Real values when available; explicit unknown/stale state when asleep |
| Cabin temperature | Show only an actual available reading; do not imply every trim supplies it |
| Heating/cooling on and off | Wake a parked car, send the correct sequence, and verify the resulting state |
| Start charging | Work with a connected, available charger and the car's timer conditions |
| 12V monitoring | Alert or shut down according to a tested parking power policy |
| Remote connection | Reconnect after power loss and network outages without replaying old commands |

For this scope we do not need a display on the box, a Raspberry Pi, an SD card, a second battery, a custom phone app, a new cloud database, or a 5G modem. Use the vehicle's existing temperature and battery data. GPS is unnecessary unless location tracking becomes a requirement.

Do not describe cached telemetry as live. Cellular availability only tells us that the box can communicate; it does not tell us the car's control units are awake. Our interface should separate the last received value, its timestamp, and the success or failure of a requested action. Avoid waking the car continuously just to make a dashboard appear current.

The upstream changelog records the initial ZE1 release in OVMS 3.3.005 on 18 July 2025. Use a current main-channel release appropriate to the hardware and car; identify and record the installed version during commissioning.[^19]

## 3. Installation depends on the Leaf generation

The following is the decision table from the Leaf integration guide. Its 2016 ranges overlap, so the actual TCU generation must resolve that boundary.[^1]

| Car | Connection and climate-control implications |
| --- | --- |
| 2011-2012 ZE0 | Leaf OBD cable; off-charge wake-up requires an additional switched 12V activation connection |
| 2013-2015 and applicable early 2016 | Leaf OBD cable; fitted original TCU normally disconnected for remote climate |
| Applicable 2016-2017 | Leaf OBD cable; isolate TCU CAN while preserving its other connections for the microphone |
| 2018+ ZE1 | Gateway tap behind instrument cluster; isolate original TCU CAN for climate. OBD alone is insufficient when parked |

Removing TCU CAN can produce persistent communication fault codes. Fitment must preserve the required microphone wiring and allow the original installation to be restored.[^1]

**A new cable may eliminate the hardest fabrication step.** OpenEnergyMonitor's first manufacturing attempt failed in May 2026. On **2 September 2026**, the supplier reported that a working cable had been tested, earlier problems resolved, and a batch ordered. This supersedes the older “no ETA” announcement. It is not proof that a retail cable is in stock today: the shop's visible kit options still did not offer a ZE1 tap cable.[^7][^4]

For a ZE1, obtain the supplier's exact cable specification, delivery estimate, and any required adapter before ordering a complete installation. If unavailable, fabricate the documented 24-pin male/female gateway interposer and DB9 connection. Budget this as a custom harness job. Keep every original gateway connection continuous and branch only the documented connections; do not use the new box as a bridge that the car depends on to communicate.

The published ZE1 wiring drawing uses eight conductors, including three CAN pairs and power/ground. Although the current Leaf software opens only two interfaces, this report does **not** replace that harness with a guessed six-wire loom. Retain the documented loom until the exact installation has been verified. Bus names also differ across projects, so identify connections by connector, pin, and function rather than assuming every “CAR-CAN” or “IT-CAN” label means the same physical pair.[^8][^2]

For an older Leaf, the seller's purpose-made cable connects the additional Leaf CAN pair on OBD pins 12/13 as well as the usual 6/14 pair. A generic cable can therefore look correct and still omit necessary connections.[^6]

A 2011-2012 activation output is a switched automotive-voltage circuit, not an ESP32 GPIO directly connected to a 12V wire. Use the documented OVMS output arrangement, or design and verify an equivalent driver. The OVMS expansion documentation distinguishes GPIO signals from its protected switched power output.[^44]

## 4. Cellular, Wi-Fi, and parked power

**Wi-Fi has fewer dependencies.** The ESP32 already supplies 2.4 GHz Wi-Fi, so it needs no additional modem, SIM, antenna cable, or cellular account. It works well when the vehicle reliably reaches a known access point. An access point broadcast by the box only gives nearby access; it does not provide internet connectivity. A phone hotspot that leaves with the driver cannot provide parked remote access.[^9]

**4G provides independent remote access.** It adds a SIM, modem, antenna, network setup, reconnect behavior, and transmit power peaks. Keep the integrated Wi-Fi hardware: the OVMS autostart interface already offers an Off setting, so normal operation can be cellular-only without changing the processor or removing recovery options.[^16]

Use the standard SIM7600G kit for the first build. The DIY A7670E is LTE Cat 1, but the specific E variant lists bands B1/B3/B5/B7/B8/B20, not B28; verify the precise regional model and local carrier coverage. Do not accidentally order the similarly named SIM800 T-Call, which is 2G. Telenor currently plans to end Norwegian 2G on 31 December 2027.[^3][^26][^25][^14]

The following are **calculations from OVMS's approximate v3.3 component figures**, not measured consumption of this proposed installation. They assume continuous operation and no replenishment from the car.[^10]

| Configuration | Approx. 12V current | Charge drawn per day |
| --- | --- | --- |
| Base + Wi-Fi client; no modem/GPS/AP | 28 + 2 = 30 mA | 0.72 Ah |
| Base + modem; Wi-Fi/GPS off | 28 + 8 = 36 mA | 0.86 Ah |
| All listed functions enabled | 86 mA | 2.06 Ah |

The larger savings are disabling the Wi-Fi access point and GPS, not insisting that the chip have no Wi-Fi. The documented v3.3 deep-sleep draw is still about **10 mA without the active GPS antenna**, or 15 mA with it. Deep sleep also means the main software cannot continuously receive remote commands. Measure the actual box plus any additional car wake activity; do not promise a month of parking from these component averages.[^10]

For a new Hologram G3 self-service SIM, published pricing is **$1/month + $0.03/MB**, with $3 for a SIM card. Example totals are $1.30 for 10 MB, $1.75 for 25 MB, and $2.50 for 50 MB, before applicable extras. These are usage scenarios, not an OVMS data forecast. The included SIM may have a legacy profile with different rates; verify that profile and Norway coverage in the dashboard.[^11][^12][^13]

Keep firmware downloads and heavy diagnostics on Wi-Fi/USB when convenient. Do not choose NB-IoT, LTE-M, or 5G merely because a listing says “IoT”: changing modem families also changes integration and availability behavior. The supported modem path matters more than headline throughput for this tiny workload.

## 5. Shopping list for the recommended first box

All quantities below are for one vehicle. Pounds are the seller's **ex-VAT** prices. Stock is a dated listing observation, not a reservation. Each source number links to the exact product or supplier statement.

| Qty | Buy | Price/status | Selection notes |
| --- | --- | --- | --- |
| 1 | OVMS v3.3 WiFi/4G kit | £195.99; in stock | Recommended. Modem, enclosure, SIM and both antennas included.[^4] |
| 1 | Nissan ZE0/e-NV200 cable | £9.94; in stock | Only for the applicable older Leaf. Buy separately or select it with kit, not both.[^6] |
| 1 | ZE1 gateway tap harness | Price/delivery unconfirmed | Replaces older cable for a ZE1; supplier batch announced 2 September.[^7] |
| 0-1 | Micro-USB data cable | Allow £3-8 | Setup/recovery; reuse an existing data-capable cable |
| 1 set | Mounting ties/pads and loom protection | Allow £5-15 | Secure box and strain-relieve cable clear of pedals |
| Varies | TCU isolation/activation connection materials | Quote after car identification | Extra wake output on earliest cars; reversible TCU work on applicable cars |

**For Wi-Fi-only use:** substitute the £159.99 OVMS Wi-Fi unit. There is no cellular SIM requirement. It retains the vehicle interfaces and USB recovery connection.[^5]

For a compatible older Leaf, the 4G kit and cable total £205.93. Including the two accessory allowances gives **£213.93-228.93 before shipping/tax and any TCU work**. The equivalent Wi-Fi range is **£177.93-192.93**. These are purchase subtotals; installation labor is excluded. A ZE1 total cannot honestly be finalized until the harness is priced.

The seller says exports outside the UK are supplied without UK VAT once the address is entered. For a Norwegian private purchase, budget Norwegian import VAT and possible carrier handling charges; Norway's ordinary VAT rate is 25%. Do not add Norwegian VAT on top of the shop's UK VAT-inclusive price. An illustrative £20 shipping assumption gives `(£205.93 + £20) × 1.25 = £282.41` in foreign-currency-equivalent cash cost, before accessories, fees, and conversion. The shipping figure is an allowance, not a quote.[^41][^42]

This purchase avoids buying separate CAN transceivers, a CAN controller, buck converter, enclosure, modem carrier, USB programmer, or GPS module. The included GPS antenna can remain unused when location is outside the scope. A regular data SIM is an alternative to Hologram once its APN and modem/network suitability are checked.

Before ordering for a ZE1, the only supplier-dependent item is the complete compatible harness. A working standalone OVMS box without that harness is not a completed parked-car installation.

## 6. Our own 4G hardware: concrete development route

If building the electronics is itself the objective, the best starting point found is **zbchristian's Rev B OVMS carrier plus a LILYGO T-Call A7670E**. This combines an ESP32, cellular modem, USB programming and antennas on one purchased board, with a carrier for power and two CAN channels. It is an engineering starting point, not an off-the-shelf Leaf kit.[^20]

The manufacturer product data currently lists **A7670E [H700], $26.52, available**. Its public page mixes several T-Call versions; the live A7670E variant was checked separately. Confirm PCB revision V1.0 or V1.1 because that determines the GPIO map.[^25]

| Qty | Component/order item | Source and purchasing instruction |
| --- | --- | --- |
| 1 | T-Call A7670E H700 | Buy exact LTE variant, not SIM800 or a different T-SIM board.[^25] |
| 1 | Rev B carrier PCB, assembled | Request fabrication/assembly from the published Gerber, BOM and placement files; populate both CAN channels.[^23][^24] |
| 2 on carrier | TCAN330DR | CAN physical interfaces, IC2/IC3; already part of PCB assembly order.[^23][^39] |
| 1 on carrier | MCP2515T-I/SO | Second CAN controller, IC5, with X49SM16MSD2SC 16 MHz crystal and associated parts.[^23][^40] |
| 1 on carrier | LMR51610XDBVR supply circuit | Include the specified inductor, filtering, fuse, diode, and voltage-sense parts.[^23][^38] |
| 1 set | DB9 male board connector, headers/sockets, remaining top-side parts | Reconcile with schematic and PCB; bottom-side BOM is not the complete order.[^24] |
| 1 | Printed enclosure | Use published case files; budget $10-25 for material/service.[^20] |
| 1 | Data SIM | $3 published new Hologram SIM price, or suitable existing SIM.[^11] |
| 1 | Correct vehicle harness | Same generation-dependent requirement as the assembled module |

Planning allowance: **$40-100 for carrier fabrication/assembly allocation, $10-25 for enclosure, and $10-25 for finishing parts**. With the $26.52 board and $3 SIM, that is **$89.52-179.52 before vehicle harness, freight, taxes, tools and labor**. These allowances are estimates, not manufacturer quotes; a minimum PCB batch or multiple shipping charges can exceed them.

The published assembly BOM has an empty LCSC part-number column. It needs component matching, ratings and footprint verification before assembly can be ordered. The schematic also contains parts absent from the bottom-side BOM. Do not upload it and approve automatic substitutions blindly.[^23][^24]

The supply uses a 65V, 1A buck-converter family. That specification alone does not establish automotive transient immunity of the assembled board. Check input capacitor ratings, reverse supply behavior, fusing, CAN-line protection, and modem burst stability. Its 10V Zener participates in the cutoff circuit; it is not proof of a complete input surge-protection design.[^38][^24]

## 7. Firmware work required for that 4G build

**The published T-Call build currently excludes the Nissan Leaf.** Its README names a MAX7317 dependency. The current upstream Leaf source still directly references that GPIO expander, while the peripheral member is compiled only when the expander is enabled. Selecting a later model year at runtime cannot cure a compile-time missing member.[^20][^2][^22]

For a confirmed **2013+ target**, the proposed adaptation is to isolate the legacy activation-output operations behind a hardware capability check. A build without the output must explicitly reject unsupported early-car wake-up instead of pretending success. Keep the existing timing and CAN commands. For a 2011-2012 target, add and test the real activation driver, or use standard OVMS hardware. Simply checking “MAX7317 enabled” without that hardware is not an implementation.

Use the supplied T-Call GPIO mapping as the base. For Rev B with T-Call V1.1, the mapping specifies internal CAN TX/RX on GPIO2/34, SPI on 18/19/23, and the second controller's CS/interrupt on 22/35. Modem connections differ between T-Call revisions. Confirm the actual board before generating the build configuration.[^21]

Build only the required vehicle support and retain networking, configuration, metrics, timekeeping, command handling, and the necessary CAN/poller components. Disable unused SD-card, expansion, scripting, logging and diagnostic components only as needed. Keep a reproducible configuration and upstream revision with the firmware image. Use the project's matching toolchain and dependencies; do not treat an Arduino example as the OVMS firmware build.

The published T-Call design has 4 MB of flash and its documented layout has no OTA updates. The proposed first custom box therefore uses **USB firmware recovery and updates**. Keep the USB port accessible. Standard OVMS has much more flash, and its current documentation describes larger OTA partitions; never flash a standard full-size image onto this small board.[^20][^18]

The carrier's cutoff claims are inconsistent: its overview says roughly 11.7V off/11.9V on, while the detailed schematic gives approximately 11.5V off/11.8V on for one resistor choice, dependent on actual Zener behavior. Treat the circuit as a candidate, calibrate it, and select thresholds with hysteresis appropriate to the actual car. Recovery must also be tested after the supply rises.[^24]

**Networking plan:** use the existing OVMS app/server first. An outbound device connection avoids opening an inbound port on the cellular network. The firmware has a TLS option for the V2 server; configure and test the intended server/client combination rather than assuming the default legacy transport provides modern authenticated encryption.[^15][^17]

Do not build a new phone app or cloud service to get version one working. If a custom interface is later justified, permit only a few named actions, display stale data honestly, and expire commands so a reconnect cannot unexpectedly start heating. Those are design requirements for our future software, not claims about unmodified upstream behavior.

## 8. The smaller Wi-Fi-only alternative

For a confirmed ZE1 and willingness to develop a smaller application, **simppeliTCU on LILYGO T-2CAN H784** is the most directly relevant alternative found. It targets the original TCU connection, provides a local web interface and MQTT, and uses the board's internal CAN channel. It does not reproduce the entire OVMS integration. Its own README calls it a draft.[^29]

The T-2CAN combines an ESP32-S3, 16 MB flash, 8 MB PSRAM, an internal CAN interface, and an external MCP2515 channel. It is **not** a drop-in processor replacement for the original ESP32 OVMS build. The standard H784 is enough; the CAN-FD variant adds nothing required by this project. The manufacturer's current data lists **$24.36, China stock available**, while its German H784 variant is unavailable.[^27][^28]

| Qty | Wi-Fi prototype purchase | Price/status |
| --- | --- | --- |
| 1 | LILYGO T-2CAN H784 | $24.36; choose standard version.[^27] |
| 1 | 12V/24V to 5V USB supply | Reference build uses FOUR Connect 65-01122, listed €12.90 by Motonet.[^34] |
| 1 | Sumitomo NH .025 connector set | 6098-5279 / 6098-5281; listing range $3.14-6.50; select complete set.[^33] |
| 1 | USB-A to USB-C cable | Data cable for programming; short power lead for installation |
| 1 set | Fused wiring, enclosure and mounting | Allow $20-40, then price locally |

The Sumitomo connectors are for a re-housing/adapter method, **not** a drop-in 40-pin TCU extension. Match terminals and wire sizes to the actual vehicle. The reference installation preserves TCU power while separating its CAN wires.[^32]

The USB supply is a reference-build component. Neither that example nor the development board's nominal “12V” input is evidence of a fully validated automotive power system. Test quiescent draw and voltage disturbances and provide a real fuse; do not attach raw vehicle power to the ESP32's low-voltage supply pins.

Source inspection found web control routes without application authentication, MQTT TLS configured with `setInsecure()`, and no implemented deep-sleep/low-voltage policy found in the inspected sketch. Before internet-connected or unattended use, add authentication, safe command handling, certificate validation, stale timestamps and an appropriate power strategy. Initially use an isolated bench/local network. A trusted broker alone does not repair missing certificate validation.[^30][^31]

Two other candidates were weaker foundations for this task. **Lama81/Leaf-ZE1-ESP32** adds a Particle Boron to an ESP32 and multiplexes one CAN controller between two buses. Its documented Boron firmware directory is excluded from the public checkout, so the cellular path is incomplete as published. **zerinrc/ze1tcu** explicitly describes itself as an experiment, not a ready road-car installation.[^35][^36][^37]

## 9. Build and acceptance plan

The order of work should prove the vehicle connection and behavior before spending effort shrinking the electronics. The effort estimates below assume someone comfortable with embedded electronics and vehicle trim work; they are planning estimates, not measured delivery promises.

**Stage 1 - identify the car and lock the scope, 1-2 hours.** Record model year, platform, region/trim, battery capacity and TCU connector. Decide whether home-only access is sufficient. Inspect signal strength where the car actually parks. Select the exact cable route and keep a record of the original connections. For a ZE1, establish supplier-harness availability or commission the documented interposer.

**Stage 2 - prepare one reference box, 1-3 hours excluding delivery.** Assemble the kit/antenna/cable combination, create an OVMS vehicle account, and run the local setup wizard. Connect the cellular antenna before powering the modem. The SIM7600G can fail to start from USB-only desk power, so test with suitable fused 12V power before diagnosing a network problem. Record the firmware and modem versions.[^15]

**Stage 3 - verify the car connection, roughly half a day.** Begin with CAN writing disabled and observe available broadcast metrics. Some diagnostic values need polling and will not appear in that mode. Confirm plausible battery readings and both expected buses before enabling commands. Install only on the low-voltage/CAN side; no traction-battery or orange-cable work is required. Use the documented power-down procedure and continuity-test a custom harness before reconnecting it.

**Stage 4 - prove the minimum controls, half a day plus repeat trials.** Enable writes after the initial checks. Test on a stationary car after it has genuinely gone to sleep, both plugged in and unplugged where the vehicle supports that. Check heating on, heating off, and charge start. Verify the resulting car state rather than accepting a “command sent” response. Leave charge-stop/limit automation and locks out of this first trial.

**Stage 5 - prove unattended behavior, at least 72 hours initially.** Log 12V voltage and input current while parked. Exercise network loss, SIM disconnect, router restart, module reboot and low-voltage recovery. Confirm the vehicle returns to its normal sleep state. Then test the intended longer parking duration under supervision; a three-day check alone does not establish several weeks of autonomy.

| Acceptance test | Pass condition |
| --- | --- |
| Ten cold starts/reboots | Reconnects and restores settings without manual repair |
| Ten parked climate cycles | Correct on/off behavior; result visible; no unexpected restart |
| Plugged-in charge-start trials | State confirms actual charging or a clear reason it did not start |
| Loss of connectivity | Honest offline/stale display; no delayed action when connection returns |
| Power/sleep check | Measured draw accepted; car sleeps; cutoff/recovery works as intended |
| Reversibility | Removing box/restoring original loom restores the original connection |

Only after these pass should a custom T-Call carrier replace the reference hardware. For that path, first prove the Leaf firmware builds and fits, then quote/assemble one or a small minimum batch, run bench checks on both CAN channels, and repeat the same vehicle acceptance tests. Allow **2-4 weeks elapsed** for a custom prototype with fabrication and iteration; a suitable assembled kit can often be configured in a day once the vehicle harness is ready.

## 10. Decisions, cost boundaries, and remaining uncertainty

**Recommended decision:** if this is one personal device, start with the assembled 4G OVMS kit and simplify configuration. If home-only operation is sufficient, the assembled Wi-Fi version is simpler and saves £36 before tax. If ownership of the circuit design is essential, use the T-Call/Rev B plan and budget explicit Leaf adaptation and power-validation work.

Do not buy both experimental platforms “just in case.” The alternatives answer different questions: the T-Call path preserves more of the OVMS software, while the T-2CAN path explores a smaller ZE1-specific application. Their purchase prices are not directly comparable without including harnesses, assembly, tools, taxes, firmware work and failed iterations.

For a one-off build, even a few engineering hours can exceed the hardware saving. For repeated builds, the arithmetic changes: use `engineering cost ÷ per-unit saving` as the break-even count, with both inputs based on actual quotes. As an illustration only, €2,000 of development divided by €100 saved per unit requires 20 units before the initial work is recovered. Do not treat this as a production quotation.

| Item still to resolve | Why it matters | Resolution before installation |
| --- | --- | --- |
| Exact Leaf generation and TCU | Determines loom and wake circuitry | Identify car/connector and match documentation |
| Away-from-home requirement | Determines whether 4G is necessary | Confirm intended parking/use pattern |
| ZE1 cable delivery and pinout | Prevents an incomplete kit purchase | Obtain complete supplier specification or fabricate verified loom |
| SIM profile and coverage | Changes recurring cost and connectivity | Confirm Norway service in actual account; test at parking locations |
| Custom Leaf build | README explicitly excludes it | Implement capability handling; compile, size-check and bench-test |
| Long-park power budget | Can make remote control unavailable or drain 12V battery | Measure complete installation and test cutoff/recovery |

The proposed custom firmware and hardware remain **uncompiled and untested on a vehicle**. Electrical validation, harness verification and real-world reliability are concrete tasks in the build plan. Vendor stock and account-specific SIM coverage can change before ordering.

Keep one “known working” firmware image, build configuration, connection drawing and test record. Standard OVMS release and partition documentation should guide updates; do not move a successful first box onto daily builds automatically.[^18]

OVMS's top-level project license is MIT, with separately licensed third-party components. Keep notices and inspect dependencies when redistributing. This personal build plan does not establish readiness to manufacture or sell an automotive radio product; that would require a separate engineering and compliance scope. The license observation is based on the repository file, not a legal clearance.[^43]

## Sources

All online sources were accessed on 11 September 2026. Undated pages are identified by title and publisher. GitHub implementation links are pinned where source was inspected; shop pages remain live because prices and stock change. Manufacturer/seller claims have not been converted into independent certification or reliability claims.

[^1]: Open Vehicles. [Nissan Leaf/e-NV200 integration guide](https://docs.openvehicles.com/en/latest/components/vehicle_nissanleaf/docs/index.html). Live documentation; generation-specific installation and controls.
[^2]: Open Vehicles. [Leaf implementation, vehicle_nissanleaf.cpp](https://github.com/openvehicles/Open-Vehicle-Monitoring-System-3/blob/85074a0ae7a983b308c6e2e081185492527ee073/vehicle/OVMS.V3/components/vehicle_nissanleaf/src/vehicle_nissanleaf.cpp). Snapshot 4 September 2026; lines 225-226, 1088-1097, 2015-2155, 2655-2817 inspected.
[^3]: Open Vehicles. [OVMS3 introduction and hardware](https://docs.openvehicles.com/en/latest/introduction.html). Processor, modem, software ecosystem and interfaces.
[^4]: OpenEnergyMonitor. [OVMS WiFi/4G kit](https://shop.openenergymonitor.com/open-vehicle-monitoring-system-ovms-wifi-4g-sim-ant-included/). Live price, included components and kit options.
[^5]: OpenEnergyMonitor. [WiFi-only OVMS](https://shop.openenergymonitor.com/wifi-only-open-vehicle-monitoring-system-ovms/). Live price and hardware.
[^6]: OpenEnergyMonitor. [Nissan ZE0/e-NV200 OBD2 cable](https://shop.openenergymonitor.com/nissan-ze0-e-nv200-obd2-ovms-cable/). Live price and explicit pin mapping; vehicle-year typo on seller page not used.
[^7]: Glyn Hudson / OpenEnergyMonitor. [ZE1 harness update, post 41 on page 2](https://community.openenergymonitor.org/t/ovms-ze1-40kwh-64kwh-2018-nissan-leaf-can-tap-cable-available/29798?page=2). 2 September 2026; tested cable and batch ordered. Earlier May update superseded.
[^8]: Open Vehicles / community wiring contribution. [Leaf ZE1 CAN tap wiring PDF](https://docs.openvehicles.com/en/latest/_downloads/1646e468de2bd4b3b5114c214970f277/Leaf-ZE1-CAN-Tap-Wiring.pdf). One-page diagram, visually inspected.
[^9]: Open Vehicles. [Wi-Fi networking](https://docs.openvehicles.com/en/latest/userguide/wifi.html). Integrated 2.4 GHz radio and AP/client behavior.
[^10]: Open Vehicles. [Warnings and notices: average power usage](https://docs.openvehicles.com/en/latest/userguide/warnings.html#average-power-usage). V3.3 component consumption and deep-sleep estimates.
[^11]: Hologram. [Current self-service pricing](https://www.hologram.io/pricing/). G3 price and SIM cost; scenarios calculated from rates.
[^12]: Hologram. [Legacy SIM and data pricing](https://www.hologram.io/pricing/legacy/). G1/G2/G3 differences.
[^13]: Hologram. [Coverage Explorer](https://docs.hologram.io/dashboard/billing/coverage-explorer). Account/SIM-specific network and pricing verification.
[^14]: Telenor Norge. [2G shutdown moved to 31 December 2027](https://www.telenor.no/om/presse-og-media/pressemeldinger/2g-utsettelse_5des_24/). 5 December 2024 announcement, current operator guidance.
[^15]: Open Vehicles. [Installation guide](https://docs.openvehicles.com/en/latest/userguide/installation.html). Setup, public server accounts and SIM7600G USB power caveat.
[^16]: Open Vehicles. [Autostart configuration source](https://github.com/openvehicles/Open-Vehicle-Monitoring-System-3/blob/85074a0ae7a983b308c6e2e081185492527ee073/vehicle/OVMS.V3/components/ovms_webserver/src/web_cfg_autostart.cpp). Wi-Fi Off option, lines 179-183.
[^17]: Open Vehicles. [OVMS server V2 implementation](https://github.com/openvehicles/Open-Vehicle-Monitoring-System-3/blob/85074a0ae7a983b308c6e2e081185492527ee073/vehicle/OVMS.V3/components/ovms_server_v2/src/ovms_server_v2.cpp). TLS setting/default and connection handling.
[^18]: Open Vehicles. [OTA updates](https://docs.openvehicles.com/en/latest/userguide/ota.html). Main/eap/edge channels and changing flash partition requirements.
[^19]: Open Vehicles. [OVMS changelog](https://github.com/openvehicles/Open-Vehicle-Monitoring-System-3/blob/85074a0ae7a983b308c6e2e081185492527ee073/vehicle/OVMS.V3/changes.txt). 18 July 2025 release 3.3.005 includes initial ZE1 support.
[^20]: zbchristian. [OVMS LILYGO carrier README](https://github.com/zbchristian/OVMS-Lilygo-based-Module/blob/70e1453b1129fc43690fc2d55066e0693363bb0d/Readme.md). 25 September 2025 snapshot; hardware, limitations and Leaf exclusion.
[^21]: Open Vehicles. [T-Call V1.1 GPIO map](https://github.com/openvehicles/Open-Vehicle-Monitoring-System-3/blob/85074a0ae7a983b308c6e2e081185492527ee073/vehicle/OVMS.V3/components/gpio_maps/lilygo_tc_v11.h). Hardware-specific pins.
[^22]: Open Vehicles. [Peripheral declarations](https://github.com/openvehicles/Open-Vehicle-Monitoring-System-3/blob/85074a0ae7a983b308c6e2e081185492527ee073/vehicle/OVMS.V3/main/ovms_peripherals.h). Conditional MAX7317 member, lines 160-162.
[^23]: zbchristian. [Rev B PCB production files and bottom BOM](https://github.com/zbchristian/OVMS-Lilygo-based-Module/tree/70e1453b1129fc43690fc2d55066e0693363bb0d/eagle/JLCPCB). Parts, Gerber and placement files; LCSC identifiers empty.
[^24]: zbchristian. [Rev B schematic](https://github.com/zbchristian/OVMS-Lilygo-based-Module/blob/70e1453b1129fc43690fc2d55066e0693363bb0d/eagle/schematic_revB.pdf). Power circuit, cutoff calculations, connectors and additional parts; Eagle source cross-checked.
[^25]: LILYGO. [T-Call A7670E H700](https://lilygo.cc/products/t-call-v1-4?variant=43440642719925). Variant/stock verified through the same product's public `.js` data; $26.52, available. PCB revision still requires confirmation.
[^26]: SIMCom. [A7670 series](https://cn.simcom.com/product/A7670X.html). Regional band table; A7670E versus other variants.
[^27]: LILYGO. [T-2CAN H784, China stock](https://lilygo.cc/products/t-2can?variant=51355687583925). Variant/stock verified through product `.js` data; $24.36, available; Germany variant unavailable.
[^28]: LILYGO. [T-2CAN documentation](https://wiki.lilygo.cc/products/industrial-series/t-2can/). Processor, memory and two distinct CAN controllers.
[^29]: fkorhone. [simppeliTCU README](https://github.com/fkorhone/simppeliTCU/blob/75ce756bb1159dedffa824f0089eb0cc1af99f0d/README.md). 8 July 2026 snapshot; scope, hardware and draft status.
[^30]: fkorhone. [simppeliTCU main sketch](https://github.com/fkorhone/simppeliTCU/blob/75ce756bb1159dedffa824f0089eb0cc1af99f0d/simppeliTCU/simppeliTCU.ino). State handling, control routes and runtime behavior inspected.
[^31]: fkorhone. [simppeliTCU MQTT implementation](https://github.com/fkorhone/simppeliTCU/blob/75ce756bb1159dedffa824f0089eb0cc1af99f0d/simppeliTCU/mqttInterface.cpp). Certificate validation disabled with `setInsecure()`, line 183.
[^32]: fkorhone. [simppeliTCU installation](https://github.com/fkorhone/simppeliTCU/blob/75ce756bb1159dedffa824f0089eb0cc1af99f0d/docs/installation.md). Connector adaptation and TCU supply/CAN method.
[^33]: Eastern Beaver. [16-pin Sumitomo NH .025 connector](https://www.easternbeaver.com/product/16-pin-sumitomo-nh-025-connector/). 6098-5279/6098-5281, terminals and price range.
[^34]: Motonet. [FOUR Connect USB supply 65-01122](https://www.motonet.fi/tuote/four-vedenpitava-usb-pistorasia-12-24-v?product=65-01122). €12.90 listing; Finland availability observed, Norway delivery not confirmed.
[^35]: Lama81. [Leaf-ZE1-ESP32 README](https://github.com/Lama81/Leaf-ZE1-ESP32/blob/989afb0e513b63de73643ba83e4503a2f1e0d537/README.md). 11 September 2026 snapshot; ESP32 + Boron architecture.
[^36]: Lama81. [Repository exclusions](https://github.com/Lama81/Leaf-ZE1-ESP32/blob/989afb0e513b63de73643ba83e4503a2f1e0d537/.gitignore). `boron/` excluded; absent from inspected checkout.
[^37]: zerinrc. [ZE1 TCU emulator](https://github.com/zerinrc/ze1tcu). Explicit experimental scope and unresolved TCU interaction.
[^38]: Texas Instruments. [LMR516xx datasheet, Rev B](https://www.ti.com/lit/ds/symlink/lmr51610.pdf). 65V input, 0.6A/1A family and electrical requirements.
[^39]: Texas Instruments. [TCAN330](https://www.ti.com/product/TCAN330). 3.3V CAN transceiver and datasheet.
[^40]: Microchip. [MCP2515](https://www.microchip.com/en-us/product/MCP2515). Standalone SPI CAN controller and ordering resources.
[^41]: OpenEnergyMonitor. [Tax and shipping policy](https://shop.openenergymonitor.com/tax-shipping-returns-warranty/). Export VAT treatment; destination charges separate.
[^42]: Norwegian Tax Administration / Norwegian Customs. [VAT rates](https://www.skatteetaten.no/satser/merverdiavgift/) and [import calculation guidance](https://www.toll.no/no/bedrift/import/beregning). Ordinary 25% rate and import value treatment.
[^43]: Open Vehicles. [License](https://github.com/openvehicles/Open-Vehicle-Monitoring-System-3/blob/85074a0ae7a983b308c6e2e081185492527ee073/LICENSE). MIT terms and separately licensed components.
[^44]: Open Vehicles. [EGPIO hardware](https://docs.openvehicles.com/en/latest/userguide/egpio.html). GPIO versus switched 12V output.
