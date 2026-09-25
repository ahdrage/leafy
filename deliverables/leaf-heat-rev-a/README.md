# Leaf Heat — custom Wi-Fi board, Rev A

**Engineering prototype, not released for manufacture or vehicle installation.**

The native KiCad 10 project is [leaf-heat-v1.kicad_pro](leaf-heat-v1.kicad_pro). It contains an editable schematic and a fully routed, two-layer 65 × 50 mm PCB. There are 47 populated components and three mounting holes. The module antenna and the car connector extend beyond the PCB outline.

The design is for a small box with a local Wi-Fi page containing **Heat on** and **Heat off**. This delivery contains the hardware design, not working firmware. Home Wi-Fi coverage was confirmed by the owner. The earlier Waveshare development-board plan is an alternative prototype approach; its pin assignments must not be used for this PCB.

## Files

- [Schematic](leaf-heat-v1.kicad_sch) and [PCB](leaf-heat-v1.kicad_pcb)
- [Schematic preview](exports/leaf-heat-v1.svg) and [3D preview](exports/leaf-heat-v1-3d.png)
- [Complete component list](exports/BOM.csv), [grouped purchasing list](exports/BOM-grouped.csv) and [placement file](exports/placements.csv)
- Project-specific symbols in `Leaf.kicad_sym` and footprints in `Leaf.pretty/`; keep the two library tables alongside the project.
- `exports/fabrication-review/` contains Gerber copper, mask, silkscreen, paste and board-outline layers plus separate plated/non-plated drill files. These are for engineering/manufacturer review, not a production release.
- [Electrical check](exports/erc.json), [layout and schematic matching check](exports/drc-final.json), [design review notes](DESIGN-REVIEW.md), [tooling research](TOOLING.md).

## What is on the board

| Function | Main component | Reason |
|---|---|---|
| Wi-Fi and controller | Espressif ESP32-C3-WROOM-02-N4 | Integrated antenna, flash and crystal; native USB and one CAN controller |
| Car communication | TI TCAN3403DRQ1 | 3.3 V CAN interface with standby, plus PESD2CAN protection |
| Car power to 3.3 V | TI LMR36510ADDAR | 65 V-rated, 1 A buck regulator with light-load operation |
| Input protection | 1 A fuse, SS110, SMBJ24CA | Fuse, reverse blocking and transient suppression |
| Programming | USB-C, USBLC6-2SC6 | Program without a separate USB-to-serial adapter |
| Monitoring | Battery and USB voltage dividers | Firmware can monitor parked battery voltage and inhibit commands during bench work |

There is no cellular modem, SIM, display, SD card, relay or extra CAN channel. Most of the small parts are required for power conversion, protection, stable booting and programming. This board requests climate operation over the car's existing CAN network; it does not switch heater power.

The power circuit uses TI's 3.3 V / 400 kHz reference values: 22 µH, three 22 µF output capacitors, 100 kΩ / 43.2 kΩ feedback divider (about 3.315 V nominal). Component tolerances, capacitor DC bias and physical performance still need verification. See the [LMR36510 datasheet](https://www.ti.com/lit/ds/symlink/lmr36510.pdf).

## Cable and firmware connections

Use the **Nissan ZE0/e-NV200 OVMS cable**, after continuity-checking the actual cable. A generic OBD-to-DB9 cable is not interchangeable. At the board's male DB9: pin 9 = car +12 V, pin 3 = ground, pin 7 = CAN-H, pin 2 = CAN-L. The shell is grounded. No 120 Ω termination is fitted, because this is a connection to the car's existing terminated bus. Verify the vehicle's model year and EV-CAN access before connection; registration in 2015 alone does not prove a 2015 model year. [OVMS Leaf documentation](https://docs.openvehicles.com/en/latest/components/vehicle_nissanleaf/docs/index.html).

| Firmware signal | ESP32-C3 GPIO | Board behavior |
|---|---:|---|
| CAN TX | 4 | Connect to the internal TWAI controller |
| CAN RX | 5 | 500 kbit/s for the intended Leaf profile |
| CAN standby | 1 | Pulled high by R10; high = standby |
| Battery sense | 0 / ADC1 | `VPWR × 47 / 1047`; measured after D1, so calibrate the diode drop |
| USB presence | 3 / ADC1 | Half VBUS; detect with ADC and hysteresis, not a raw digital input threshold |
| Status LED | 7 | High lights the LED |
| USB D− / D+ | 18 / 19 | Native USB programming |
| Boot straps | 2, 8, 9 | Pulled high; BOOT button pulls GPIO9 low |

The intended firmware must start with CAN in standby, never replay a heat request after reset, implement a local stop deadline, handle bus errors, and use low-battery sleep. R17 discharges USB VBUS and D5 limits its rise from D2 leakage when the board is car-powered. USB and vehicle grounds are common; the board is not isolated. During initial programming and bench testing, disconnect the vehicle cable.

For the intended 2013–2015 profile, follow the documented OVMS TCU-disconnection requirement and verify the selected command sequence. Heater behavior, plugged/unplugged operation and shutdown must be observed on the actual car. Do not treat a successful CAN transmission as proof that the cabin is heating.

## Before a prototype order

Have the power circuit, connector land pattern and assembly choices reviewed. Confirm the exact DB9 part and cable mating arrangement, then request a quote for **an assembled prototype**, including the through-hole DB9 connector. The board contains an exposed-pad regulator and a radio module that need appropriate reflow assembly.

Proposed fabrication: two-layer FR-4, 1.6 mm thickness, 1 oz copper, lead-free finish, green mask, white silkscreen. The small routing escapes use 0.2 mm tracks; the project minimum is 0.15 mm clearance. Vias use 0.3 mm drills. The assembly provider must review paste apertures, thermal-pad via solder wicking, component orientation and panel handling around the overhanging antenna. Placement coordinates and Gerbers use the lower-left drill/place origin. J1 uses a footprint origin at signal pin 1, so its placement entry is not a component-body centroid.

The 3D image uses KiCad library models. The DB9 body model is approximate and must not be used to finalize an enclosure. No enclosure has been designed yet.

The first assembled board needs power, USB, standby-current, CAN and cold-temperature tests. The 65 V regulator and TVS do not by themselves establish automotive transient compliance. There is no hardware battery cutoff; unattended parked operation depends on tested firmware and measured current draw.
