# Leafy for iPhone

A native SwiftUI app for Leafy’s home-Wi-Fi API. It shows the main battery’s **BMS percentage**, sample age, protected 12 V supply and command results. It can request Heat On or Heat Off. The separate dashboard percentage remains available on the board’s website; the current API exposes BMS only.

## Run in the simulator

Open [Leafy.xcodeproj](Leafy.xcodeproj), select **Leafy** and an installed iPhone simulator, then Run. No Apple Developer membership is needed for simulator use. The project is checked in; XcodeGen is only needed after changing [project.yml](project.yml).

For an isolated test connection, run from the repository root:

```sh
node ios/scripts/simulator-server.mjs
```

Enter these **test-only** settings in the app:

- Server: `http://127.0.0.1:18787`
- App token: `leafy-simulator-token-not-for-real-cars`

The fixture binds only to loopback and uses the real API bridge with a fake board. It cannot contact a car and never reads private configuration. Its public token is not a real credential. Stop it with Ctrl+C. Ports 18787–18789 must be free. The simulator’s loopback reaches the Mac; on a physical iPhone, loopback refers to the phone.

## Connect to your actual Leafy

1. Start the [home API server](../server/README.md) on an awake Mac or other home host. It must be configured with the board’s URL and control key.
2. In the app enter the **server’s** LAN URL, such as `http://192.168.1.50:8787`. This is not the board’s website URL.
3. Enter `LEAFY_API_TOKEN` from your private `server/.env.local`. Do not use the board’s control key. The app token and server URL are saved together in this device’s Keychain, accessible while unlocked and not synchronized to other devices.
4. Allow Local Network access if iOS asks. Keep the iPhone, server and car on the reachable home network. If access was denied, change it under iOS Settings → Privacy & Security → Local Network.
5. Verify the readings first, then perform a supervised Heat On/Off check while parked. Simulator results are not a vehicle acceptance test.

To install on an iPhone, open the project in Xcode, select your signing team under Signing & Capabilities, select the phone and Run. This task did not configure signing, install on a phone, deploy a permanent server or publish to TestFlight/App Store.

HTTP is allowed only for private IPv4, loopback and `.local` addresses by app validation; other servers require HTTPS. Certificate checks are not bypassed, redirects are refused and no blanket ATS exception is used. Plain HTTP still exposes the token to the local network: use only trusted home Wi-Fi, with no port forwarding or public tunnel. The iOS deployment target is 17; simulator testing used iOS 26.1.

## Commands and readings

- Heat On asks for confirmation. Heat Off sends an explicit request without another confirmation.
- “Accepted” means the board queued a request, **not** that physical heating or shutdown was confirmed.
- The app saves a UUID and command intent before sending, disables duplicate taps during delivery and never automatically resends a command. No offline command queue is used.
- An uncertain result survives app restart. New Heat On is blocked; **Check request result** performs a lookup only. Explicit Off remains available when connected. **I’ve checked the car…** requires confirmation before clearing uncertainty and sends nothing itself.
- The latest command record is retained when forgetting a connection and restored only for the same server URL. A later deliberate command replaces that record; the API server retains the complete command ledger.
- Status polls every five seconds while foregrounded, without overlapping requests. Backgrounding clears live status. Network waits are bounded by the client’s 10/12-second request/resource limits.
- Missing data appears as `—`; older battery data is labelled **Last known**. Battery age advances locally between polls. A failed status read clears the readings and disables commands; status older than 15 seconds also disables commands.
- Protected supply is measured **after the input diode**, not exact battery-terminal voltage. The BMS percentage is traction-battery charge, not battery health or range.

## Testing

Host logic tests use the same model/client source as the app:

```sh
ios/scripts/test-logic.sh
node --test server/test/*.test.mjs
```

Build and optionally run Xcode tests with a destination available on your Mac:

```sh
xcodebuild -project ios/Leafy.xcodeproj -scheme Leafy \
  -destination 'platform=iOS Simulator,name=iPhone 17 Pro,OS=26.1' \
  -derivedDataPath ios/build build-for-testing
```

After starting the fixture, change `build-for-testing` to `test` to run the unit/UI test targets. The UI test suite expects the fixture above and never uses a real car connection. Do not point that fixture at real hardware.

See [the dated verification report](verification/2026-11-16.md) for what actually ran, including the simulator automation limitation. Built apps, DerivedData and Xcode user state are ignored by Git. No private token is included in source or screenshots.

References: [Apple’s local-network ATS setting](https://developer.apple.com/documentation/bundleresources/information-property-list/nsapptransportsecurity/nsallowslocalnetworking), [device-only unlocked Keychain storage](https://developer.apple.com/documentation/security/ksecattraccessiblewhenunlockedthisdeviceonly).
