> Leafy G.5 compatibility: board outline, mounting holes, connector positions and component bodies are unchanged. See [compatibility record](compatibility-g5.json). Existing enclosure renders show G.3 artwork; the PCB now says Leafy.

# Leaf Rev G.3 enclosure v2

Updated Blender case for the **100 × 100 mm Rev G.3 PCB**, including the new radial capacitor and supervisor. The case keeps the existing dimensions and mounting pattern, adds a 2.2 mm drop-in antenna-cable exit with matching lid-lip relief and a rounded internal tie saddle. The board reference and renders show the new 02U module.

- [Editable Blender file](leaf-rev-g-enclosure.blend)
- [Base STL](print/leaf-rev-g-case-base.stl), [lid STL](print/leaf-rev-g-case-lid.stl)
- [Closed view](previews/01-closed-case.png), [open view](previews/02-open-case-with-board.png), [exploded view](previews/03-exploded-case.png)
- [Fit/mesh checks](validation.json), [dimensions](parameters.json), [complete ZIP](leaf-rev-g-enclosure-package.zip)

Outside dimensions are **124.8 × 129.4 × 39.6 mm**. The tall floor standoffs retain access/clearance for the DB9 connector. PCB underside is at 18.4 mm, top at 20 mm and lid underside at 37.2 mm. C15's 11.2 mm body fits with approximately **6 mm vertical clearance**. The DB9/cable opening remains 42 mm wide. Actual cable hood and screwlock projection still need a physical fit test.

Only the supplied STL files are printable. The PCB, parts, screws and nuts in Blender are reference objects. Select `LID ASSEMBLY` and set its Z position to 0 mm to close the model, or 62 mm for the exploded view. Dimensions and STL coordinates are millimetres. Do not scale the parts in the slicer.

Print the base flat down and the supplied lid exterior-face down. Start with a 0.4 mm nozzle, 0.2 mm layers, at least four walls and adequate top/bottom layers. PETG can suit a supervised indoor/cabin fit prototype; select a filament with a documented heat rating appropriate to the final parked-car environment. Plain PLA is unsuitable for assuming hot-car durability. No temperature, flammability, condensation, vibration or weatherproof rating is claimed.

Bought fasteners (not included in the electronic-parts basket): four **unfilled nylon M2.5 × 8 mm screws and M2.5 nuts** for the PCB, and four **M3 × 10 mm screws and M3 nuts** for the lid. Test the actual screws/nuts with `print/OPTIONAL-fastener-fit-test.stl` before printing both case parts. Use `OPTIONAL-connector-fit-test.stl` to check the actual cable hood. Also supply one small 2.5 mm nylon cable tie per case; ordinary mechanical/soldering supplies remain outside the electronics basket.

The four native PCB mounting holes align with the posts. Checks find manifold single solids, positive volume, correct millimetre-scale STL bounds, no base/lid intersection and no detected component/case surface collisions. C15 and U5 use conservative dimensional proxies; the DB9 model is based on drawing envelopes. This is digital verification, not proof of printed fit. The antenna now mounts outside the casing. Test Wi-Fi range in the actual car; the empty socket shown in the render needs ANT1 attached before radio use.

Rebuild with Blender 5.2.1 LTS:

```sh
/Applications/Blender.app/Contents/MacOS/Blender --background --factory-startup --python-exit-code 1 --python enclosure/rev-g-v2/build_enclosure.py
```

The native board hash in `parameters.json`, `reference/board-geometry.json` and `validation.json` must agree with the current Rev G.3 PCB. Rev F enclosure files remain unchanged.


## Antenna cable assembly

Fit the 300 mm Molex 1461530300 with the lid removed and power disconnected. Press its MHF I / U.FL plug squarely onto U2. Leave a slack loop, then route the coax over the rounded saddle and into the drop-in notch. Pass a 2.5 mm nylon tie through the saddle slot and around the cable; retain it gently without crushing the 1.13 mm coax. Smooth printed edges. Check that the cable can rest in the exit without being pinched when the lid closes, and that a light external pull is taken by the saddle/tie, not U2. Stop and correct fit if either check fails. No specified pull strength is claimed.

Mount the flex antenna inside the car on suitable plastic away from metal; the antenna is outside this box, not outside the vehicle. The entire lead is 300 mm, including routing inside the case. Keep bend radii generous and avoid tension or tight folds. The casing is not waterproof.

## G.4 compatibility

The G.4 revision changes U1/U2 solder mask and paste only. All mounting/outline/component geometry remains unchanged and the enclosure is compatible; see [the verification record](compatibility-g4.json). Existing 3D files and renders retain G.3 provenance and have not been relabelled as G.4 renders.
