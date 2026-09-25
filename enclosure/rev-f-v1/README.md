# Leaf Heat — Rev F enclosure v1

A two-piece, screw-fastened enclosure for the **100 × 100 × 1.6 mm Rev F board**. It has four PCB supports, four separate lid fasteners, a drop-in opening for the DB9 car connector, a small status-LED viewing hole and a locating lip on the lid. Remove the lid for programming, BOOT/RESET and hand-solder access. The PCB design is unchanged.

The outside dimensions are **124.8 × 129.4 × 39.6 mm**, excluding screw heads and the projecting connector. The extra height and rear space keep the main shell away from the Wi-Fi antenna. This is a first-print prototype, not a physically verified or sealed vehicle enclosure.

## Files

- [Editable Blender model](leaf-rev-f-enclosure.blend): opens in an exploded view, with the actual KiCad board model inside. PCB and bought fasteners are separate reference collections.
- [Base STL](print/leaf-rev-f-case-base.stl) and [lid STL](print/leaf-rev-f-case-lid.stl): the two parts to print.
- [Fastener fit test](print/OPTIONAL-fastener-fit-test.stl): sample posts with the same screw bores and side-loading nut pockets as the enclosure.
- [Connector fit test](print/OPTIONAL-connector-fit-test.stl): a flat U-shaped gauge matching the opening width and height.
- [Closed case](previews/01-closed-case.png), [open case with PCB](previews/02-open-case-with-board.png), [exploded view](previews/03-exploded-case.png) and [empty base](previews/04-empty-base.png).
- [Dimensions and clearances](parameters.json), [mesh and fit-check results](validation.json), and [complete enclosure package](leaf-rev-f-enclosure-package.zip).

The STL coordinates are **millimetres**, already oriented on the print bed. Import at 100%; the base should measure 124.8 × 129.4 × 37.2 mm. The lid print includes a 1.6 mm lip and is 4.0 mm high. Do not export the whole Blender scene for printing: it includes the PCB, screws and studio objects.

## Printing

Print one base and one lid. A reasonable starting profile is a 0.4 mm nozzle, 0.2 mm layers, four perimeters, at least five solid top/bottom layers, and 20–30% infill. Inspect the slicer preview around the horizontal nut-pocket roofs. They require short bridges; no large support structures are designed into the case. A brim may help with corner lifting.

Use **plain, unfilled ASA** as the intended vehicle-case material, provided the printer/service can control warping. PETG is a practical material for the first fit test. These are material choices, not a temperature qualification of this printed part. Prusa describes ASA's higher temperature/UV resistance and recommends an enclosed printing environment; its [material guide](https://help.prusa3d.com/filament-material-guide) and [ASA guidance](https://help.prusa3d.com/article/asa_1809) explain the printing tradeoffs. Validate the finished case at the intended mounting location and operating temperature.

Print the inexpensive fit tests first. Verify the nuts slide into their pockets, the screws turn freely through the bores, and the actual DB9 connector/cable hood fit the gauge. Printer shrinkage, layer seams and hardware dimensions vary. Adjust the named clearances in `parameters.json` and regenerate rather than scaling the whole enclosure; scaling would also move the PCB holes.

## Extra hardware to buy

These fasteners are **not included in the existing Mouser electronics basket**.

| Quantity | Part | Location |
| ---: | --- | --- |
| 4 | M2.5 × 8 mm pan/button-head screws, unfilled nylon | PCB mounting |
| 4 | M2.5 nylon hex nuts, nominal 5.0 mm across flats and 2.0 mm thick | PCB-post pockets |
| 4 | M3 × 10 mm pan/button-head machine screws | Lid |
| 4 | M3 hex nuts, nominal 5.5 mm across flats and 2.4 mm thick | Lid-post pockets |

Screw length is measured under the head. Use ordinary hex nuts, not tall locknuts. Check actual dimensions with the fit coupon: the M2.5 pockets are 5.5 mm across flats × 2.5 mm high, and the M3 pockets are 5.9 mm across flats × 2.8 mm high. No tapped plastic threads or heat-set inserts are required. PCB screw holes in the actual board are 2.7 mm; do not substitute M3 screws through them.

## Assembly

