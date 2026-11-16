#pragma once
// Copy to settings.hpp locally. Never publish your Wi-Fi password or control key.
#define LEAF_WIFI_SSID ""
#define LEAF_WIFI_PASSWORD ""
#define LEAF_CONTROL_KEY ""
// Enable only after bench CAN checks, TCU confirmation and cable continuity checks.
#define LEAF_CAN_WRITE_ENABLED false
// Temporary in-car diagnostic: receive at 500 kbit/s without TX/ACK/error frames.
// This mode must not be combined with CAN writes; it keeps the CAN controller awake.
#define LEAF_CAN_LISTEN_ONLY false
// VPWR is AFTER the Schottky diode. Calibrate against a meter before vehicle use.
#define LEAF_ADC_SCALE 32.2765957447f
#define LEAF_ADC_CORRECTION 1.0f
#define LEAF_MIN_HEAT_VPWR 12.2f

// Passive 1.5-second SOC sampling every 60 seconds; no car wakeup. Re-measure current.
#define LEAF_TELEMETRY_ENABLED true
