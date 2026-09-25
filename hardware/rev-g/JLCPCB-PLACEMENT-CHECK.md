# Leafy G.5 — placement check for the NEW order

The component positions, MPNs, lead geometry and corrected JLC CPL are unchanged from G.4. The six catalogue offsets were verified in earlier JLC previews. The new G.5 order still needs its own preview check: historical approval is not current approval.

| Part | JLCPCB code | Native KiCad angle | JLC angle | Required physical alignment |
| --- | --- | ---: | ---: | --- |
| L1 | C2044314 | 0° | 0° | Centred, both terminals aligned, nonpolar |
| U1 | C1858393 | 0° | 270° | Eight leads aligned; pin one upper-left |
| U2 | C2926676 | 0° | 0° | External-antenna 02U model; all eighteen outer castellations aligned, pin one upper-left, socket upper-right |
| U4 | C7519 | 90° | 0° | Six leads aligned; pin one lower-left |
| U5 | C5218894 | 0° | 270° | Fourteen leads aligned; pin one upper-left |
| U6 | C2866750 | 0° | 270° | Fourteen leads aligned; pin one upper-left |

`CPL-FACTORY-JLCPCB.csv` already includes the catalogue corrections. Do not rotate it again. `CPL-NATIVE-REFERENCE-ONLY.csv` and `placements-FACTORY.csv` are reference files, not the JLC upload. Use `FACTORY-PIN1-REFERENCE.csv` for independent physical pad-one coordinates (origin lower-left, X right, Y up).

U2 is the ESP32-C3-WROOM-02U-N4 with an external antenna socket. Its origin is (73,92) mm in the exported coordinate system; pin one is (64.25,98) mm. Fit the specified C2926676 and keep the cable socket accessible.

Only U1/U2/U4/U5/U6/L1 are factory assembled. The other 49 components and external ANT1 are customer fitted. Factory paste Gerbers are reference only; normal JLC stencil engineering is accepted. U1/U2 require the G.5 filled/capped process from the fabrication notes. Do not power or program the partial assembly.

Retain manual placement confirmation for the new upload. Historical cart/order records, screenshots and source documents are preserved under `quotations` and the G.4 baseline archive.
