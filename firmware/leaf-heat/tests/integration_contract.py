"""Build-time safety requirements; hardware integration still needs bench testing."""
from pathlib import Path
p=Path(__file__).resolve().parents[1]
s=(p/'src/main.cpp').read_text()
checks={
 'station remains associated during power saving':'WIFI_PS_MIN_MODEM' in s and 'WIFI_MODE_STA' in s,
 'only automatic sleep, no deliberate disconnect':not any(x in s for x in ['esp_deep_sleep_start','esp_light_sleep_start','esp_wifi_disconnect','esp_wifi_stop']),
 'reconnect event implemented':'WIFI_EVENT_STA_DISCONNECTED' in s and 'retry.next_ms()' in s,
 'server validates control key':'leaf::authorized' in s,
 'physical CAN gated by commissioning setting':'LEAF_CAN_WRITE_ENABLED' in s,
 'stale command expiry implemented':'expires_ms' in s,
 'ADC uses calibration':'adc_cali_raw_to_voltage' in s,
 'CAN driver released while idle':'twai_driver_uninstall' in s,
}
for k,v in checks.items():print(('PASS ' if v else 'FAIL ')+k)
assert all(checks.values())
