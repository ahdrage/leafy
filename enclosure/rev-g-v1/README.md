# Leaf Rev G enclosure v1

**G.2 compatibility:** the outline, mounting holes, all component/pad positions and 3D models remain unchanged from G.1. The existing case geometry is therefore compatible with G.2; see [the comparison](compatibility-g2.json). Original Blender renders show the earlier copper/silkscreen and retain their original hashes. This does not establish physical fit or environmental qualification.

Updated Blender case for the **100 × 100 mm Rev G PCB**, including the new radial capacitor and supervisor. The case keeps the Rev F dimensions and mounting pattern; its board reference, renders and validation now use Rev G.

- [Editable Blender file](leaf-rev-g-enclosure.blend)
- [Base STL](print/leaf-rev-g-case-base.stl), [lid STL](print/leaf-rev-g-case-lid.stl)
- [Closed view](previews/01-closed-case.png), [open view](previews/02-open-case-with-board.png), [exploded view](previews/03-exploded-case.png)
- [Fit/mesh checks](validation.json), [dimensions](parameters.json), [complete ZIP](leaf-rev-g-enclosure-package.zip)

Outside dimensions are **124.8 × 129.4 × 39.6 mm**. The tall floor standoffs retain access/clearance for the DB9 connector. PCB underside is at 18.4 mm, top at 20 mm and lid underside at 37.2 mm. C15's 11.2 mm body fits with approximately **6 mm vertical clearance**. The DB9/cable opening remains 42 mm wide. Actual cable hood and screwlock projection still need a physical fit test.

Only the supplied STL files are printable. The PCB, parts, screws and nuts in Blender are reference objects. Select `LID ASSEMBLY` and set its Z position to 0 mm to close the model, or 62 mm for the exploded view. Dimensions and STL coordinates are millimetres. Do not scale the parts in the slicer.

Print the base flat down and the supplied lid exterior-face down. Start with a 0.4 mm nozzle, 0.2 mm layers, at least four walls and adequate top/bottom layers. PETG can suit a supervised indoor/cabin fit prototype; select a filament with a documented heat rating appropriate to the final parked-car environment. Plain PLA is unsuitable for assuming hot-car durability. No temperature, flammability, condensation, vibration or weatherproof rating is claimed.

Bought fasteners (not included in the electronic-parts basket): four **unfilled nylon M2.5 × 8 mm screws and M2.5 nuts** for the PCB, and four **M3 × 10 mm screws and M3 nuts** for the lid. Test the actual screws/nuts with `print/OPTIONAL-fastener-fit-test.stl` before printing both case parts. Use `OPTIONAL-connector-fit-test.stl` to check the actual cable hood. Avoid metal PCB fasteners around the ESP32 antenna.

The four native PCB mounting holes align with the posts. Checks find manifold single solids, positive volume, correct millimetre-scale STL bounds, no base/lid intersection and no detected component/case surface collisions. C15 and U5 use conservative dimensional proxies; the DB9 model is based on drawing envelopes. This is digital verification, not proof of printed fit. The H2 support lies within the suggested antenna clearance region, so keep nylon hardware and test Wi-Fi range in the assembled case.

Rebuild with Blender 5.2.1 LTS:

```sh
/Applications/Blender.app/Contents/MacOS/Blender --background --factory-startup --python-exit-code 1 --python enclosure/rev-g-v1/build_enclosure.py
```

The native board hash in `parameters.json`, `reference/board-geometry.json` and `validation.json` must agree with the current Rev G PCB. Rev F enclosure files remain unchanged.

## Rev G.1 compatibility

The U5 BOM substitution uses the same DYY14 package and changes no physical PCB geometry. The existing Blender/STL files remain valid. [Compatibility check](compatibility-g1.json) ties the current PCB hash to the original rendered board through the full native geometry-equivalence audit. Original render/mesh provenance is retained; no new physical fit test is implied.
