import XCTest
@testable import Leafy

final class MemoryStore: LeafyStore {
    var config: Connection?
    var journal: CommandRecord?
    var failWrites = false
    func connection() throws -> Connection? { config }
    func save(connection: Connection) throws { if failWrites { throw URLError(.cannotWriteToFile) }; config = connection }
    func forgetConnection() throws { config = nil }
    func record() throws -> CommandRecord? { journal }
    func save(record: CommandRecord) throws { if failWrites { throw URLError(.cannotWriteToFile) }; journal = record }
}
final class FakeAPI: LeafyAPI {
    var offline = false
    var unknown = false
    var posts = 0
    var gets = 0
    var ids: [UUID] = []
    var onSend: (() -> Void)?
    var sample = LeafyClient.Status(apiVersion: 1, deviceReachable: true, observedAt: "2026-11-16T12:00:00Z", protectedSupplyVolts: 13.7, canWriteEnabled: true, requestBusy: false, lastCommandError: 0, heater: .init(requested: false, actualState: "unknown"), tractionBattery: .init(socPercent: 92.5, ageSeconds: 26, availability: "fresh", source: "ev_can_0x55b_bms"))
    func status() async throws -> LeafyClient.Status { gets += 1; if offline { throw URLError(.notConnectedToInternet) }; return sample }
    func send(_ command: LeafyClient.Command, id: UUID) async throws -> LeafyClient.CommandResult {
        posts += 1; ids.append(id); onSend?()
        if unknown { throw LeafyClient.Failure.deliveryUnknown(id) }
        return .init(commandId: id.uuidString.lowercased(), action: command.action.rawValue, outcome: "accepted", actualHeaterState: "unknown", createdAt: command.issuedAt, message: "Request accepted; verify in car")
    }
    func commandResult(id: UUID) async throws -> LeafyClient.CommandResult {
        .init(commandId: id.uuidString.lowercased(), action: "on", outcome: "unknown", actualHeaterState: "unknown", createdAt: "2026-11-16T12:00:00Z", message: "Check car")
    }
    func close() {}
}
@MainActor final class LeafyTests: XCTestCase {
    let token = String(repeating: "a", count: 32)
    func testConnectionRejectsUnsafeAddressesAndShortToken() {
        for address in ["http://example.com", "http://user:pass@192.168.1.2", "http://192.168.1.2/path", "http://192.168.1.2?secret=x", "file:///tmp", "http://192.168.1.999"] {
            XCTAssertThrowsError(try Connection.validate(address: address, token: token), address)
        }
        XCTAssertThrowsError(try Connection.validate(address: "http://192.168.1.2:8787", token: "short"))
        for address in ["http://192.168.1.2:8787", "http://127.0.0.1:18787", "http://leafy.local:8787", "https://leafy.example.com"] {
            XCTAssertNoThrow(try Connection.validate(address: address, token: token))
        }
    }
    func testConnectOnlyReadsAndPersistsCredentials() async {
        let store = MemoryStore(), api = FakeAPI()
        let model = LeafyModel(store: store, makeClient: { _ in api })
        await model.connect(address: "http://127.0.0.1:18787", token: token)
        XCTAssertNotNil(store.config); XCTAssertEqual(api.posts, 0)
        XCTAssertEqual(model.batteryText, "92.5%")
        XCTAssertTrue(model.canHeatOn)
    }
    func testFailedStatusClearsReadingsAndDisablesCommands() async {
        let store = MemoryStore(), api = FakeAPI()
        let model = LeafyModel(store: store, makeClient: { _ in api })
        await model.connect(address: "http://127.0.0.1:18787", token: token)
        api.offline = true; await model.refresh(); await model.send(.on)
        XCTAssertNil(model.status); XCTAssertFalse(model.canHeatOn)
        XCTAssertFalse(model.canHeatOff); XCTAssertEqual(api.posts, 0)
        XCTAssertFalse(model.message.isEmpty)
    }
    func testIntentIsSavedBeforeSendingAndNotReplayedAfterRestart() async {
        let store = MemoryStore(), api = FakeAPI()
        let model = LeafyModel(store: store, makeClient: { _ in api })
        await model.connect(address: "http://127.0.0.1:18787", token: token)
        api.onSend = { XCTAssertEqual(store.journal?.outcome, "pending") }
        await model.send(.on)
        XCTAssertEqual(api.posts, 1); XCTAssertEqual(store.journal?.outcome, "accepted")
        let restored = LeafyModel(store: store, makeClient: { _ in api })
        await restored.refresh()
        XCTAssertEqual(restored.latestCommand?.id, store.journal?.id); XCTAssertEqual(api.posts, 1)
    }
    func testUnknownBlocksNewOnButAllowsExplicitOffAndLookupNeverResends() async {
        let store = MemoryStore(), api = FakeAPI()
        let model = LeafyModel(store: store, makeClient: { _ in api })
        await model.connect(address: "http://127.0.0.1:18787", token: token)
        api.unknown = true; await model.send(.on)
        XCTAssertEqual(model.latestCommand?.outcome, "unknown")
        XCTAssertFalse(model.canHeatOn); XCTAssertTrue(model.canHeatOff)
        await model.send(.on); await model.checkCommand()
        XCTAssertEqual(api.posts, 1)
        let restored = LeafyModel(store: store, makeClient: { _ in api })
        await restored.refresh(); XCTAssertFalse(restored.canHeatOn)
        XCTAssertEqual(api.posts, 1)
        api.unknown = false; await restored.send(.off)
        XCTAssertEqual(api.posts, 2); XCTAssertEqual(restored.latestCommand?.action, "off")
    }
    func testJournalFailurePreventsCommandDelivery() async {
        let store = MemoryStore(), api = FakeAPI()
        let model = LeafyModel(store: store, makeClient: { _ in api })
        await model.connect(address: "http://127.0.0.1:18787", token: token)
        store.failWrites = true; await model.send(.on)
        XCTAssertEqual(api.posts, 0); XCTAssertFalse(model.message.isEmpty)
    }
    func testReadingsAgeAndBackgroundDisablesCommands() async {
        let store = MemoryStore(), api = FakeAPI()
        var now = Date()
        let model = LeafyModel(store: store, now: { now }, makeClient: { _ in api })
        await model.connect(address: "http://127.0.0.1:18787", token: token)
        now.addTimeInterval(100)
        XCTAssertTrue(model.batteryDetail.contains("Last known"))
        XCTAssertFalse(model.canHeatOn)
        model.suspend(); XCTAssertNil(model.status)
        await model.refresh(); XCTAssertTrue(model.canHeatOn)
        model.forget(); XCTAssertNil(store.config); XCTAssertNil(model.connection)
    }
}
