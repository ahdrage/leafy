# Development history

This records engineering decisions and outcomes, not private conversations. Earlier documents retain their historical context and must not be used as G.5 manufacturing instructions.

| Stage | Change and reason |
| --- | --- |
| Research | Compared complete OVMS, 4G modules and custom approaches; established that the vehicle integration is more than a modem |
| Narrowed scope | Home Wi-Fi, climate On/Off only, because Wi-Fi reaches the parking location |
| A | Initial compact two-layer custom board with USB programming |
| B | Four-layer placement/plane/routing revision after layout review |
| C | Replaced USB-C/power with three-pin UART to reduce complexity/cost; separate programmer and supply required |
| D | 150 × 150 mm board, larger passives and accessible pads; four difficult parts factory fitted |
| E | 100 × 100 mm, more useful hand-solder spacing; corrected D1 purchasing code |
| F | Mouser-compatible CAN chip, DB9 and output capacitors; U3 pin 5 changed to ground for TCAN3404 |
| G | RC input damping, independent battery cutoff, powered-off ADC isolation, closer regulator components and different buttons |
| G.1 | Stocked TPS3760A012DYYR supervisor; documented the lost automotive qualification/earlier overvoltage allowance |
| G.2 | Routing and silkscreen cleanup after Adi's review |
| Firmware review | Fixed low-battery protection re-arming, bounded normal CAN retries and transceiver startup timing; expanded to 25 host tests |
| G.3 | External-antenna module, Molex antenna and enclosure cable exit/strain relief; GPIOs unchanged |
| G.4 | Explicit top-side mask tents and custom paste discussion to address thermal-hole solder wicking |
| G.5 | Epoxy-filled/planarized/copper-capped thermal holes, normal library stencil, Standard PCBA and Leafy branding |

## Manufacturing decisions

The final factory scope is **U1/U2/U4/U5/U6/L1**, with 49 other components per board hand-fitted. U3 and D4 still need careful soldering; this is not a through-hole-only beginner kit.

Selecting “Tented” in a quote did not by itself cover holes represented as through-hole pads. G.4 defined mask coverage explicitly, but the supplier could not guarantee the large one-sided tents and warned about ink entering the holes and solder wicking.

G.5 instead requires filling and copper capping **all 18 thermal holes: six 0.33 mm at U1, twelve 0.30 mm at U2**. The 0.33 mm exception must be explicit. Component, test and mounting holes stay open; solid thermal copper connections are intentional.

We removed the exact 0.125 mm stencil and exact-aperture requirements. G.5 accepts JLC's normal component-library stencil engineering, with Special stencil = No. The order uses Standard PCBA. Old tenting, mask-cap-survival and exact-stencil instructions are superseded.

## Review reached on 25 September 2026

Processed PCB artwork was compared with G.5: original drill locations, copper connectivity, continuous thermal-pad mask openings, all eighteen fill locations and temporary rails. The CAM record explicitly included the 0.33 mm holes. Finished size remains 100 × 100 mm after rail removal.

The final engineer-adjusted assembly viewer was reviewed separately. All six exact parts, centres and pin-one directions matched. A uniform +5 mm Y translation corresponds to the panel rail, not a relative placement error. The order specifies two partial assemblies out of five fabricated boards. The owner confirmed the PCB file; the assistant left final assembly approval to the owner after reviewing it.

At that September review, delivery, first power-up and heater operation had not been demonstrated. The later commissioning result is recorded below; hidden solder-joint quality and RF range remain unqualified.

## Deferred work and constraints

**15 November update:** the assembled G.5 unit has passed supervised manual climate On/Off with the charging cable connected. Firmware gained receive-only diagnostics, per-tab key saving, explicit HTTP outcomes and a fix for browser button-handler shadowing. Bench cutoff/recovery observations and 41 passing host checks plus real-browser regression are recorded in the [commissioning log](COMMISSIONING-2026-11-15.md). No CAD/BOM revision was made. Unplugged climate operation, timers and long-term qualification remain open.

No common-mode choke was added; this does not establish EMC performance. Low-battery protection takes precedence over Wi-Fi availability. G.5 preserves the already received Mouser part identities. Printed case fit, antenna range, supply transients, hardware CAN fault behaviour and longer vehicle testing remain outstanding; initial supply, Wi-Fi, reception and plugged-in On/Off results are now recorded.

Detailed G.1–G.5 change notes, earlier CAD and firmware review records are preserved. See [validation](VALIDATION.md) for the remaining physical work.

## 16 November: unplugged heating and live battery display

- The owner reported Heat On working without the charging cable. Unplugged Heat Off was not separately recorded.
- A home-network API bridge and Swift client were implemented and tested (23 server checks, Swift typechecking), then API/iOS work was paused to focus on the existing website. No complete iOS app or end-to-end vehicle API test is claimed.
- The first website update installed passive BMS sampling and an automatic Off-request countdown. After READY was confirmed it received 94.2% BMS SOC; the owner reported 97% on the instrument panel. These are different vehicle signals, so the difference alone was not a decoder fault.
- A follow-up added dashboard SOC alongside BMS SOC on the same EV-CAN connection. The latest verified flash received 95% dashboard / 92.5% BMS, each aged 26 seconds, at protected supply 13.70 V with reader/command errors 0. The owner confirmed that the display looks good; a simultaneous exact numerical instrument comparison was not separately logged.
- Both signals have independent age/unknown/stale handling. Passive windows do not wake a sleeping car. Status requests have a three-second timeout and never retry heat commands. The timer display reflects an existing deadline; it does not verify physical heating or shutdown.
- The latest build, all 48 host checks and simulated real-browser regression passed. No PCB, BOM, calibration, heat threshold or climate-sequence change was made. Nothing was pushed to GitHub.

See [full session record](WEBSITE-BATTERY-2026-11-16.md) and [remaining physical checks](VALIDATION.md).

### Later the same day: native iOS prototype

At the owner’s request, API/iOS work resumed. A SwiftUI app now provides setup, Keychain token storage, BMS percentage/age, protected supply and explicit heater requests. Pending/uncertain commands persist across restart and are never automatically replayed. The app and test targets build; seven host-model tests and 23 server tests pass. Interactive simulator checks exercised the real API with an isolated fake board, including On/Off, cancellation, stale/missing data, connection loss, commissioning lock and uncertain-result recovery. Xcode’s automated simulator test service could not attach, so UI checks were performed through the running simulator instead. No vehicle commands, firmware flash, GitHub push or physical iPhone installation occurred. See [app verification](../ios/verification/2026-11-16.md).
