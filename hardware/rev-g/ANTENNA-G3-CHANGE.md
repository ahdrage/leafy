# Rev G.3 — external Wi-Fi antenna

U2 changes from Espressif ESP32-C3-WROOM-02-N4 to **ESP32-C3-WROOM-02U-N4**, factory supplied by JLCPCB as **C2926676**. ANT1 is one **Molex 1461530300** per board, ordered from Mouser as **538-146153-0300** (supplier MPN punctuation: 146153-0300). It plugs directly into U2's U.FL socket; no extra adapter or RF trace is needed.

The antenna has an integral 300 mm, 1.13 mm coax cable and an MHF I / U.FL compatible plug. Its adhesive flex element is approximately 35 × 9 mm. At the board's 2.4 GHz operating band it is specified as 50 Ω, 2.2 dBi peak gain, with operating temperature −40 to +85 °C. The extra 5/6 GHz bands do not add 5 GHz capability to this ESP32-C3.

Sources checked 14 September 2026:

- [Espressif module datasheet](https://documentation.espressif.com/esp32-c3-wroom-02_datasheet_en.html), external antenna connector and recommended land patterns. A PDF is saved in `references/esp32-c3-wroom-02-02u.pdf`.
- [Molex specification F3](https://www.molex.com/content/dam/molex/molex-dot-com/products/automated/en-us/productspecificationpdf/146/146153/PS-146153-100-001.pdf), §3 (MHF I for 0XXX, 300 mm, temperature), §6.1.6 (2.4 GHz gain). The current product specification supersedes older brochure temperature figures. Direct PDF download failed; the online PDF was inspected.
- [JLCPCB's Espressif catalogue entry](https://jlcpcb.com/partdetail/3250151-ESP32_C3_WROOM_02UN4/C2926676). Avoid the similarly named generic assembly-service entry.

## Electrical and manufacturing changes

Both module variants have the same 19 numbered pins, GPIO functions and 4 MB flash. The official KiCad land patterns compare identically. The new body is 18 × 14.3 mm instead of 18 × 20 mm. The local symbol description, MPN, schematic, PCB footprint outline, 3D model and factory BOM now identify the external-antenna version.

All traces, vias, filled copper, pad positions, pad sizes, drill sizes, paste apertures, board edges and mounting holes remain identical to G.2. The old module's antenna keepout is deliberately retained as unused clearance; it causes no loss of function. No RF signal is exposed as a fabricated PCB pin. The schematic documents ANT1 as an off-board plug-in accessory, and `accessories.json` / `BOM-ACCESSORIES.csv` track it separately.

The factory still fits exactly U1/U2/U4/U5/U6/L1. You solder 49 PCB components and plug in ANT1 per board. The Mouser list therefore becomes 28 products / 100 pieces for two boards: 98 soldered parts plus two antennas. Do not buy U2 twice. No firmware code change is required; existing GPIO assignments, flash configuration and battery/CAN fixes remain intact.

Fresh ERC, refilled DRC and schematic parity all report zero violations. `exports/antenna-g3-audit.json` verifies the changes against the immutable `history/rev-g2-before-external-antenna.zip`, in addition to the complete 55-component native audit. G.2 is retained for history; use only current G.3 files for manufacturing.

## Cable and casing

Use [enclosure v2](../../enclosure/rev-g-v2/README.md). Its split cable exit accepts the terminated cable with the lid removed. The internal saddle takes a small nylon tie, protecting the connector from cable pull. Keep a slack loop at U2, avoid sharp bends and smooth printed edges. The case is not weatherproof. Fit the antenna with all power disconnected before enabling Wi-Fi; align the tiny plug squarely and press the connector, never the cable.

Mount the adhesive element inside the car on suitable plastic outside the box, away from metal and wiring, ideally in a position with a clear path toward the house. Install adhesive onto a clean dry surface at a warm temperature (ideally 21–38 °C). Try placement before permanently sticking it down. The 300 mm cable includes the length used inside the box; it is not 300 mm of free reach beyond the wall.

## Limits

Matching the antenna connector, frequency, impedance and gain establishes a sensible prototype choice, not guaranteed better range. The selected gain is below Espressif's stated 2.33 dBi limit outside FCC certification, but the antenna type/complete product still needs its own applicable RF assessment; this is not a certification claim. Check Wi-Fi signal and reconnection in the assembled case at the actual parking position before vehicle deployment. Supplier exposed-pad DFM, printed fit, supply/current measurements and car testing remain necessary. Battery cutoff still removes Wi-Fi power at dangerously low supply voltage.
