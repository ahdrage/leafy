# Rev G.3 deliverables

These packages belong together. **Quotation/review only until assembler DFM is confirmed.** Earlier Rev F quotations/BOMs do not cover Rev G.

G.3 changes U2 to ESP32-C3-WROOM-02U-N4 / C2926676 and adds the customer-fitted Molex 1461530300 antenna. All electrical geometry is retained from G.2. Use the new BOM and G.3 fabrication data together. See ANTENNA-G3-CHANGE.md; older G.2 files are archived under history.

The JLCPCB preview rotations were corrected and checked against all six footprints. `CPL-FACTORY-JLCPCB.csv` includes the JLC catalogue offsets; do not apply them twice. `placements-FACTORY.csv` and `CPL-NATIVE-REFERENCE-ONLY.csv` retain native KiCad angles. Use `FACTORY-PIN1-REFERENCE.csv` to verify orientation. Manufacturer DFM/production approval and physical testing remain outstanding.

- `leaf-heat-rev-g3-gerbers.zip`: four-layer fabrication data and drill files.
- `leaf-heat-rev-g3-factory-assembly.zip`: Gerbers, exact six-part factory BOM, placements, paste drawing and manufacturing instructions. Factory fits U1/U2/U4/U5/U6/L1 only.
- `leaf-heat-rev-g3-hand-assembly.zip`: 49 hand parts plus one plug-in antenna per board, Mouser list for two boards, diagrams and hand/wiring instructions. The browser cart is verified; the package includes its original export, prices and comparison report.
- `leaf-heat-rev-g3-kicad.zip`: native editable project, local libraries, BOM source and review reports.
- `leaf-heat-rev-g3-review-images.zip`: schematic, top/bottom/inner layers, paste, assembly and back-side values.

The standalone firmware source and Blender/print package are linked from the Rev G README. No purchase or powered hardware validation is implied by exporting these files. SHA-256 manifests record the native board, schematic and packaged files.
