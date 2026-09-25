#include "control.hpp"
#include <atomic>
#include <iostream>
#include <stdexcept>
#include <vector>

#define CHECK(x) do { if (!(x)) throw std::runtime_error(#x); } while (0)
#define LEAF_CAN_WRITE_ENABLED true
#define LEAF_MIN_HEAT_VPWR 12.2f
#define ESP_ERR_INVALID_STATE 1
#define ESP_ERR_TIMEOUT 2
#define pdTRUE 1
#define pdMS_TO_TICKS(x) ((x) * 100 / 1000)
struct Request { bool on; uint64_t expires_ms; };
struct EndSimulation {};
struct Input { uint64_t at; Request request; };
struct Voltage { uint64_t at; int mv; };
struct Sent { uint64_t at; leaf::Frame frame; };
static uint64_t clock_ms, end_ms, failed_wake_at;
static int requests;
static std::atomic<bool> busy, heat_requested, battery_ok;
static std::atomic<int> vpwr_mv, last_error;
static std::vector<Input> inputs;
static std::vector<Voltage> voltages;
static std::vector<Sent> sent;
static uint64_t now_ms() { return clock_ms; }
static bool can_send(const leaf::Frame& frame) {
    sent.push_back({clock_ms, frame});
    return !(clock_ms == failed_wake_at && frame.id == 0x679);
}
static void can_stop() {}
static int read_vpwr() {
    int mv = 0;
    for (const auto& v : voltages) if (clock_ms >= v.at) mv = v.mv;
    return mv;
}
static int xQueueReceive(int, Request* request, int) {
    for (const auto& input : inputs) {
        if (input.at == clock_ms) { *request = input.request; return pdTRUE; }
    }
    return 0;
}
static void vTaskDelay(int ticks) {
    CHECK(ticks > 0);
    clock_ms += ticks * 10;
    if (clock_ms >= end_ms) throw EndSimulation{};
}

#include "control_task.inc"

static void run(std::vector<Voltage> voltage, std::vector<Input> input,
                uint64_t end = 40000, uint64_t fail_at = UINT64_MAX) {
    voltages = voltage; inputs = input; sent.clear(); clock_ms = 0;
    end_ms = end; failed_wake_at = fail_at;
    busy = false; heat_requested = false; battery_ok = false; vpwr_mv = 0; last_error = 0;
    try { control_task(nullptr); } catch (const EndSimulation&) {}
}
static int climate_count(uint8_t byte, uint64_t begin, uint64_t end) {
    int count = 0;
    for (const auto& s : sent)
        if (s.at >= begin && s.at < end && s.frame.id == 0x56e && s.frame.data[0] == byte) ++count;
    return count;
}

int main() {
    int count = 0, failures = 0;
    auto test = [&](const char* name, auto fn) {
        ++count;
        try { fn(); std::cout << "PASS " << name << '\n'; }
        catch (const std::exception& e) { ++failures; std::cout << "FAIL " << name << ": " << e.what() << '\n'; }
    };
    const std::vector<Voltage> two_sessions{{0,12600},{5000,12100},{18000,12300},{24000,12100}};
    test("low-battery Off re-arms after partial recovery and a new On", [&] {
        run(two_sessions, {{20,{true,1020}}, {19000,{true,20000}}});
        CHECK(climate_count(0x56, 0, 19000) == 24);
        CHECK(climate_count(0x4e, 19000, 24000) == 24);
        CHECK(climate_count(0x56, 24000, 34000) == 0);
        CHECK(climate_count(0x56, 34000, 40000) == 24);
        CHECK(!heat_requested);
    });
    test("uncertain On with failed wake still re-arms low-battery Off", [&] {
        run(two_sessions, {{20,{true,1020}}, {19000,{true,20000}}}, 40000, 19000);
        CHECK(climate_count(0x4e, 19000, 40000) == 0);
        CHECK(climate_count(0x56, 34000, 40000) == 24);
        CHECK(!heat_requested);
    });
    test("new heating session receives its own ten-second low-voltage interval", [] {
        run({{0,12600},{5000,12100},{9000,12300},{11000,12100}},
            {{20,{true,1020}}, {10000,{true,11000}}}, 27000);
        CHECK(climate_count(0x56, 0, 21000) == 0);
        CHECK(climate_count(0x56, 21000, 27000) == 24);
    });
    test("rejected low-voltage and expired On requests cannot postpone Off", [] {
        run({{0,12600},{5000,12100}},
            {{20,{true,1020}}, {8000,{true,9000}}, {12000,{true,11000}}}, 21000);
        CHECK(climate_count(0x56, 0, 15000) == 0);
        CHECK(climate_count(0x56, 15000, 21000) == 24);
        CHECK(!heat_requested);
    });
    test("On rejected while a sequence is busy cannot reset the low-voltage interval", [] {
        run({{0,12600},{1000,12100},{2000,12300},{3000,12100}},
            {{20,{true,1020}}, {2100,{true,3100}}}, 15000);
        CHECK(climate_count(0x56, 0, 11000) == 0);
        CHECK(climate_count(0x56, 11000, 13500) == 24);
        CHECK(!heat_requested);
    });
    test("failed low-battery Off is attempted once per low-voltage episode", [] {
        run({{0,12600},{5000,12100}}, {{20,{true,1020}}}, 40000, 15000);
        int wakes = 0;
        for (const auto& s : sent) if (s.at >= 15000 && s.frame.id == 0x679) ++wakes;
        CHECK(wakes == 1);
        CHECK(heat_requested);  // Failed Off must not claim the heater is off.
    });
    std::cout << count << " tests, " << failures << " failures\n";
    return failures ? 1 : 0;
}
