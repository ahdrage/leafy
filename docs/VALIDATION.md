# Validation status — 25 September 2026

**Manufacturing files reviewed; physical prototype not yet validated.**

| Area | Evidence / status |
| --- | --- |
| CAD | Saved G.5 ERC/DRC: zero reported violations, unconnected items or schematic mismatches under configured rules, with refill/parity checks |
| Native audits | 55 components, pin/net mapping, factory scope and fabrication output comparisons |
| G.5 compatibility | Copper, nets, drills, placements, BOM and mechanical geometry unchanged from G.4; mask/process/branding changed |
| PCB CAM | Original drill locations, connectivity, continuous thermal-pad mask openings, all 18 fill locations including 0.33 mm, temporary rails reviewed |
| Final placement | Six exact MPNs, centres, lead alignment and pin-one directions checked in final viewer; two top-side partial assemblies |
| Firmware | Recorded ESP32-C3 build; 25 behavioral host tests; no physical device execution claimed |
| Enclosure | Mesh/geometry checks and G.5 compatibility; no printed fit/environmental test claimed |
| Physical operation | Supply/transients, parked current, RF, CAN and heater operation **not yet tested** |

See [design review](../hardware/rev-g/DESIGN-REVIEW.md) and [firmware fixes](../firmware/leaf-heat/verification/REVIEW-FIXES.md). Reports identify exact inputs; changes require relevant checks again. A zero CAD report is not proof of reliability.

## Next milestones

1. Inspect incoming factory joints and thermal-pad work; finish hand assembly, check orientation/bridges/rail resistance.
2. Current-limited first power, vehicle disconnected. Measure 3.3 V regulation, startup, ripple and Wi-Fi bursts; check input hot-plug behavior with suitable instruments.
3. Measure cutoff/recovery thresholds and delays at VPWR and the input. Calibrate ADC; measure shutdown, connected and router-loss current.
4. At least 24-hour Wi-Fi test with router restart, DHCP renewal and weak signal; check actual antenna location.
5. Correctly terminated two-node CAN bench test: reset/standby, arbitration, missing ACK, bus-off and pending-frame cancellation.
6. Confirm actual model/TCU and unplugged cable continuity. Enable CAN only after bench checks, then observe On/Off, timeout, repeated sessions and network loss beside the car.
7. Verify the vehicle's own timeout and consequences of board power loss; do not infer success from frame transmission.
8. Check printed case, cable fit, antenna strain relief and intended environmental conditions.

Record test date, hardware revision, firmware commit/non-secret settings, instruments, wiring, supply/temperature, expected/measured results and pass/fail. Save traces/photos without private identifiers.

No ISO 7637/16750, EMC, completed-device radio, ingress or automotive qualification is claimed.
