# Rev G sources and reproducibility

Use the supplied native KiCad files and matched ZIPs for this checked revision. They are the authoritative reviewed artifacts; scripts are engineering generators, not a one-click production release system.

Generation sequence:

1. `build_rev_g.py` copies the preserved Rev F source, adds the new circuitry and critical regulator routes.
2. `route_rev_g.py` adds plane fanouts. `prepare_router.py` prepares the external-router DSN. The local Freerouting session is in `exports/leaf-heat-v7.ses`; it was imported using KiCad's native `ImportSpecctraSES` function.
3. `finish_rev_g.py` completes the fine-pitch escapes. `finalize_values.py` applies the final precision resistors, 10 µF delay caps, taped C15 ordering part, and all 27 hand-parts rows on the back. Do not use the builder's intermediate values as the BOM.
4. Run native schematic netlist export/ERC and PCB DRC with copper refill, save-board and schematic parity. Run `audit_rev_g.py`, `analyze_protection.py` and `export_rev_g.py` with the KiCad Python runtime. The audit reads both native revisions; it does not modify them.
5. `make_shopping_list.py` regenerates the final target quantities. Live basket availability/prices are a separate verification step and cannot be inferred from this script.
6. `package_rev_g.py` checks native hashes against the audit and packages the final Gerbers, BOMs, placements and review files. If any native file changes, regenerate all dependent exports, audits and packages.

Python runtime: `tools/KiCAD-MCP-Server/venv/bin/python3`, with KiCad 10.0.6. CLI: `/Applications/KiCad/KiCad.app/Contents/MacOS/kicad-cli`. Set `FONTCONFIG_FILE` to the repository's `hardware/fontconfig.xml`. The Freerouting jar/JRE are under `tools/freerouting`; router results may vary by runtime/version and must receive a fresh native DRC after import.

Rev G.1 is a targeted metadata-only U5 substitution. `apply_u5_g1.py` is a one-time migration that archives the preceding release; do not rerun it. `audit_u5_g1.py` proves full parsed native equivalence after the exact identity/datasheet change and verifies the unchanged hand BOM and native placement CSV, and the explicit JLC catalogue rotation offsets. Run it after exports and include its report in the packages. The builder also now specifies the new U5.

The enclosure has separate geometry/hash checks described in its README. Physical PCB changes require refreshing its GLB reference and native geometry hash before rebuilding the Blender model. For G.1, the complete geometry-equivalence audit permits reuse of the original model, recorded in `enclosure/rev-g-v1/compatibility-g1.json`; original render provenance is retained. Firmware has its own pinned build configuration and host tests.

Historical intermediates and logs under `exports/` are retained for investigation. Only the five ZIPs listed in `deliverables/README.md` are the current board handoff packages. No assembler DFM approval or physical qualification is implied by reproducibility or matching hashes.

## G.2 layout and silkscreen update

`history/rev-g1-before-adi-g2.zip` preserves the complete pre-change source and outputs. `apply_adi_g2.py` applies the approved edits to that exact G.1 PCB only. The native files include the G.2 changes and subsequent G.3 antenna overlay; do not rerun historical migrations.

For the historical G.2 build only: export the schematic XML netlist, run ERC, and run KiCad PCB DRC with `--refill-zones --save-board --all-track-errors --schematic-parity --severity-all`. Keep the 1.0 mm text / 0.15 mm stroke / 0.15 mm silk-clearance rules. On this Mac the refill/save operation needs access to macOS display services; the sandbox-only run can abort. Then run `export_rev_g.py`, `export_pin1_reference.py`, `audit_rev_g.py`, `audit_adi_g2.py`, and `package_rev_g.py` in that order. The G.2 packager wrote `rev-g2` names; those outputs are now archived. Use the G.3 process below for current files. The historical `audit_u5_g1.py` compares G.1 only and is not the current layout audit.

G.2 geometry compatibility with the existing enclosure is recorded in `enclosure/rev-g-v1/compatibility-g2.json`. Do not overwrite the original render hashes with a new board hash without rebuilding the reference.

## G.3 antenna update

`apply_antenna_g3.py` is a one-time overlay for the exact archived G.2 PCB, not a general rebuild command. Current native files already include it. Use `export_rev_g.py`, `make_shopping_list.py`, fresh ERC/netlist/DRC with refill, `audit_rev_g.py`, `audit_antenna_g3.py`, and `export_pin1_reference.py` for current exports/checks. `audit_adi_g2.py` remains a historical G.2 audit and must not be relabelled as a G.3 check. `package_rev_g.py` requires current G.3 audit hashes. Rebuild the new enclosure under `enclosure/rev-g-v2` from the current PCB GLB.

## G.4 top-side tenting update

`apply_tenting_g4.py` is the one-time overlay against the immutable `history/rev-g3-before-tenting.zip` G.3 baseline. Current files already include it. Do not rerun historical migrations. Run fresh ERC/netlist and PCB DRC with refill/save/parity, then `export_rev_g.py`, `export_pin1_reference.py`, `audit_rev_g.py`, `audit_tenting_g4.py` and `package_rev_g.py`. The current packager requires the G.4 audit hashes. `audit_antenna_g3.py` is now historical. Do not overwrite its old report as if it checked G.4.

The Gerber audit uses gerbonara 0.13.0, shapely 2.0.7 and NumPy 1.26.4 installed in the repository's KiCad Python environment. It parses final positive mask/paste Gerbers independently, evaluates hole coverage/open bottom ends and stencil area, compares native geometry and electrical fabrication plots against G.3, and makes the enlarged review drawing. The supply basket is unchanged and must not be regenerated with its live extras removed. Firmware and enclosure geometry are unaffected; see the enclosure's G.4 compatibility record.

## Current G.5 release

`history/rev-g4-before-filled-g5.zip` preserves the G.4 input with verified per-file hashes. `apply_filled_g5.py` is a one-time mask/process/branding migration; do not rerun it on the already revised PCB. The audit was run before the migration and failed on the G.4 mask tents, then passed after the change. No copper/drill/part/placement changes are permitted by this revision.

For current outputs: fresh netlist/ERC and DRC with refill/save/parity; `export_fill_g5.py`; `export_rev_g.py`; `export_pin1_reference.py`; `audit_rev_g.py`; `audit_filled_g5.py`; then `package_rev_g.py`. All commands use the KiCad Python environment above. The new packager requires G.5 audit hashes. Older G.1–G.4 audits/migrations are historical only. `verify_mouser_export.py` is a historical live-cart script: do not run it to overwrite the received-parts basket with obsolete assumptions.
