import SwiftUI

@main struct LeafyApp: App {
    @StateObject private var model = LeafyModel(store: KeychainStore(), makeClient: {
        try LeafyClient(baseURL: URL(string: $0.address)!, apiToken: $0.token)
    })
    var body: some Scene { WindowGroup { LeafyView(model: model) } }
}
