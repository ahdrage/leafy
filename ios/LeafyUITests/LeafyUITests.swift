import XCTest

// Start scripts/simulator-server.mjs before this suite. All commands target its fake car.
@MainActor final class LeafyUITests: XCTestCase {
    private let app = XCUIApplication()
    private let token = "leafy-simulator-token-not-for-real-cars"
    override func setUpWithError() throws {
        continueAfterFailure = false
        app.launch()
        if app.buttons["Connection settings"].waitForExistence(timeout: 2) {
            app.buttons["Connection settings"].tap()
            app.buttons["Forget connection"].tap()
        }
        XCTAssertTrue(app.staticTexts["Connect your Leafy"].waitForExistence(timeout: 5))
    }
    private func connect() {
        let address = app.textFields["serverAddress"]
        address.tap(); address.typeText("http://127.0.0.1:18787")
        let key = app.secureTextFields["appToken"]
        key.tap(); key.typeText(token)
        app.buttons["Connect"].tap()
        XCTAssertTrue(app.staticTexts["Connected at home"].waitForExistence(timeout: 12))
    }
    private func scenario(_ name: String) async throws -> Int {
        var request = URLRequest(url: URL(string: "http://127.0.0.1:18789/scenario?name=\(name)")!)
        request.httpMethod = "POST"
        let (data, _) = try await URLSession.shared.data(for: request)
        let body = try JSONSerialization.jsonObject(with: data) as! [String: Any]
        return (body["calls"] as! [String]).count
    }
    private func waitLabel(_ identifier: String, contains text: String) {
        let element = app.staticTexts[identifier]
        let predicate = NSPredicate(format: "label CONTAINS %@", text)
        expectation(for: predicate, evaluatedWith: element)
        waitForExpectations(timeout: 15)
    }
    func testSetupIsRequiredBeforeControllingCar() {
        XCTAssertTrue(app.textFields["serverAddress"].exists)
        XCTAssertTrue(app.secureTextFields["appToken"].exists)
        XCTAssertFalse(app.buttons["heatOn"].exists)
        XCTAssertFalse(app.buttons["Connect"].isEnabled)
    }
    func testBatteryCommandsOfflineAndRelaunch() async throws {
        _ = try await scenario("fresh")
        connect()
        // Clear any deliberately uncertain record from a preceding manual run.
        if app.buttons["I’ve checked the car…"].exists {
            app.swipeUp(); app.buttons["I’ve checked the car…"].tap()
            app.alerts.buttons["I’ve checked the car"].tap(); app.swipeDown()
        }
        waitLabel("batteryValue", contains: "92.5%")
        let before = try await scenario("fresh")
        app.buttons["heatOn"].tap(); app.alerts.buttons["Cancel"].tap()
        let afterCancel = try await scenario("fresh")
        XCTAssertEqual(before, afterCancel)
        app.buttons["heatOn"].tap(); app.alerts.buttons["Request heat"].tap()
        waitLabel("commandMessage", contains: "Heat on request accepted")
        app.buttons["heatOff"].tap()
        waitLabel("commandMessage", contains: "Heat off request accepted")
        _ = try await scenario("stale")
        waitLabel("batteryAge", contains: "Last known")
        _ = try await scenario("offline")
        XCTAssertTrue(app.staticTexts["Connection unavailable"].waitForExistence(timeout: 15))
        XCTAssertFalse(app.buttons["heatOn"].isEnabled)
        XCTAssertFalse(app.buttons["heatOff"].isEnabled)
        XCTAssertEqual(app.staticTexts["batteryValue"].label, "—")
        _ = try await scenario("fresh")
        XCTAssertTrue(app.staticTexts["Connected at home"].waitForExistence(timeout: 15))
        let beforeRestart = try await scenario("fresh")
        app.terminate(); app.launch()
        XCTAssertTrue(app.staticTexts["Connected at home"].waitForExistence(timeout: 15))
        let afterRestart = try await scenario("fresh")
        XCTAssertEqual(beforeRestart, afterRestart)
    }
}
