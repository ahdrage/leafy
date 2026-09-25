# Rev D design review — 12 September 2026

**150 × 150 mm hand-solder engineering prototype.** The native KiCad electrical/layout checks pass. This establishes CAD consistency, not a physically tested heater controller. Firmware, assembly, bench tests and vehicle tests remain.

## Assembly decision

The factory list contains exactly **U1, U2, U4 and L1**. U1's exposed underside pad needs a suitable reflow process, U2 has underside ground connections, and U4 is a small six-lead package. L1 is factory fitted as requested. These choices leave **37 hand-fitted parts**, with **21 distinct purchasing MPNs**. The completed circuit still has 41 components. TP1–TP7 and four mounting holes are PCB features, not extra purchased parts.

U3 remains the SOIC-8 version of TCAN3403-Q1, with visible 1.27 mm pitch leads and longer pad toes. D4 remains the three-lead PESD2CAN, with a hand-solder footprint. These are the most demanding hand-fitted components. Larger pads make access easier; this is still a surface-mount soldering project.

## Circuit and component checks

- Every existing component pin retains its Rev C electrical net. GPIO assignments, Nissan cable pinout, UART pinout and CAN standby pull-up are unchanged. No termination resistor, USB circuit or additional common-mode choke has been introduced.
- All 13 resistors retain their resistance and 1% tolerance while moving from 0603 to 1206. All capacitors retain nominal capacitance; voltage ratings are equal or higher. C1 and C5–C7 retain their exact original 1210 MPNs.
- C2 is KEMET C1206C224K1RACTU, 220 nF / 100 V; C3/C8 are C1206C105K3RACTU, 1 µF / 25 V; C4/C10–C14 are C1206C104K5RACTU, 100 nF / 50 V; C9 is C1206C106K4RACTU, 10 µF / 16 V. These are X7R ceramic parts. Nominal value and voltage rating do not remove DC-bias or thermal-shock effects.
- D6 is Lite-On LTST-C150KGKT, a 1206 green LED. Cathode is pad 1 / GND, marked K. R9 remains 1 kΩ.
- SW1/SW2 are Omron B3F-1000. The manufacturer drawing was visually checked: 6.5 × 4.5 mm hole spacing, 4.3 mm actuator height and two horizontally common contact pairs match the footprint. The 1.1 mm finished holes are at the upper end of the drawing's 1.0 to 1.1 mm reference range. Both contact groups remain separate until pressed.
- The regulator retains TI's 3.3 V reference values: 22 µH, three 22 µF output capacitors, and 100 kΩ / 43.2 kΩ feedback. The nominal output is 3.315 V. Using 1% resistor tolerances and the 1.5% reference bound gives approximately 3.220–3.412 V before dynamic effects. Startup, ripple, load response and temperature still require measurement.
- J3 exposes GND, board RX and board TX only. Programming requires a 3.3 V logic UART adapter and separate regulated 12 V bench power. U4 clamps the external UART lines; it does not make 5 V signalling acceptable.

