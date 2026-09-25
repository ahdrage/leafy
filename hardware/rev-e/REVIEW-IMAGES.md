# Rev E image guide

This is the 100 × 100 mm, four-layer hand-solder prototype. Factory scope is U1/U2/U4/L1 only; the completed board needs another 37 hand-fitted parts.

| Image | What it shows |
| --- | --- |
| board-3d.png | Intended completed assembly. The fuse body model is missing and the DB9 model is approximate. |
| assembly-map.png / .svg | Top-side pad positions and references; orange identifies the four factory components. Pad shapes are simplified for this ownership map. |
| placement.png / .svg | Native KiCad component body outlines and references; use with the BOM and hand guide. |
| top.png / .svg | Top copper and printed labels. White gaps around traces separate them from the ground pour. Traces beneath printed text are covered by solder mask. |
| ground.png / .svg | In1.Cu ground reference plane. Clear rings isolate pads/vias belonging to other nets. |
| power.png / .svg | In2.Cu supply distribution: protected-input region at the left and a diagonal branch to the battery-sense resistor, with 3.3 V and ground elsewhere. Different nets use the same layer colour. |
| bottom.png / .svg | Bottom copper and ground pour, shown from above for alignment with the other copper views. |
| factory-paste.png / .svg | Native stencil-layer preview. Only four component sites have paste. Black drill markers are holes in the preview, not extra stencil openings; the paste Gerber is the manufacturing authority. |
| back-legend.png / .svg | Hand-parts value table printed on the bottom, viewed from the bottom so the text reads normally. |
| schematic.png / .svg | Complete circuit. Zoom the vector SVG or the supplied schematic PDF for detail. |

The dedicated ground reference, plane priorities, four-layer antenna keepout and hand-pad thermal reliefs are recorded in the native PCB. Electrical, layout, connectivity and schematic parity checks reported zero issues. Refer to `DESIGN-REVIEW.md` for the exact checks and the remaining physical tests; these images do not establish working heater firmware or automotive qualification.