1. Clean loose print material from the holes and nut pockets. Slide four M2.5 nuts into the shorter PCB posts and four M3 nuts into the taller lid posts. All pockets open toward the interior. Check them before fitting the PCB.
2. With power disconnected, lower the fully assembled board into the base. The car connector drops into the open-topped front cutout; its mounting screws remain accessible outside. The underside sits 16 mm above the inside floor, leaving room for solder tails.
3. Fit the four M2.5 × 8 nylon screws through the PCB holes. Tighten gently into the captured nuts; do not bend the board or crush the printed supports.
4. Check connector mating and screwlock engagement with the actual cable. The opening is intentionally wider than the metal connector to allow room for its mating hood. Do not pull the cable into alignment by tightening its screws.
5. Place the lid onto its locating lip and fit the four M3 × 10 screws. The nominal lip clearance is 0.35 mm per side. Check the lid seats without force.
6. Verify Wi-Fi range with the case closed and check board temperature during operation. The cable opening and LED hole are unsealed: there is no IP rating or waterproof claim.

## Geometry and remaining fit checks

The board mounting coordinates come directly from the native Rev F PCB: **(4,4), (96,4), (45,96), (96,96) mm**, measured right/down from its upper-left corner. Blender maps these to X/right, Y/up, with the same four holes. The two front PCB holes are intentionally asymmetric; they must not be replaced with a guessed rectangular pattern.

The front opening is **42.0 mm wide × 21.7 mm high**, centred on J1 at PCB X = 21.54 mm. NorComp's [182-series drawing](https://content.norcomp.net/rohspdfs/Connectors/18Y/182/182-yyy-113Ryy1.pdf) is the connector dimensional authority. The inherited KiCad DB9 model is approximate, so it is replaced in the Blender presentation by drawing-based envelope geometry. The female screwlock projection is assumed to be 5 mm for visualization; the actual screwlock and cable hood must be checked physically. The opening is not a panel clamp or cable strain-relief fixture.

The main shell provides approximately **17.9 mm behind, 28 mm to the right, 17.5 mm below and 16.2 mm above** the conservative antenna envelope. [Espressif recommends at least 15 mm housing clearance around the antenna and testing the final product's range](https://docs.espressif.com/projects/esp-hardware-design-guidelines/en/latest/esp32c3/pcb-layout-design.html). **The existing H2 mounting position is an exception:** its nylon PCB support/fastener is closer than 15 mm. This is why the board fasteners are specified as unfilled nylon. That choice does not prove zero RF impact; compare open/closed-case Wi-Fi performance. The lid's metal fasteners are outside the antenna clearance region.

The model checks cover closed printable meshes, separate connected solids, positive volume, base/lid interference, surface collisions with component references, native mounting-hole positions and the actual millimetre dimensions in each exported STL. Intentional PCB-to-support contact is excluded from the component-surface check. F1 is represented by a conservative envelope because the KiCad library lacks its body model. Existing capacitor body models are approximate; the available top clearance is much larger than their small height variation.

These checks cannot verify actual printer tolerances, the cable's hood shape, RF range, heat, vibration, flammability or long-term screw retention. The hardware remains an untested prototype and still needs its separate firmware and electrical bring-up.

## Reopening and regeneration

The installed **Blender 5.2.1 LTS** includes its own command-line interface and Python API. No MCP server, add-on or extra CLI installation was needed. The project uses ordinary Blender meshes, materials and collections.

In the saved Blender file the lid is raised 62 mm for inspection. Select **LID ASSEMBLY** in the Outliner and set its Location Z to **0 mm** to close the lid and move its screws together; set it to **62 mm** for the exploded view. The `03 REFERENCE` collection contains the bought fasteners; the STL files already contain only their intended printable parts.

To regenerate after editing `parameters.json`, run:

```sh
/Applications/Blender.app/Contents/MacOS/Blender --background --factory-startup --python-exit-code 1 --python /Users/alf/repos/leaf/enclosure/rev-f-v1/build_enclosure.py
```

The saved board geometry and GLB are tied to the Rev F PCB hash in `validation.json`. Regeneration checks that the requested mounting points match the saved native geometry. If the PCB is revised, re-export both references and review the fit before reusing the case.
