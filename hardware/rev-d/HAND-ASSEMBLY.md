# Rev D — hand-assembly guide

The factory fits **U1, U2, U4 and L1**. Fit the remaining **37 parts** using `BOM-HAND.csv` and the assembly map. Every component mounts on the top. Only through-hole solder joints are made from the underside.

This is still an SMD project. The larger 1206 resistors/capacitors are 3.2 × 1.6 mm, with pads extending beyond their ends. U3 and D4 remain the hardest hand-fitted parts, but both have visible leads and extended pads. Practise with spare 1206 parts and a spare SOIC/SOT-23 board first.

## Equipment

A temperature-controlled iron with a small chisel tip, fine electronics solder, electronics flux, tweezers, magnifier, solder wick, board holder and multimeter are appropriate. Use ventilation and eye protection when clipping leads. Avoid plumbing/acid flux. Extra resistors and capacitors are inexpensive insurance against losing a part.

Use a short, controlled heating time following the component maker's hand-solder guidance. Heat the pad and terminal together. More pressure or prolonged heating is not a substitute for a clean, correctly sized tip. In particular, do not thermally shock ceramic capacitors or lever components against the board. Let a stubborn joint cool before another attempt. A ground pad may take slightly longer because it connects to a plane.

For each two-terminal SMD component: apply flux, lightly tin one pad, hold the component with tweezers, reheat that pad and slide the part into alignment. Let it cool, then solder the other end. Inspect both ends. Do not bridge the gap underneath with solder.

## Parts and orientation

| Parts | Orientation/check |
| --- | --- |
| R1–R10, R18–R20 | Resistors are not polarized. Check the value with the list/meter before fitting; R2 is **43.2 kΩ**, not 43 kΩ or 47 kΩ. |
| C1–C14 | Ceramic capacitors are not polarized. Their values usually are not printed. Keep each value in its labelled bag. C1/C2 need **100 V** ratings. |
| F1 | 1 A fuse; either orientation. Never bridge it with wire or solder. |
| D1 | Polarized Schottky diode. Package cathode band goes to pad 1 / board cathode line / VPWR. |
| D3 | SMBJ24CA is bidirectional; either orientation. Do not substitute the unidirectional SMBJ24A without review. |
| D6 | Green LED. Match the package cathode marking to **K** / pad 1 on the PCB. |
| U3 | TCAN3403DRQ1 SOIC-8. Align pin 1 with the board's pin-1 marker; inspect all eight leads for bridges. |
| D4 | PESD2CAN,215. Three-pin SOT-23; match the two-lead side and single-lead side to the footprint. Pin 3 is GND. |
| SW1/SW2 | Omron B3F-1000, four through-hole legs. Legs come in electrically common pairs; verify the unpressed switch does not short its two contact groups. |
| J1 | Exact NorComp 182-009-113R531, male DB9. Solder nine pins and both shell anchors. The anchors need more heat. |
| J3 | Three-pin header. Square PCB pad is pin 1, GND; the board labels read GND / RX / TX. |

There is **no component** to fit at TP1–TP7; these are bare test holes.

## Assembly sequence

1. Inspect the delivered board and factory-fitted parts. Confirm U1, U2, U4 and L1 are fitted correctly and no hand positions were populated unexpectedly. Obtain the factory's exposed-pad inspection result where available.
2. With power and programmer disconnected, fit the low SMD parts: resistors, capacitors, fuse, diodes and LED. Work one value at a time, checking each reference against the parts list. The regulator's nearby parts must sit directly on their pads; do not extend them on wires.
3. Fit U3 and D4. Tack one corner lead, align, then solder the remaining visible leads using flux. Inspect for bridges under magnification; use solder wick to remove excess.
4. Fit the through-hole buttons, then J3 and J1. Keep the parts seated and solder every intended terminal. Fit the buttons after any cleaning because B3F-1000 switches are not washable.
5. Inspect every hand joint and compare the completed board against the full assembly map. Check polarity and resistance/capacitance values again. Check that the two button contact groups are open when unpressed and close only while pressed.
6. With all supplies disconnected, check for accidental shorts between GND and CAR_12V, VPWR and 3V3, and between adjacent U3 leads. Capacitors can briefly look like low resistance while charging from a meter; a continuity beep alone is not a complete diagnosis.

## First power and programming

Complete all hand assembly before power: the factory's four components alone do not make a working regulator. Keep the vehicle disconnected.

Use a regulated **12 V bench supply with current limiting**, connected through J1 pin 9 (+) and pin 3 (GND). Verify these pins by continuity to the labelled test points, not by counting the mating face from memory. Start with ESP_EN held low through TP7 to TP1/GND. Begin with a low current limit and watch the supply; stop if current stays unexpectedly high or a part heats. Current-limit settings and startup behaviour need bench qualification, so do not repeatedly increase the limit to force a faulted board to start.

Measure CAR_12V, VPWR and 3V3 relative to TP1. The protected input is below the input supply by D1's forward drop. The expected nominal output is about **3.315 V**; investigate a stable reading outside approximately **3.22–3.41 V** before releasing reset. These bounds are static component-tolerance calculations, not a substitute for checking ripple/startup with an oscilloscope.

Release the EN short only after the rail is verified. A radio startup can draw more current than the reset-held state, so use the measured behaviour to set a suitable limit. Check the supply under radio activity before any car connection.

Program using a **3.3 V logic UART adapter** and the separate 12 V supply; J3 provides no power. Adapter TX goes to board RX, adapter RX to board TX, and grounds connect. Insulate the adapter's power lead. Hold BOOT, press/release RESET, then release BOOT to enter download mode. Firmware offsets and build instructions must come from the actual firmware project; no heater firmware is supplied here. See `PROGRAMMING.md`.

## Test-point map

| Ref | Net | Purpose |
| --- | --- | --- |
| TP1 | GND | Meter/bench ground |
| TP2 | CAR_12V | Incoming power, before fuse |
| TP3 | VPWR | Protected supply after fuse and diode |
| TP4 | 3V3 | Regulated output |
| TP5 | CAN_H | CAN high measurement; avoid accidental shorts |
| TP6 | CAN_L | CAN low measurement; avoid accidental shorts |
| TP7 | ESP_EN | Reset/enable; pull to GND to hold the radio in reset |

The first vehicle connection still requires verification of the exact Nissan cable, safe firmware behaviour, CAN standby, low-battery handling and parked current. The board itself has no automatic hardware battery disconnect.
