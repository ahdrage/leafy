# Build guide — G.5 prototype

Use a matched G.5 PCB, BOM and placement file. Read [validation status](VALIDATION.md) first.

## 1. Inspect the design

Open `hardware/rev-g/leaf-heat-v7.kicad_pro` in KiCad 10. Keep the local symbols, `Leaf.pretty/`, library tables and rules beside it. PCB Editor's 3D Viewer shows the board; a schematic PDF and assembly drawings are also included.

Native CAD and matching Gerbers are the reviewed starting point. Historical migration scripts are not a one-command release system. Read `hardware/rev-g/BUILD-REPRODUCTION.md` before regenerating anything.

## 2. Order partial assembly

Follow [ORDER-G5.md](../hardware/rev-g/ORDER-G5.md). Upload the G.5 Gerber ZIP, **BOM-FACTORY-JLCPCB.csv** and **CPL-FACTORY-JLCPCB.csv**. JLC rotations are already corrected; do not rotate them twice.

The recorded order is five four-layer PCBs, two with U1/U2/U4/U5/U6/L1 assembled on top. Confirm filling/planarization/copper caps on all eighteen thermal holes, explicitly including 0.33 mm. Use G.5 fabrication notes, not older tenting/stencil instructions. The factory must not power/program the incomplete boards. Review CAM and placement for each new order.

## 3. Hand assembly

Use [the required two-board parts list](../hardware/rev-g/exports/MOUSER-TWO-BOARDS.csv) and [HAND-ASSEMBLY.md](../hardware/rev-g/HAND-ASSEMBLY.md). A separate complete basket includes spares/tools; do not import both as cumulative quantities. Buy the correct passive cable, fasteners and bench equipment separately if needed.

Check each value, polarity and joint against the assembly image and back-side table. Practice surface-mount soldering first, particularly U3/D4. Inspect for bridges and rail shorts before powering.

## 4. Power and firmware

Keep the vehicle disconnected. Use a current-limited supply through J1; 13.5–14 V may be needed to cross the battery supervisor's restart threshold. Verify polarity and connector pin numbering.

A portable firmware setup from the repository root needs Python, a C++17 compiler for tests, and PlatformIO:

```sh
python3 -m venv .venv
.venv/bin/python -m pip install platformio==6.1.18
python3 firmware/leaf-heat/tests/run_host_tests.py
.venv/bin/pio run -d firmware/leaf-heat
```

The project pins Espressif32 6.12.0. Without local settings the image has empty credentials and CAN writes disabled. Copy `include/settings.example.hpp` to `include/settings.hpp` within the firmware directory; enter Wi-Fi credentials and a separate control key of at least 12 characters. Keep CAN disabled during commissioning. Never publish settings or configured binaries.

Use **3.3 V logic UART**: adapter TX → J3 pin 2, RX → pin 3, GND → pin 1. Leave adapter power disconnected. Power the board before connecting UART; remove UART before board power. Follow [firmware instructions](../firmware/leaf-heat/README.md) for BOOT/RESET and flashing.

## 5. Bench, network and vehicle tests

Measure regulation/ripple, cutoff/recovery, ADC accuracy and parked current. Attach the external antenna before Wi-Fi use. Reserve the IP address; use the same LAN without guest isolation. Test router restarts and weak signal for at least 24 hours, including absence of stale commands.

Test a properly terminated two-node CAN bench network first. Verify [cable continuity and vehicle/TCU profile](../hardware/rev-g/VEHICLE-WIRING.md). Only afterward explicitly enable CAN writes and test beside the car. Observe On/Off, local timeout and the car's own timeout. Transmit success does not prove heating.

## 6. Case

Use the STLs under `enclosure/rev-g-v2/print/`; Blender source and generator are included. PCB/component meshes are references, not printable parts. Read the enclosure guide for scale, fasteners, material, fit coupons and antenna strain relief. G.5 retains the checked G.3 mechanical geometry, with compatibility records. Physical fit and hot-car suitability remain unverified.
