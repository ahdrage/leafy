#include "control.hpp"
#include <atomic>
#include <cstring>
#include <iostream>
#include <stdexcept>
#include <vector>

#define CHECK(x) do { if (!(x)) throw std::runtime_error(#x); } while (0)
#define LEAF_CAN_WRITE_ENABLED true
using esp_err_t = int;
using TickType_t = uint32_t;
constexpr int ESP_OK = 0, ESP_FAIL = -1, ESP_ERR_TIMEOUT = 0x107;
constexpr int STB = 1, TX = 4, RX = 5, TWAI_MODE_NORMAL = 0;
constexpr uint32_t TWAI_ALERT_TX_SUCCESS = 0x2, TWAI_ALERT_TX_FAILED = 0x400, TWAI_ALERT_BUS_OFF = 0x2000;
struct twai_general_config_t { int mode, tx_io, rx_io, tx_queue_len = 5, rx_queue_len = 5; };
struct twai_timing_config_t {};
struct twai_filter_config_t {};
struct twai_message_t { uint32_t identifier = 0; uint8_t data_length_code = 0, data[8]{}; bool ss = false; };
#define TWAI_GENERAL_CONFIG_DEFAULT(tx, rx, mode) twai_general_config_t{mode,tx,rx}
#define TWAI_TIMING_CONFIG_500KBITS() twai_timing_config_t{}
#define TWAI_FILTER_CONFIG_ACCEPT_ALL() twai_filter_config_t{}
static uint32_t tick_hz;
#define pdMS_TO_TICKS(ms) ((ms) * tick_hz / 1000)

// Model ESP-IDF 5.5 legacy TWAI: queue-disabled direct TX, single-shot failure
// on arbitration loss, normal retry until ACK, and stop cancelling pending TX.
enum class BusEvent { ArbitrationLost, Ack, BusOff, AckAndBusOff };
struct Event { uint64_t after_us; BusEvent kind; };
static uint64_t clock_us, enabled_at, transmitted_at;
static int standby;
static bool installed, running, pending, can_started;
static bool fail_install, fail_start, fail_alerts;
static std::atomic<int> last_error;
static twai_message_t pending_message;
static std::vector<Event> events;
static std::vector<twai_message_t> delivered;
static int gpio_set_level(int, int level) {
    standby = level;
    if (!level) enabled_at = clock_us;
    return ESP_OK;
}
[[maybe_unused]] static void vTaskDelay(TickType_t ticks) {
    // A zero-tick delay yields without any guaranteed time passing.
    clock_us += static_cast<uint64_t>(ticks) * 1000000 / tick_hz;
}
[[maybe_unused]] static void esp_rom_delay_us(uint32_t us) { clock_us += us; }
static int twai_driver_install(const twai_general_config_t* config,
                               const twai_timing_config_t*, const twai_filter_config_t*) {
    CHECK(config->mode == TWAI_MODE_NORMAL); CHECK(config->tx_queue_len == 0);
    if (fail_install) return ESP_FAIL;
    installed = true; return ESP_OK;
}
static int twai_start() { if (fail_start) return ESP_FAIL; running = true; return ESP_OK; }
static int twai_stop() {
    if (!running) return ESP_FAIL; // Legacy stop rejects the bus-off state.
    running = false; pending = false; return ESP_OK;
}
static int twai_driver_uninstall() { installed = false; return ESP_OK; }
static int twai_reconfigure_alerts(uint32_t, uint32_t*) { return fail_alerts ? ESP_FAIL : ESP_OK; }
static int twai_transmit(const twai_message_t* message, TickType_t) {
    CHECK(installed && running && !standby);
    if (pending) return ESP_FAIL;
    pending_message = *message; pending = true; transmitted_at = clock_us;
    return ESP_OK;
}
static int twai_read_alerts(uint32_t* alerts, TickType_t ticks) {
    *alerts = 0;
    if (!ticks) return ESP_ERR_TIMEOUT; // No stale alerts in these scenarios.
    const uint64_t deadline = clock_us + static_cast<uint64_t>(ticks) * 1000000 / tick_hz;
    for (const auto& event : events) {
        const auto at = transmitted_at + event.after_us;
        if (!pending || at > deadline) break;
        clock_us = at;
        switch (event.kind) {
        case BusEvent::ArbitrationLost:
            if (!pending_message.ss) continue;
            *alerts = TWAI_ALERT_TX_FAILED; break;
        case BusEvent::Ack:
            delivered.push_back(pending_message); *alerts = TWAI_ALERT_TX_SUCCESS; break;
        case BusEvent::BusOff:
            running = false; *alerts = TWAI_ALERT_BUS_OFF; break;
        case BusEvent::AckAndBusOff:
            running = false;
            delivered.push_back(pending_message); *alerts = TWAI_ALERT_TX_SUCCESS | TWAI_ALERT_BUS_OFF; break;
        }
        pending = false; return ESP_OK;
    }
    clock_us = deadline;
    return ESP_ERR_TIMEOUT;
}

