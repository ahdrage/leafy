import Foundation
import Security

struct KeychainStore: LeafyStore {
    private let service = "no.leafy.app.connection"
    func connection() throws -> Connection? { try read("connection") }
    func save(connection: Connection) throws { try write(connection, account: "connection") }
    func record() throws -> CommandRecord? { try read("latest-command") }
    func save(record: CommandRecord) throws { try write(record, account: "latest-command") }
    func forgetConnection() throws {
        let result = SecItemDelete(query("connection") as CFDictionary)
        guard result == errSecSuccess || result == errSecItemNotFound else { throw StorageFailure.status(result) }
        // Retain the latest command: forgetting credentials must not erase an uncertain delivery.
    }
    private func query(_ account: String) -> [String: Any] {
        [kSecClass as String: kSecClassGenericPassword, kSecAttrService as String: service,
         kSecAttrAccount as String: account, kSecAttrSynchronizable as String: false]
    }
    private func read<T: Decodable>(_ account: String) throws -> T? {
        var request = query(account)
        request[kSecReturnData as String] = true
        request[kSecMatchLimit as String] = kSecMatchLimitOne
        var item: CFTypeRef?
        let result = SecItemCopyMatching(request as CFDictionary, &item)
        if result == errSecItemNotFound { return nil }
        guard result == errSecSuccess, let data = item as? Data else { throw StorageFailure.status(result) }
        return try JSONDecoder().decode(T.self, from: data)
    }
    private func write<T: Encodable>(_ value: T, account: String) throws {
        let attributes: [String: Any] = [kSecValueData as String: try JSONEncoder().encode(value),
            kSecAttrAccessible as String: kSecAttrAccessibleWhenUnlockedThisDeviceOnly]
        let result = SecItemUpdate(query(account) as CFDictionary, attributes as CFDictionary)
        if result == errSecItemNotFound {
            var item = query(account); item.merge(attributes) { _, new in new }
            let added = SecItemAdd(item as CFDictionary, nil)
            guard added == errSecSuccess else { throw StorageFailure.status(added) }
        } else if result != errSecSuccess { throw StorageFailure.status(result) }
    }
    private enum StorageFailure: Error { case status(OSStatus) }
}
