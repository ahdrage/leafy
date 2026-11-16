# Leafy API for an iOS app

**Status, 16 November 2026:** API/iOS work resumed. The [native Leafy app](../ios/README.md) is built and has been exercised in the iPhone simulator against this API with a fake board. Seven app-model tests and 23 server tests pass. Physical iPhone/vehicle use through the bridge remains unvalidated; the existing board-hosted website still works independently.

A small, single-car API bridge. It runs on a Mac, Raspberry Pi, or other computer on the same network as Leafy. No cloud account or database service is required. Node.js 22 or newer is the only server dependency.

```text
iPhone app → API server → Leafy over home Wi-Fi → Leaf EV-CAN
```

The server must be awake and able to reach the car. The iPhone must be able to reach the server. This first version is for local/private networking, not direct public-internet exposure. An off-site VPS alone cannot reach the car's private Wi-Fi address.

## Start on this Mac

From Terminal:

```sh
cd /path/to/leafy
node --env-file=server/.env.local server/src/main.mjs
```

Private configuration is in `server/.env.local`. It is ignored by Git and contains:

- `LEAFY_DEVICE_URL`: the same IP address used for the board's existing web page. Reserve that address in the router if possible.
- `LEAFY_DEVICE_KEY`: the board's current control key.
- `LEAFY_API_TOKEN`: a separate random token for the app. Copy it into the app's setup screen and store it in the iOS Keychain. Never put it in source control, a URL, screenshots, or logs.
- `LEAFY_BIND`: the interface used by the API. The example defaults to `127.0.0.1` (this Mac only). The owner’s private configuration is set to the Mac’s home-Wi-Fi address for iPhone development.

To configure another installation, copy `.env.example` to `.env.local`, fill in the board address and key, and generate a distinct app token with `openssl rand -hex 32`. Launch from the repository root; the state path is relative to that directory. Protect the configuration file with owner-only permissions.

Do not launch a second instance if one is already listening. Stop with Ctrl+C. A lock prevents multiple processes using the same command ledger. After an abnormal shutdown, verify that the old process has stopped before deleting `server/data/commands.json.lock`. Keep `commands.json`: it prevents replay of previously attempted commands.

## Connect a physical iPhone

The owner’s local configuration is already enabled for the current home-Wi-Fi interface. For another installation, set the actual LAN interface address and enable access, then restart:

```dotenv
LEAFY_BIND=192.168.1.50
LEAFY_ALLOW_LAN_HTTP=true
```

Replace that example IP with the Mac’s actual address. Reserve it in the router or update the setting if it changes. Use `http://<Mac's LAN IP>:8787` as the app's server address; `localhost` on an iPhone refers to the phone. Both the device key and app token travel over HTTP on the LAN in this mode, so only use a trusted network. Do not add router port forwarding or a public tunnel. Allow Node through the Mac firewall if prompted, and keep the Mac awake.

For routine iPhone use or access away from home, put the loopback server behind authenticated/private networking with HTTPS, for example an always-on home host with a private VPN and an HTTPS proxy. The car still needs home Wi-Fi coverage. That deployment is not configured by this change. The API token remains required even behind a VPN.

Use a local-network permission description in the iOS app. iOS App Transport Security must allow the chosen endpoint; prefer HTTPS with a trusted certificate rather than a blanket `NSAllowsArbitraryLoads` exception. The [Xcode app](../ios/README.md) includes a local-network permission description, `NSAllowsLocalNetworking` and Keychain storage. It validates private addresses for plain HTTP; HTTPS remains required for other hosts.

## API

[OpenAPI specification](openapi.json) and [Swift client](../ios/LeafyClient.swift).

All routes require `Authorization: Bearer <LEAFY_API_TOKEN>`. No cookies or browser CORS access are provided. The device key stays on the server.

| Request | Purpose |
| --- | --- |
| `GET /v1/status` | Read protected supply voltage, command state and main-battery SOC if available |
| `POST /v1/heater/commands` | Submit an explicit `on` or `off` request |
| `GET /v1/commands/{id}` | Look up a previously submitted command without sending it again |

Example command body:

```json
{"action":"on","issuedAt":"2026-11-16T12:00:00Z"}
```

Set `Content-Type: application/json` and `Idempotency-Key` to a newly generated UUID. Generate the timestamp at the user's button tap; the example timestamp above is intentionally not reusable. Commands older than 10 seconds or over 5 seconds in the future are rejected. Keep the phone's clock correct.

