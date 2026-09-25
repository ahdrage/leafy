# Rev G.4 deliverables

These packages belong together. **Quotation/review only until assembler DFM is confirmed.** Earlier Rev F quotations/BOMs do not cover Rev G.

G.4 adds component-side solder-mask tents and coordinated thermal paste at U1/U2. All copper/drills, parts and placements remain identical to G.3. Use the new G.4 fabrication data and matching BOM together. See TENTING-G4-CHANGE.md; G.3 is archived under history. The stencil proposal is 0.125 mm and still needs explicit assembler acceptance.

The unchanged JLCPCB rotations were previously checked against all six G.3 footprints; the G.4 upload must receive its own final preview check. `CPL-FACTORY-JLCPCB.csv` includes the JLC catalogue offsets; do not apply them twice. `placements-FACTORY.csv` and `CPL-NATIVE-REFERENCE-ONLY.csv` retain native KiCad angles. Use `FACTORY-PIN1-REFERENCE.csv` to verify orientation. Manufacturer DFM/production approval and physical testing remain outstanding.

- `leaf-heat-rev-g4-gerbers.zip`: four-layer fabrication data and drill files.
- `leaf-heat-rev-g4-factory-assembly.zip`: Gerbers, exact six-part factory BOM, placements, paste drawing and manufacturing instructions. Factory fits U1/U2/U4/U5/U6/L1 only.
- `leaf-heat-rev-g4-hand-assembly.zip`: 49 hand parts plus one plug-in antenna per board, Mouser list for two boards, diagrams and hand/wiring instructions. The browser cart is verified; the package includes its original export, prices and comparison report.
- `leaf-heat-rev-g4-kicad.zip`: native editable project, local libraries, BOM source and review reports.
- `leaf-heat-rev-g4-review-images.zip`: schematic, top/bottom/inner layers, paste, assembly, back-side values and a magnified Gerber-derived tenting drawing.

The standalone firmware source and Blender/print package are linked from the Rev G README. No purchase or powered hardware validation is implied by exporting these files. SHA-256 manifests record the native board, schematic and packaged files.
