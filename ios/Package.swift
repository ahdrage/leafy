// swift-tools-version: 5.9
import PackageDescription
let package = Package(name: "Leafy", platforms: [.macOS(.v13)], products: [.library(name: "Leafy", targets: ["Leafy"])], targets: [
    .target(name: "Leafy", path: ".", exclude: ["LeafyTests", "LeafyUITests", "Leafy.xcodeproj", "build", "verification", "scripts", "project.yml", "README.md", "Leafy/Info.plist", "Leafy/LeafyApp.swift", "Leafy/LeafyView.swift", "Leafy/KeychainStore.swift"], sources: ["Leafy/Model.swift", "LeafyClient.swift"]),
    .testTarget(name: "LeafyTests", dependencies: ["Leafy"], path: "LeafyTests")
])
