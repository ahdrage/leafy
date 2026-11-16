import Foundation
import Combine

struct Connection: Codable, Equatable {
    let address: String
    let token: String
    static func validate(address: String, token: String) throws -> Connection {
        let address = address.trimmingCharacters(in: .whitespacesAndNewlines)
        let token = token.trimmingCharacters(in: .whitespacesAndNewlines)
        guard let url = URL(string: address), let host = url.host?.lowercased(),
              ["http", "https"].contains(url.scheme), url.user == nil, url.password == nil,
              url.query == nil, url.fragment == nil, url.path.isEmpty || url.path == "/",
              url.port == nil || (1...65535).contains(url.port!),
              token.count >= 32, token.count <= 512,
              token.unicodeScalars.allSatisfy({ $0.value >= 33 && $0.value <= 126 }) else {
            throw SetupError.invalid
        }
        if url.scheme == "http" {
            let parts = host.split(separator: ".", omittingEmptySubsequences: false)
            let octets = parts.compactMap { Int($0) }
            let ipv4 = parts.count == 4 && octets.count == 4 && octets.allSatisfy { (0...255).contains($0) }
            let localIP = ipv4 && (octets[0] == 10 || octets[0] == 127 ||
                (octets[0] == 192 && octets[1] == 168) ||
                (octets[0] == 172 && (16...31).contains(octets[1])))
            guard localIP || host == "localhost" || host.hasSuffix(".local") else { throw SetupError.localOnly }
        }
        return Connection(address: address.hasSuffix("/") ? String(address.dropLast()) : address, token: token)
    }
}
enum SetupError: LocalizedError {
    case invalid, localOnly
    var errorDescription: String? {
        switch self {
        case .invalid: return "Enter the server address (without a path) and its app token of at least 32 characters."
        case .localOnly: return "Use a private home-network address for HTTP, or a trusted HTTPS server."
        }
    }
}
struct CommandRecord: Codable {
    let id: UUID
    let action: String
    let issuedAt: String
    let server: String
    var outcome: String
    var message: String
    var unresolved: Bool { outcome == "pending" || outcome == "unknown" }
}
protocol LeafyAPI: AnyObject {
    func status() async throws -> LeafyClient.Status
    func send(_ command: LeafyClient.Command, id: UUID) async throws -> LeafyClient.CommandResult
    func commandResult(id: UUID) async throws -> LeafyClient.CommandResult
    func close()
}
extension LeafyClient: LeafyAPI {}
protocol LeafyStore {
    func connection() throws -> Connection?
    func save(connection: Connection) throws
    func forgetConnection() throws
    func record() throws -> CommandRecord?
    func save(record: CommandRecord) throws
}
@MainActor final class LeafyModel: ObservableObject {
    @Published private(set) var connection: Connection?
    @Published private(set) var status: LeafyClient.Status?
    @Published private(set) var latestCommand: CommandRecord?
    @Published private(set) var message = ""
    @Published private(set) var connecting = false
    @Published private(set) var refreshing = false
    @Published private(set) var sending = false
    @Published private(set) var checkingCommand = false
    private let store: LeafyStore
    private let now: () -> Date
    private let makeClient: (Connection) throws -> LeafyAPI
    private var client: LeafyAPI?
    private var receivedAt: Date?
    private var generation = 0
    private var persistenceFailed = false
    var isOnline: Bool { status != nil && receivedAt.map { now().timeIntervalSince($0) < 15 } == true }
    var canHeatOff: Bool { isOnline && status?.canWriteEnabled == true && !sending && !connecting && !persistenceFailed }
    var canHeatOn: Bool { canHeatOff && status?.requestBusy == false && latestCommand?.unresolved != true }
    var batteryText: String {
        guard let value = status?.tractionBattery.socPercent else { return "—" }
        return String(format: "%g%%", value)
    }
    var batteryDetail: String {
        guard let battery = status?.tractionBattery else { return "Connect to read the battery" }
        guard let seconds = battery.ageSeconds, battery.socPercent != nil else {
            return battery.availability == "unsupported" ? "Battery reading not supported by this firmware" : "Waiting for the car to send a reading"
        }
        let elapsed = max(0, Int(now().timeIntervalSince(receivedAt ?? now())))
        let age = seconds + elapsed
        let label = age > 120 || battery.availability == "stale" ? "Last known" : "Updated"
        return "\(label) · \(age < 60 ? "\(age)s" : "\(age / 60)m") ago"
    }
    init(store: LeafyStore, now: @escaping () -> Date = Date.init,
         makeClient: @escaping (Connection) throws -> LeafyAPI) {
        self.store = store; self.now = now; self.makeClient = makeClient
        do {
            if let saved = try store.connection() {
                let valid = try Connection.validate(address: saved.address, token: saved.token)
                connection = valid; client = try makeClient(valid)
                let record = try store.record()
                latestCommand = record?.server == valid.address ? record : nil
            }
        } catch { message = "Could not restore the saved connection. Unlock the phone and reconnect." }
    }
    func connect(address: String, token: String) async {
        guard !connecting && !sending else { return }
        connecting = true; defer { connecting = false }
        var candidate: LeafyAPI?
        do {
            let valid = try Connection.validate(address: address, token: token)
            candidate = try makeClient(valid)
            let sample = try await candidate!.status()
            try validate(sample)
            let record = try store.record()
            try store.save(connection: valid)
            generation += 1; client?.close(); client = candidate; connection = valid
            latestCommand = record?.server == valid.address ? record : nil
            persistenceFailed = false; status = sample; receivedAt = now(); message = ""
        } catch { candidate?.close(); message = describe(error) }
    }
    func refresh() async {
        guard !refreshing, !connecting, let client else { return }
        let version = generation
        refreshing = true; defer { refreshing = false }
        do {
            let sample = try await client.status(); try validate(sample)
            guard version == generation, !Task.isCancelled else { return }
            status = sample; receivedAt = now()
            if !persistenceFailed { message = "" }
        } catch {
            guard version == generation else { return }
            status = nil; receivedAt = nil; message = describe(error)
        }
    }
    func send(_ action: LeafyClient.Action) async {
        guard action == .on ? canHeatOn : canHeatOff, let connection, let client else { return }
        let intent = LeafyClient.Command(action)
        var record = CommandRecord(id: UUID(), action: action.rawValue, issuedAt: intent.issuedAt,
            server: connection.address, outcome: "pending", message: "Sending request…")
        do { try store.save(record: record) }
        catch { persistenceFailed = true; message = "Could not save the request safely. Nothing was sent. Reconnect to try again."; return }
        latestCommand = record; sending = true; defer { sending = false }
        do {
            let result = try await client.send(intent, id: record.id)
            try apply(result, to: &record)
        } catch let LeafyClient.Failure.http(code, _) where (400..<500).contains(code) {
            record.outcome = "rejected"; record.message = "Request rejected (\(code)). Check the connection and car before trying again."
        } catch {
            record.outcome = "unknown"; record.message = "Delivery uncertain. Check the car. This request will not be sent again automatically."
        }
        persistResult(record)
        await refresh()
    }
    func checkCommand() async {
        guard !sending, !checkingCommand, var record = latestCommand, record.unresolved, let client else { return }
        checkingCommand = true; defer { checkingCommand = false }
        let version = generation
        do {
            let result = try await client.commandResult(id: record.id)
            guard version == generation else { return }
            try apply(result, to: &record); persistResult(record)
        } catch {
            guard version == generation else { return }
            message = "Cannot confirm the saved request. Check the car; nothing was resent."
        }
    }
    func acknowledgeOutcome() {
        guard !sending, !checkingCommand, var record = latestCommand, record.unresolved else { return }
        record.outcome = "reviewed"; record.message = "You marked this outcome as checked. No new request was sent."
        persistResult(record)
    }
    func suspend() { generation += 1; status = nil; receivedAt = nil }
    func forget() {
        guard !sending, !connecting, !checkingCommand else { return }
        do {
            try store.forgetConnection(); generation += 1; client?.close(); client = nil
            connection = nil; status = nil; receivedAt = nil; latestCommand = nil; message = ""
        } catch { message = "Could not remove the saved connection. Please try again." }
    }
    private func persistResult(_ record: CommandRecord) {
        latestCommand = record
        do { try store.save(record: record) }
        catch { persistenceFailed = true; message = "Could not save the result. Check the car before reconnecting." }
    }
    private func apply(_ result: LeafyClient.CommandResult, to record: inout CommandRecord) throws {
        guard UUID(uuidString: result.commandId) == record.id, result.action == record.action,
              ["accepted", "rejected", "pending", "unknown"].contains(result.outcome) else { throw LeafyClient.Failure.unreadableResponse }
        record.outcome = result.outcome
        let action = record.action == "on" ? "Heat on" : "Heat off"
        switch result.outcome {
        case "accepted": record.message = "\(action) request accepted. Check the car to confirm."
        case "rejected": record.message = "\(action) request rejected. Check the car’s supply voltage and whether another request is busy."
        default: record.message = "Delivery uncertain. Check the car or look up this request. Nothing will be resent automatically."
        }
    }
    private func validate(_ sample: LeafyClient.Status) throws {
        let battery = sample.tractionBattery
        guard sample.apiVersion == 1, sample.deviceReachable,
              ["fresh", "stale", "unavailable", "unsupported"].contains(battery.availability),
              battery.socPercent.map({ $0.isFinite && (0...100).contains($0) }) ?? true,
              battery.ageSeconds.map({ $0 >= 0 && $0 < 315360000 }) ?? true,
              (battery.socPercent == nil) == (battery.ageSeconds == nil),
              sample.protectedSupplyVolts.map({ $0.isFinite && (0...100).contains($0) }) ?? true else {
            throw LeafyClient.Failure.unreadableResponse
        }
    }
    private func describe(_ error: Error) -> String {
        if let error = error as? SetupError { return error.localizedDescription }
        if case LeafyClient.Failure.http(401, _) = error { return "App token not accepted. Check your server’s app token." }
        if case LeafyClient.Failure.http(503, _) = error { return "The server cannot reach Leafy. Check the car’s power and Wi-Fi." }
        return "Could not connect. Check the server address, home Wi-Fi and local network permission."
    }
}
