# Rev A design review and validation record

Date: 2026-09-11. Tool: KiCad 10.0.6.

## Completed checks

- Native KiCad schematic electrical rules check: **0 violations**.
- Native KiCad PCB rules check with filled ground zones: **0 violations**.
- Native KiCad unconnected-items check: **0 remaining connections**.
- Native KiCad PCB-to-schematic comparison: **0 mismatches**.
- No DRC exclusions were used to hide routing errors. Power-source flags identify external supplies and the regulator output in the schematic.
- The PCB was populated from the schematic's exported netlist. Manufacturer and MPN fields were copied into the footprints. The three mechanical holes are marked board-only and excluded from purchasing/placement lists.
- Power-switching and USB connections were routed explicitly. Remaining connections were routed locally, then native KiCad findings were corrected. Both copper layers contain ground pours; the radio antenna keepout is retained.
- Native 2D and 3D views were inspected. The design was opened in the user's KiCad application.

These checks establish CAD connectivity and geometry under the configured rules. They do not validate the circuit under load, radio performance, firmware, CAN behavior or compatibility with the actual vehicle.

## Custom library review

- `NorComp_182-009-113R531`: signal spacing 2.77 × 2.84 mm; 1.20 mm signal drills; mounting pitch 24.99 mm; mounting drills 3.20 mm. Based on the manufacturer's [182-series drawing](https://content.norcomp.net/rohspdfs/Connectors/18Y/182/182-yyy-113Ryy1.pdf). The generic body model/outline is approximate. Confirm the exact hardware suffix, connector mating depth and enclosure setback before releasing the board.
- `ESP32-C3-WROOM-02_0p3mm_Vias`: derived from KiCad's module footprint. Ground-pad thermal holes are 0.30 mm with 0.65 mm pads instead of the library's 0.20 mm holes. The antenna keepout remains in place. Printed outline segments are clipped to the PCB edge; the antenna intentionally overhangs.
- The custom TCAN3403 and USBLC6 symbols are simplified functional symbols with pin numbering taken from their manufacturer datasheets. The USBLC6 drawing represents the ESD array as a block, not its internal semiconductor circuit.

## Pending engineering and physical verification

1. Review the supply layout against TI's layout recommendations, including the input loop, switch node, feedback routing, capacitor effective capacitance, inductor temperature/current margin and exposed-pad assembly. The board has not been simulated or measured.
2. Confirm component availability and substitutes in the chosen assembler's quote. Do not silently replace the regulator variant, radio module, connector or protection parts. The part list is a design BOM, not a live stock reservation.
3. Measure 3.3 V during USB startup and Wi-Fi transmit bursts at the minimum intended USB voltage, and from a current-limited 12–14.5 V bench source. Check regulator temperature, ripple, restart and diode reverse leakage over temperature. USB power is intended for bench programming; do not assume every long or low-quality cable can start it reliably.
4. Verify that absent USB does not register as present, and that USB-present detection uses ADC thresholds. The 100 kΩ/100 kΩ divider gives approximately 2.5 V from 5 V VBUS, which is too close to the guaranteed digital-high threshold to rely on digital input sensing across tolerances.
5. Measure sleep and Wi-Fi connected current at the car input. Firmware must set a conservative low-battery threshold and avoid a rapid wake/sleep cycle. Determine the actual maintenance burden on the Leaf's 12 V battery before leaving the device connected.
6. Check the passive cable with a meter, establish the vehicle's model-year profile, and follow OVMS instructions for the original TCU. Start with CAN listen-only tests and observe bus health before enabling heat commands. Verify standby across reset, firmware updates and USB connection.
7. Test heat-on, heat-off, the local stop timer, reboot during heating, Wi-Fi loss, charger-connected and charger-disconnected behavior. Confirm no continued bus wakefulness after the command sequence finishes.
8. Review the proposed input-transient envelope and test it with suitable equipment. SMBJ24CA has finite pulse-energy capacity. There is no claim of ISO 7637 or ISO 16750 compliance, EMC approval or completed automotive qualification.
9. Fit-test the connector and mounting holes; design a non-metallic enclosure that keeps the antenna clear of wiring and metal. Verify condensation, cold operation, cable strain relief and retention before installation.

## Primary design references

- [OVMS Nissan Leaf integration](https://docs.openvehicles.com/en/latest/components/vehicle_nissanleaf/docs/index.html)
- [TI LMR36510 power regulator](https://www.ti.com/lit/ds/symlink/lmr36510.pdf)
- [TI TCAN3403-Q1 CAN transceiver](https://www.ti.com/lit/gpn/TCAN3403-Q1)
- [Espressif ESP32-C3-WROOM-02 module](https://documentation.espressif.com/esp32-c3-wroom-02_datasheet_en.html)
- [Espressif schematic checklist](https://docs.espressif.com/projects/esp-hardware-design-guidelines/en/latest/esp32c3/schematic-checklist.html)
- [Bourns SRN6045TA inductor](https://www.bourns.com/docs/Product-Datasheets/SRN6045TA.pdf)
- [Nexperia PESD2CAN](https://assets.nexperia.com/documents/data-sheet/PESD2CAN.pdf)
- [Nexperia PMEG6030EP](https://assets.nexperia.com/documents/data-sheet/PMEG6030EP_.pdf)
- [Nexperia BZT52-B Zener series](https://assets.nexperia.com/documents/data-sheet/BZT52-B_SER.pdf)
- [ST USBLC6-2](https://www.st.com/resource/en/datasheet/usblc6-2.pdf)
- [GCT USB4105 connector](https://gct.co/files/drawings/usb4105.pdf)
- [NorComp 182 connector](https://content.norcomp.net/rohspdfs/Connectors/18Y/182/182-yyy-113Ryy1.pdf)
