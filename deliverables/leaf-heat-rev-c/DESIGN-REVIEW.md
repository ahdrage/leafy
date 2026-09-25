# Rev C design review — 12 September 2026

**The USB-removal revision is complete and passes the documented CAD checks. It is not yet a demonstrated working heater controller.** Physical power, flashing, CAN, parked-current and vehicle tests cannot be established from CAD files.

## Change and cost rationale

The schematic and PCB replace USB-C with a UART0 programming header. Ten components were removed: J2, D2, D5 and R11–R17. Four were added: J3 and R18–R20. U4 was rewired as UART ESD protection; C14 changed from 1 µF to 100 nF and moved with it. U2 now uses GPIO20/21 for UART, while GPIO3/18/19 are no-connects. All other electrical connections, values and MPNs were compared against Rev B.

Population falls from **47 to 41** and distinct MPNs from **29 to 25**. The custom PCB has no USB differential pair and can use a standard four-layer stack without paid impedance control. Earlier calculator comparisons showed a $50.20 PCBWay fabrication difference and a $32.84 JLCPCB charge for the Rev B impedance option, **per batch**. These are evidence of removable service costs, not a fresh Rev C quotation or guaranteed net saving. The external programmer, bench supply/lead, connector assembly and current component sourcing also affect total cost. Existing online quotation requests still refer to Rev B.

Four layers and 1 oz inner copper remain. Reducing layer count, copper thickness or changing the vehicle interface would be separate work and is unnecessary to remove the USB-related charge.

## Electrical review

**Programming.** J3 pin 1 is GND, pin 2 is board RX and pin 3 is board TX. The saved schematic and pad map were checked against U2's module pins 11 (GPIO20/RXD) and 12 (GPIO21/TXD). RESET and the GPIO9 BOOT button remain, as do the high straps on GPIO2 and GPIO8. Serial recovery therefore remains available independently of application firmware. [ESP32-C3 module datasheet](https://documentation.espressif.com/esp32-c3-wroom-02_datasheet_en.html), [download guidance](https://docs.espressif.com/projects/esp-hardware-design-guidelines/en/latest/esp32c3/download-guidelines.html).

