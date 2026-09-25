# Credits and provenance

## OVMS / Open Vehicles

Leafy began with the question: can the Leaf remote-climate function documented by OVMS be implemented in a simple Wi-Fi-only box?

The climate protocol in `firmware/leaf-heat/include/control.hpp` is derived from Open Vehicle Monitoring System 3, revision `85074a0ae7a983b308c6e2e081185492527ee073`:

- [Leaf source](https://github.com/openvehicles/Open-Vehicle-Monitoring-System-3/blob/85074a0ae7a983b308c6e2e081185492527ee073/vehicle/OVMS.V3/components/vehicle_nissanleaf/src/vehicle_nissanleaf.cpp): wake frames, climate bytes and timing.
- [Leaf header](https://github.com/openvehicles/Open-Vehicle-Monitoring-System-3/blob/85074a0ae7a983b308c6e2e081185492527ee073/vehicle/OVMS.V3/components/vehicle_nissanleaf/src/vehicle_nissanleaf.h): repeat-count reference.
- [Vehicle documentation](https://docs.openvehicles.com/en/latest/components/vehicle_nissanleaf/docs/index.html): vehicle generations, TCU installation and limitations.
- [Upstream licence](https://github.com/openvehicles/Open-Vehicle-Monitoring-System-3/blob/85074a0ae7a983b308c6e2e081185492527ee073/LICENSE).

The source credits **Michael Stegen / Stegen Electronics, Mark Webb-Johnson, Sonny Chen @ EPRO/DX and Tom Parker**. The full original notice is preserved in [OVMS-NOTICE.txt](firmware/leaf-heat/OVMS-NOTICE.txt). Credit also belongs to subsequent OVMS contributors.

Leafy's board, local application, battery protection and narrowed sequencer are developed for this separate prototype. Leafy does not run a complete OVMS image or reproduce its diagnostics, apps, cloud services or supported-vehicle range. OVMS's successful operation does not establish that this custom board works.

## Project and review

Project owner: **Alf-Henning Drage**. Thanks to **Adi** for practical reviews of routing, planes, silkscreen, solderability and exposed-pad assembly. This acknowledgement does not imply certification of the design.

Development used AI-assisted research, CAD scripting, firmware and documentation, followed by native CAD checks, source comparisons and host tests. Physical assembly, electrical and vehicle tests remain necessary; generated explanations and passing static checks are not proof of operation.

## Tools and references

- [KiCad](https://www.kicad.org/): schematic, PCB, ERC/DRC, manufacturing exports and rendering. Project libraries include KiCad-derived symbols/footprints; see [library licensing](https://www.kicad.org/libraries/license/) and retained notices in `LICENSES/`.
- [KiCAD-MCP-Server](https://github.com/mixelpixx/KiCAD-MCP-Server): part of the local CAD setup, not vendored in this publication.
- [Freerouting](https://github.com/freerouting/freerouting): routing assistance, followed by local corrections and KiCad checks.
- [Blender](https://www.blender.org/): enclosure generation, mesh checking and renders.
- [ESP-IDF](https://github.com/espressif/esp-idf) and [PlatformIO](https://platformio.org/): firmware framework and toolchain.
- TI, Espressif and other component manufacturers: electrical/package/layout data linked in the design review and BOM.
- [OpenEnergyMonitor cable documentation](https://shop.openenergymonitor.com/nissan-ze0-e-nv200-obd2-ovms-cable/): passive Nissan cable pinout.

Names identify sources and parts, not sponsorship. Manufacturer PDFs and downloaded web pages are linked at source rather than redistributed as project-owned content. Dependencies retain their own licences.
