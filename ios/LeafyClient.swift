import Foundation

// Store apiToken in the iOS Keychain, never in source code or UserDefaults.
// Keep one client per configured server. HTTPS is required outside a trusted LAN.
public final class LeafyClient: @unchecked Sendable {
    public struct Status: Decodable, Sendable {
        public let apiVersion: Int
        public let deviceReachable: Bool
        public let observedAt: String
        public let protectedSupplyVolts: Double?
        public let canWriteEnabled: Bool
        public let requestBusy: Bool
        public let lastCommandError: Int
        public let heater: Heater
        public let tractionBattery: Battery
    }
    public struct Heater: Decodable, Sendable {
        public let requested: Bool
        public let actualState: String // "unknown": do not label this "heater running".
    }
    public struct Battery: Decodable, Sendable {
        public let socPercent: Double?
        public let ageSeconds: Int?
        public let availability: String // fresh, stale, unavailable, unsupported
        public let source: String?
    }
    public enum Action: String, Encodable, Sendable { case on, off }
    public struct Command: Encodable, Sendable {
        public let action: Action
        public let issuedAt: String
        public init(_ action: Action) {
            self.action = action
            self.issuedAt = ISO8601DateFormatter().string(from: Date())
        }
    }
    public struct CommandResult: Decodable, Sendable {
        public let commandId: String
        public let action: String
        public let outcome: String // accepted, rejected, pending, unknown
        public let actualHeaterState: String
        public let createdAt: String
        public let message: String
    }
    public enum Failure: Error {
        case invalidServerURL
        case http(Int, String)
        case unreadableResponse
        // Persist this ID and query commandResult(id:). Do not create a new On.
        case deliveryUnknown(UUID)
    }
    private struct ErrorBody: Decodable { let error: String; let message: String? }
    private final class NoRedirects: NSObject, URLSessionTaskDelegate, @unchecked Sendable {
        func urlSession(_ session: URLSession, task: URLSessionTask,
                        willPerformHTTPRedirection response: HTTPURLResponse,
                        newRequest request: URLRequest,
                        completionHandler: @escaping @Sendable (URLRequest?) -> Void) {
            completionHandler(nil) // Do not forward the bearer token to redirects.
        }
    }
    private let baseURL: URL
    private let token: String
    private let session: URLSession
    public init(baseURL: URL, apiToken: String) throws {
        guard ["http", "https"].contains(baseURL.scheme), baseURL.host != nil,
              baseURL.user == nil, baseURL.password == nil,
              baseURL.query == nil, baseURL.fragment == nil,
              baseURL.path.isEmpty || baseURL.path == "/" else { throw Failure.invalidServerURL }
        self.baseURL = baseURL
        self.token = apiToken
        let config = URLSessionConfiguration.ephemeral
        config.waitsForConnectivity = false // No delayed/offline command delivery.
        config.timeoutIntervalForRequest = 10
        config.timeoutIntervalForResource = 12
        config.httpCookieStorage = nil
        config.urlCache = nil
        self.session = URLSession(configuration: config, delegate: NoRedirects(), delegateQueue: nil)
    }
    public func close() { session.invalidateAndCancel() }
    private func request(_ path: String) -> URLRequest {
        var r = URLRequest(url: baseURL.appendingPathComponent(path))
        r.setValue("Bearer " + token, forHTTPHeaderField: "Authorization")
        r.setValue("application/json", forHTTPHeaderField: "Accept")
        r.cachePolicy = .reloadIgnoringLocalCacheData
        return r
    }
    private func checked<T: Decodable>(_ type: T.Type, data: Data, response: URLResponse) throws -> T {
        guard let response = response as? HTTPURLResponse else { throw Failure.unreadableResponse }
        guard (200..<300).contains(response.statusCode) else {
            let body = try? JSONDecoder().decode(ErrorBody.self, from: data)
            throw Failure.http(response.statusCode, body?.message ?? body?.error ?? "Request failed")
        }
        return try JSONDecoder().decode(T.self, from: data)
    }
    public func status() async throws -> Status {
        let (data, response) = try await session.data(for: request("v1/status"))
        return try checked(Status.self, data: data, response: response)
    }
    // Generate/store id and Command once at the user's tap, before this call.
    // A duplicate transport attempt must reuse BOTH, not create a new intent.
    public func send(_ command: Command, id: UUID) async throws -> CommandResult {
        var r = request("v1/heater/commands")
        r.httpMethod = "POST"
        r.setValue("application/json", forHTTPHeaderField: "Content-Type")
        r.setValue(id.uuidString.lowercased(), forHTTPHeaderField: "Idempotency-Key")
        r.httpBody = try JSONEncoder().encode(command)
        let data: Data, response: URLResponse
        do { (data, response) = try await session.data(for: r) }
        catch { throw Failure.deliveryUnknown(id) }
        // Rejected/unknown command results can carry a non-2xx HTTP status.
        if let result = try? JSONDecoder().decode(CommandResult.self, from: data) { return result }
        if let http = response as? HTTPURLResponse, (400..<500).contains(http.statusCode) {
            return try checked(CommandResult.self, data: data, response: response)
        }
        throw Failure.deliveryUnknown(id)
    }
    public func commandResult(id: UUID) async throws -> CommandResult {
        let (data, response) = try await session.data(for: request("v1/commands/" + id.uuidString.lowercased()))
        return try checked(CommandResult.self, data: data, response: response)
    }
}