Primary references: [TI regulator datasheet](https://www.ti.com/lit/ds/symlink/lmr36510.pdf), [TI CAN transceiver datasheet](https://www.ti.com/lit/gpn/TCAN3403-Q1), [ST protection datasheet](https://www.st.com/resource/en/datasheet/usblc6-2.pdf), [Nexperia CAN protection datasheet](https://assets.nexperia.com/documents/data-sheet/PESD2CAN.pdf), [Yageo RC resistor series](https://www.yageogroup.com/content/datasheet/asset/file/PYU-RC_GROUP_51_ROHS_L), [KEMET 220 nF](https://search.kemet.com/component-documentation/download/specsheet/C1206C224K1RACTU), [KEMET 1 µF ordering alias](https://search.kemet.com/component-documentation/download/specsheet/C1206C105K3RAC7800), [KEMET 100 nF](https://search.kemet.com/component-documentation/download/specsheet/C1206C104K5RACTU), [KEMET 10 µF](https://search.kemet.com/component-documentation/download/specsheet/C1206C106K4RACTU), [Lite-On product catalogue](https://optoelectronics.liteon.com/upload/media/service/Publications/2017ProductCatalog/2017LiteOnCatalog.pdf), [Omron B3F drawing and handling limits, pages 3–4](https://omronfs.omron.com/en_US/ecb/products/pdf/en-b3f.pdf).

## Layout and fabrication checks

The enlarged board separates the power, radio, car interface and programming sections. Local regulator and bypass routes remain close to their components. Enlarging the PCB does not justify stretching the regulator's switching loop across it. The hand-parts legend uses the spare central area.

There are four copper layers. In1.Cu is the ground reference plane; In2.Cu distributes protected input and 3.3 V with ground in the remaining area. Ground pours and 154 separate ground vias connect the layout. Neither internal layer contains routed signal tracks. Signal/power track widths are intentionally different to suit their function; actual routed tracks are at least 0.30 mm, above the project's 0.25 mm manufacturing target.

Hand-fitted parts have extended pads and thermal-relief plane connections. The regulator and radio retain direct thermal-pad connections. The radio antenna extends beyond the board, with a rule area covering all four copper layers. Filled-copper sample points inside that clearance were checked. Keep metal enclosures and mounting hardware away from the antenna; see [Espressif's layout guidance](https://docs.espressif.com/projects/esp-hardware-design-guidelines/en/latest/esp32c3/pcb-layout-design.html).

Factory paste exists only for U1/U2/U4/L1. Both factory BOM formats and both placement formats contain exactly these four references. All 37 hand parts are absent from factory purchasing/placement files. Full-reference files are explicitly labelled. The hand BOM quantities are 37 parts for one board and 74 for two, before spares.

The thermal holes are ordinary plated holes, not filled/capped microvias. U2's thermal-hole masks are open on both surfaces. The assembler must review stencil coverage and solder wicking before manufacture; process changes and any extra cost need review. The 3D render illustrates the complete assembly but lacks the fuse body model and uses an approximate DB9 model. It is not an enclosure drawing.

## Recorded verification

| Check | Result |
| --- | --- |
| Native KiCad 10.0.6 schematic ERC | 0 reported violations |
| Native PCB DRC, all severities/all track errors | 0 reported violations |
| Unconnected items | 0 |
| PCB versus schematic parity | 0 issues |
| Per-item DRC exclusions | None |
| Full native schematic/BOM/PCB comparison | All 41 components match |
| Critical manually routed copper | All 299 original items retain their geometry, nets and sizes after routing |
| Board outline and manufacturing origin | 150 × 150 mm; lower-left origin |
| Factory stencil/BOM/placement membership | U1, U2, U4, L1 only |
| Rev C native source | Preserved byte for byte against the recorded baseline |

Reports are `exports/erc.json`, `exports/drc-final.json`, `exports/independent-audit.json` and `exports/manufacturing-audit.json`. The independent audit contains 907 assertions, including repeated per-pin and per-route comparisons; this is not 907 separate physical tests. Its board and schematic hashes identify the checked files.

Two inherited rule categories are ignored: footprint type mismatch (SMT packages contain plated thermal holes) and unused tuning-profile track geometries. No short-circuit, connectivity, clearance, library-matching or schematic-parity errors were waived. Remaining noncritical routes were completed with a router interchange; KiCad's final refilled native board is the verification authority. The intermediary router representation is not a manufacturing file.

## Remaining physical work

Follow `HAND-ASSEMBLY.md`. Do not power the four-part factory assembly before completing the remaining circuit. Inspect soldering and polarity, check the supply while holding ESP_EN low, then measure startup/load response and program the radio. Check both buttons and UART, CAN standby and radio performance before connection to the car.

The new B3F buttons are rated −25 to +70 °C and are not washable; fit them after cleaning. This limits the prototype's specified operating envelope and does not qualify it for a colder parked car. Ceramic capacitors require controlled hand-solder heating. Thermal performance, transient/EMC immunity, vibration, enclosure fit, parked current and low-battery behaviour have not been physically verified. The 65 V regulator rating is not a 65 V continuous rating for the whole assembly.

The original Leaf model-year/cable/TCU and command-sequence checks remain necessary. Registration in 2015 alone does not prove the required CAN profile. No working heater firmware or OTA update implementation is included. See the [OVMS Leaf documentation](https://docs.openvehicles.com/en/latest/components/vehicle_nissanleaf/docs/index.html).

The larger PCB may increase fabrication cost. Factory placement falls to four parts, but setup, sourcing, inspection and shipping remain. No new price or guaranteed saving is claimed by this revision.