#include "can_transport.inc"

static void reset(uint32_t hz = 100) {
    tick_hz = hz; clock_us = enabled_at = transmitted_at = 0; standby = 1;
    installed = running = pending = can_started = false;
    fail_install = fail_start = fail_alerts = false; last_error = 0;
    delivered.clear(); events.clear();
}
static void check_stopped() {
    CHECK(standby == 1); CHECK(!pending); CHECK(!installed); CHECK(!running); CHECK(!can_started);
}
int main() {
    int count = 0, failures = 0;
    auto test = [&](const char* name, auto fn) {
        ++count; reset();
        try { fn(); std::cout << "PASS " << name << '\n'; }
        catch (const std::exception& e) { ++failures; std::cout << "FAIL " << name << ": " << e.what() << '\n'; }
    };
    const leaf::Frame on{0x56e,1,{0x4e}};
    test("normal arbitration losses followed by ACK succeed", [&] {
        events = {{100,BusEvent::ArbitrationLost},{300,BusEvent::ArbitrationLost},{800,BusEvent::Ack}};
        CHECK(can_send(on)); CHECK(delivered.size() == 1);
        CHECK(delivered[0].identifier == on.id && delivered[0].data_length_code == on.size);
        CHECK(std::memcmp(delivered[0].data, on.data, on.size) == 0);
    });
    test("continuous contention is bounded and pending On is cancelled", [&] {
        for (uint64_t us = 100; us < 60000; us += 100) events.push_back({us,BusEvent::ArbitrationLost});
        CHECK(!can_send(on)); CHECK(clock_us - transmitted_at <= 40000);
        check_stopped(); CHECK(delivered.empty());
        // A late ACK after cancellation cannot deliver the old frame.
        events = {{50000,BusEvent::Ack}};
        uint32_t alerts = 0; twai_read_alerts(&alerts, pdMS_TO_TICKS(100));
        CHECK(delivered.empty());
    });
    test("no ACK times out and leaves no pending frame", [&] {
        CHECK(!can_send(on)); CHECK(last_error == ESP_ERR_TIMEOUT);
        CHECK(clock_us - transmitted_at <= 40000); check_stopped(); CHECK(delivered.empty());
    });
    test("bus-off aborts transmission", [&] {
        events = {{500,BusEvent::BusOff}};
        CHECK(!can_send(on)); check_stopped();
    });
    test("bus-off cannot be masked by a simultaneous TX success alert", [&] {
        events = {{500,BusEvent::AckAndBusOff}};
        CHECK(!can_send(on)); check_stopped();
    });
    test("transceiver is ready before first TX at 100 Hz and 1000 Hz", [&] {
        for (auto hz : {100u,1000u}) {
            reset(hz); events = {{500,BusEvent::Ack}};
            CHECK(can_send(on)); CHECK(transmitted_at - enabled_at >= 30);
            can_stop(); check_stopped();
            CHECK(can_send(on)); CHECK(transmitted_at - enabled_at >= 30);
        }
    });
    test("driver installation failure leaves transceiver in standby", [&] {
        fail_install = true; CHECK(!can_send(on)); check_stopped();
    });
    test("driver start failure releases installed driver", [&] {
        fail_start = true; CHECK(!can_send(on)); check_stopped();
    });
    test("failed alert configuration cannot transmit an unmonitored frame", [&] {
        fail_alerts = true; events = {{500,BusEvent::Ack}};
        CHECK(!can_send(on)); CHECK(delivered.empty()); check_stopped();
    });
    std::cout << count << " tests, " << failures << " failures\n";
    return failures ? 1 : 0;
}
