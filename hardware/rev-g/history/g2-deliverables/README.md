# Rev G.2 deliverables

These packages belong together. **Quotation/review only until assembler DFM is confirmed.** Earlier Rev F quotations/BOMs do not cover Rev G.

G.2 applies Adi's routing and silkscreen review. Two vias move and copper/silkscreen change; replace the G.1 fabrication upload before ordering. BOM and component positions are unchanged. U5 remains TPS3760A012DYYR / C5218894; see `U5-G1-CHANGE.md` for its accepted qualification limits and `ADI-G2-CHANGES.md` for this revision.

The JLCPCB preview rotations were corrected and checked against all six footprints. `CPL-FACTORY-JLCPCB.csv` includes the JLC catalogue offsets; do not apply them twice. `placements-FACTORY.csv` and `CPL-NATIVE-REFERENCE-ONLY.csv` retain native KiCad angles. Use `FACTORY-PIN1-REFERENCE.csv` to verify orientation. Manufacturer DFM/production approval and physical testing remain outstanding.

- `leaf-heat-rev-g2-gerbers.zip`: four-layer fabrication data and drill files.
- `leaf-heat-rev-g2-factory-assembly.zip`: Gerbers, exact six-part factory BOM, placements, paste drawing and manufacturing instructions. Factory fits U1/U2/U4/U5/U6/L1 only.
- `leaf-heat-rev-g2-hand-assembly.zip`: 49 hand parts per board, Mouser list for two boards, diagrams and hand/wiring instructions. The browser cart is verified; the package includes its original export, prices and comparison report.
- `leaf-heat-rev-g2-kicad.zip`: native editable project, local libraries, BOM source and review reports.
- `leaf-heat-rev-g2-review-images.zip`: schematic, top/bottom/inner layers, paste, assembly and back-side values.

The standalone firmware source and Blender/print package are linked from the Rev G README. No purchase or powered hardware validation is implied by exporting these files. SHA-256 manifests record the native board, schematic and packaged files.