The app should save the UUID and command before sending. A duplicate ID returns its existing result; it is not forwarded again, including after a server restart. Do not generate a new ID to automatically retry a failed request. A fresh UUID is for a new, deliberate user action.

Command outcomes:

- `accepted` (HTTP 202): Leafy queued the request. This is **not confirmation that the heater is running or stopped**. Subsequent `lastCommandError` may reveal CAN failure, but no car climate-state decoder is implemented.
- `rejected`: the board rejected the request, e.g. low protected voltage, commissioning lock or a busy sequence.
- `pending`: another request with this ID is still in progress. Poll its command-result URL.
- `unknown`: delivery may have happened but the response/result was lost. Check the car; never automatically resend On with a new ID.

A separate HTTP 409 `delivery_busy` error means another HTTP delivery is still in flight and this new request was **not sent**. Wait for the result, then explicitly request Off if needed. Off can preempt a running heater sequence once the earlier HTTP delivery has finished. New On requests are rate limited to one per three seconds; Off is not subject to that interval.

The server sends no commands on startup/reconnect, has no offline command queue and does not retry board commands. It reserves each command in an owner-only, durable local ledger before contacting Leafy. At 10,000 recorded IDs it fails closed; archive/reset only while stopped, with all old clients retired and the app token rotated. Do not delete history as routine troubleshooting.

## Battery and heater meanings

`protectedSupplyVolts` is the measured supply **after the input diode**. It is neither the exact battery-terminal voltage nor the 12 V battery's charge percentage.

`tractionBattery.socPercent` is the main traction battery's BMS SOC decoded from EV-CAN `0x55B`, following the pinned OVMS implementation. It may differ from the dashboard percentage. It is not battery health/SOH or range.

Firmware listens without transmitting for 1.5 seconds each minute while idle, and also collects received frames during commanded CAN activity. A sleeping car may provide no new readings. Status reads never wake it. The default sampling schedule adds some power consumption; repeat parked-current checks before relying on long-term parking performance.

- `fresh`: sample age at most 120 seconds.
- `stale`: older sample; show the age alongside the value.
- `unavailable`: updated firmware has not received a valid SOC sample since boot.
- `unsupported`: installed firmware does not provide SOC yet, or telemetry is disabled.

Missing values are `null`, never a fabricated 0%. Do not show an old percentage as live. If the device cannot be read, the server returns 503 instead of a cached successful status. `heater.actualState` remains `unknown`; `heater.requested` is local request/timer state only.

The prototype now has the 16 November dual-battery website firmware installed, including the JSON endpoint and passive SOC sampling. The bridge’s `tractionBattery.socPercent` remains the BMS value; the dashboard field has not been added to this API. The normal website received both signals from the car, but that does not establish end-to-end bridge/iOS validation. Older firmware remains supported with voltage-only status. No hardware or Mouser changes are required.

## iOS use

Open [the app project](../ios/Leafy.xcodeproj) to use the provided native UI. It already saves the token in Keychain, polls status while active, persists command intent and handles uncertain results. The example below is for other clients; preserve these same behaviors.

```swift
let client = try LeafyClient(baseURL: serverURL, apiToken: tokenFromKeychain)
let status = try await client.status()

// Only in response to a deliberate user tap:
let id = UUID()
let command = LeafyClient.Command(.on)
// Persist id and command here before sending; disable duplicate taps.
let result = try await client.send(command, id: id)
// Show result.message. Do not turn an "accepted" result into "heater running".
```

If `deliveryUnknown(id)` is thrown, query `commandResult(id:)` after connectivity recovers. A 404 does not justify an automatic fresh On: the original request may still be in transit. Let the user check the car and make an explicit decision. Preserve unresolved IDs across app restarts. Do not queue taps while offline.

## Validation

```sh
node --test server/test/*.test.mjs
```

The tests use temporary simulated boards, including a complete local HTTP chain. They cover authentication, stale/missing status, body limits, redirects, rejection, unknown outcomes, expiry, UUID casing, concurrent duplicates, delivery ordering and persistence across restart. No test sends vehicle commands.

The native app builds and has been tested interactively in the iOS simulator against a fake board through the real bridge. Seven host logic tests and 23 server tests pass. Physical iPhone/vehicle status and commands through this bridge still require device testing. Battery reception on the normal board-hosted website has been demonstrated separately. See [implementation and acceptance record](../docs/API-2026-11-16.md).