R18 and R19 are 1 kΩ series resistors, using the existing LED-resistor MPN. R20 is an existing-type 10 kΩ pull-up so RX does not float. Espressif recommends series resistance on UART TX, with 499 Ω as its example. Our 1 kΩ choice is an engineering tradeoff for part consolidation and current limiting at 115200 baud. With an assumed total 100 pF cable/input load, estimated 10–90% edge time is 0.222 µs, versus an 8.68 µs bit. With a 0.4 V adapter low, worst 1% resistor corners and supply corners, RX is approximately 0.679 V, below the conservative 0.805 V low threshold. These calculations do not qualify arbitrary cables or faster flashing. [Espressif schematic guidance](https://docs.espressif.com/projects/esp-hardware-design-guidelines/en/latest/esp32c3/schematic-checklist.html).

**ESD.** U4 has two feed-through channels: pins 1/6 protect RX and 3/4 protect TX; pin 2 returns to GND and pin 5 references the 3.3 V rail. C14 is a local 100 nF bypass. Protection sits near the service connector, with two nearby ground vias. The part is usable for signal protection beyond USB; it does not implement a USB protocol. Its presence does not establish whole-board ESD immunity. Connect only a 3.3 V logic adapter to a powered board; the resistors are not level shifters, and this interface does not provide powered-off isolation. [ST USBLC6-2 datasheet](https://www.st.com/resource/en/datasheet/usblc6-2.pdf).

**Power.** The board is powered through J1 pin 9, F1 and D1 into VPWR. The USB diode-OR branch and its leakage/discharge network are gone. J3 exposes no 5 V, 3.3 V or 12 V supply pin. The buck retains TI's 3.3 V reference values: 22 µH, three 22 µF output capacitors, 2.2 µF + 220 nF input capacitors, 100 kΩ/43.2 kΩ feedback, 1 µF VCC and 100 nF bootstrap bypass. Nominal output is 3.315 V; static corners using ±1.5% reference and 1% resistors are 3.220–3.412 V, within both major ICs' supply ranges. Ripple, DC-bias-dependent capacitance, startup and load transients still require measurements. The regulator pinout, capacitor voltage ratings and inductor MPN were retained and checked against the datasheet guidance. [TI LMR36510 datasheet, tables 6.5 and 8.1](https://www.ti.com/lit/ds/symlink/lmr36510.pdf).

**CAN and car input.** The fuse, reverse-blocking diode, input TVS, TCAN3403 and PESD2CAN network retain their connections and placement. U3 pins 3 and 5 use 3.3 V; pin 8 has standby pull-up R10. TX/RX remain GPIO4/5 and standby GPIO1. The DB9 remains pin 9 power, 3 ground, 7 CAN-H, 2 CAN-L. No bus termination or common-mode choke was added. U3's component-level ±58 V bus rating is not a whole-board transient test result; the TVS and input protection also have finite ratings. [TI TCAN3403-Q1 datasheet](https://www.ti.com/lit/gpn/TCAN3403-Q1), [PESD2CAN datasheet](https://assets.nexperia.com/documents/data-sheet/PESD2CAN.pdf).

The battery divider remains after D1 and needs calibration for diode drop. Its worst 1% corner is 2.974 V at 65 V VPWR; normal 12 V operation is far lower. This arithmetic does not rate the entire board for a sustained 65 V input: the input TVS conducts far below that. There is no independent hardware battery cutoff.

## Layout, mechanics and assembly

The saved board has a dedicated In1.Cu ground plane with no routed tracks. In2.Cu distributes 3.3 V and GND; its 3.3 V area extends to the UART protection. Both internal layers remain free of tracks. There are 84 separate ground vias, excluding thermal holes inside footprints. The new UART routes use F.Cu and B.Cu; they require no differential length/impedance rule. The protection chip sits immediately above J3, with approximately 3 mm of copper between each header signal and its ESD contact.

The original power/CAN placement and surviving route geometry were compared by footprint and copper-item identifiers. All 278 surviving original copper items retain their net assignments and endpoints. Obsolete USB copper and obstructing ground vias were removed deliberately; replacement local returns were added. Ground under the top UART routing was sampled at intervals no greater than 0.1 mm. The only absent-ground samples are expected non-ground plated-hole clearances. The antenna keepout remains on all copper layers and was checked against filled copper.

J3's 2.54 mm pitch, three 1.00 mm holes, pin-one marking and top mounting were checked against the saved board and [Harwin's connector specifications](https://www.harwin.com/products/M20-9990346). Its ground pin has thermal reliefs. It is not keyed; the three contacts are clearly printed. The existing DB9 footprint and mounting holes remain; its library 3D body is approximate. Physical mating and enclosure clearance still need confirming with the actual cable and connector. The J1 schematic symbol now explicitly names the custom footprint in its filter; its electrical pin map did not change.

All 41 placement rows match saved PCB coordinates and rotations, with no missing or extra components. The BOM identifies 39 SMT parts and two THT connectors. Gerber/drill origins and four copper-layer exports were checked. J1/J3 origins are pin 1, so their centroid/rotation interpretation must be reviewed by the assembler. Exposed-pad stencil and thermal-hole solder wicking also require factory process review.

## Check results and limits

| Check | Result |
|---|---|
| Native KiCad 10.0.6 ERC | 0 reported violations |
| Native DRC after zone refill, all reported severities and all track errors | 0 reported violations |
| Unconnected items | 0 |
| Schematic/PCB parity | 0 mismatches |
| Explicit DRC exclusions | None |
| Independent schematic/pad/BOM/preserved-copper audit | Passed |
| Placement count/origin/rotation audit | 41/41 passed |
| Visual review | Schematic, UART circuit, all four copper layers, placement and 3D rendering reviewed |
| Physical tests / firmware / car operation | Not performed / not implemented |

The footprint-type heuristic remains disabled because KiCad classified U1's SMD footprint as through-hole based on its plated thermal holes. U1 and U2 are correctly declared and purchased as SMT parts. The diagnostic result is preserved in `exports/drc-expanded.json`; this is a documented checker limitation, not a concealed electrical failure. Missing-courtyard, footprint-filter and track-to-via alignment checks that were disabled in Rev B are enabled in Rev C. The unused tuning-profile check remains disabled. ERC's inherited non-applicable simulation/global-label settings are listed in its report.

Evidence: [ERC](exports/erc.json), [DRC](exports/drc-final.json), [independent audit](exports/independent-audit.json), [manufacturing audit](exports/manufacturing-audit.json), [Rev B hashes](exports/baseline-sha256.json). The audit is not an independent human engineering sign-off or a substitute for a prototype.

## First prototype acceptance

1. Factory checks exact parts, polarized orientations, connector fit, stencil/thermal-hole treatment and complete assembly. Review its placement preview before production.
2. On a disconnected bench, inspect joints and check power-to-ground resistance before applying a current-limited 12 V supply. Measure 3.3 V and supply current, then exercise expected load and Wi-Fi bursts while checking ripple, reset behavior and regulator temperature.
3. Confirm UART boot log, first flash, normal reset and recovery after an intentionally nonworking application. Use 115200 baud and verify clean signal levels with the chosen lead.
4. Test CAN standby through power-up/reset, communication against a known CAN test setup, error handling and restart behavior. No vehicle connection is needed for these first tests.
5. Implement and verify firmware: authenticated local requests, no replay after boot, bounded heating/stop behavior, Wi-Fi reconnection and measured parked-current/low-battery policy. There is no USB-presence inhibit anymore; initial development stays on the disconnected bench. OTA/rollback is separate firmware work.
6. Verify the actual Nissan ZE0 cable pinout and the car's model-year/TCU requirements, then observe heat-on and heat-off on the car under supervision. Test plugged/unplugged behavior and bus sleep before leaving the box installed. Registration year alone is not a verified protocol profile. [OVMS Nissan Leaf documentation](https://docs.openvehicles.com/en/latest/components/vehicle_nissanleaf/docs/index.html).

Automotive transient, EMC/EMI and cold-temperature operation remain unqualified. This review preserves the agreed existing vehicle-protection design; it does not certify it or claim that every possible vehicle fault is covered.
