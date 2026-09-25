#pragma once
// Copy to settings.hpp locally. Never publish your Wi-Fi password or control key.
#define LEAF_WIFI_SSID ""
#define LEAF_WIFI_PASSWORD ""
#define LEAF_CONTROL_KEY ""
// Enable only after bench CAN checks, TCU confirmation and cable continuity checks.
#define LEAF_CAN_WRITE_ENABLED false
// VPWR is AFTER the Schottky diode. Calibrate against a meter before vehicle use.
#define LEAF_ADC_SCALE 32.2765957447f
#define LEAF_ADC_CORRECTION 1.0f
#define LEAF_MIN_HEAT_VPWR 12.2f
