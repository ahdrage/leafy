import SwiftUI

private enum Theme {
    static let forest = Color(red: 0.075, green: 0.23, blue: 0.17)
    static let mint = Color(red: 0.72, green: 0.91, blue: 0.70)
    static let orange = Color(red: 0.96, green: 0.48, blue: 0.25)
    static let background = Color(uiColor: .systemGroupedBackground)
    static let card = Color(uiColor: .secondarySystemGroupedBackground)
}
struct LeafyView: View {
    @ObservedObject var model: LeafyModel
    @Environment(\.scenePhase) private var scenePhase
    @State private var settings = false
    @State private var confirmOn = false
    @State private var confirmReviewed = false
    var body: some View {
        NavigationStack {
            ScrollView {
                VStack(alignment: .leading, spacing: 24) {
                    HStack(spacing: 8) {
                        Image(systemName: "leaf.fill").foregroundStyle(Theme.forest)
                        Text("Leafy").font(.largeTitle.bold())
                        Spacer()
                        #if targetEnvironment(simulator)
                        Text("SIMULATOR").font(.caption2.bold()).foregroundStyle(.secondary)
                        #endif
                        if model.connection != nil {
                            Button { settings = true } label: { Image(systemName: "gearshape").font(.title3).padding(10) }
                                .tint(.primary).accessibilityLabel("Connection settings")
                        }
                    }
                    if model.connection == nil { ConnectionView(model: model) }
                    else { dashboard }
                }
                .padding(24).frame(maxWidth: 620).frame(maxWidth: .infinity)
            }
            .background(Theme.background)
            .toolbar(.hidden, for: .navigationBar)
            .refreshable { await model.refresh() }
            .sheet(isPresented: $settings) { settingsView }
            .alert("Warm up your Leaf?", isPresented: $confirmOn) {
                Button("Cancel", role: .cancel) {}
                Button("Request heat") { Task { await model.send(.on) } }
            } message: { Text("Send a Heat On request now. Leafy requests Off after 15 minutes. Check the car to confirm it responds.") }
            .alert("Have you checked the car?", isPresented: $confirmReviewed) {
                Button("Cancel", role: .cancel) {}
                Button("I’ve checked the car") { model.acknowledgeOutcome() }
            } message: { Text("This clears the uncertain-request warning so you can make a new deliberate request. It does not send a command.") }
            .task(id: scenePhase) {
                guard scenePhase == .active else { return }
                while !Task.isCancelled {
                    await model.refresh()
                    do { try await Task.sleep(for: .seconds(5)) } catch { break }
                }
            }
            .onChange(of: scenePhase) { _, value in if value != .active { model.suspend() } }
        }
    }
    private var dashboard: some View {
        VStack(alignment: .leading, spacing: 22) {
            TimelineView(.periodic(from: .now, by: 1)) { _ in
                VStack(alignment: .leading, spacing: 18) {
                    HStack {
                        Label(model.isOnline ? "Connected at home" : "Connection unavailable", systemImage: model.isOnline ? "wifi" : "wifi.slash")
                            .font(.subheadline.weight(.medium))
                            .foregroundStyle(model.isOnline ? Theme.forest : .secondary)
                        Spacer()
                        if model.refreshing { ProgressView().controlSize(.small) }
                    }
                    VStack(alignment: .leading, spacing: 12) {
                        HStack {
                            Text("MAIN BATTERY").font(.caption.weight(.semibold)).tracking(1.6)
                            Spacer()
                            Image(systemName: "car.side.fill").font(.system(size: 38)).foregroundStyle(Theme.mint)
                        }
                        Text(model.batteryText).font(.system(size: 70, weight: .medium, design: .rounded)).minimumScaleFactor(0.6)
                            .accessibilityIdentifier("batteryValue")
                        Text(model.batteryDetail).font(.subheadline).foregroundStyle(Theme.mint)
                            .accessibilityIdentifier("batteryAge")
                        Text("BMS reading · may differ from the dashboard")
                            .font(.caption).foregroundStyle(.white.opacity(0.8))
                    }
                    .padding(24).frame(maxWidth: .infinity, alignment: .leading)
                    .foregroundStyle(.white)
                    .background(LinearGradient(colors: [Theme.forest, Color(red: 0.12, green: 0.34, blue: 0.25)], startPoint: .topLeading, endPoint: .bottomTrailing), in: RoundedRectangle(cornerRadius: 26))
                    HStack {
                        Label("Protected supply", systemImage: "bolt.batteryblock")
                        Spacer()
                        Text(model.status?.protectedSupplyVolts.map { String(format: "%.2f V", $0) } ?? "—")
                            .fontWeight(.semibold).monospacedDigit()
                    }.font(.subheadline).padding(18).background(Theme.card, in: RoundedRectangle(cornerRadius: 18))
                    VStack(alignment: .leading, spacing: 14) {
                        Text("A warmer start").font(.title2.bold())
                        Text("Request cabin heating before you head out.").font(.subheadline).foregroundStyle(.secondary)
                        Button { confirmOn = true } label: {
                            Label(model.sending ? "Sending request…" : "Heat on", systemImage: "heat.waves")
                                .font(.headline).frame(maxWidth: .infinity).padding(.vertical, 16)
                        }
                        .buttonStyle(.plain).foregroundStyle(.black)
                        .background(model.canHeatOn ? Theme.orange : Color.secondary.opacity(0.18), in: RoundedRectangle(cornerRadius: 18))
                        .disabled(!model.canHeatOn).accessibilityIdentifier("heatOn")
                        Button { Task { await model.send(.off) } } label: {
                            Label("Heat off", systemImage: "power").font(.headline).frame(maxWidth: .infinity).padding(.vertical, 15)
                        }
                        .buttonStyle(.plain).background(Theme.card, in: RoundedRectangle(cornerRadius: 18))
                        .disabled(!model.canHeatOff).accessibilityIdentifier("heatOff")
                        Text(heaterNote).font(.footnote).foregroundStyle(.secondary)
                    }
                }
            }
            if !model.message.isEmpty {
                Label(model.message, systemImage: "exclamationmark.circle")
                    .font(.subheadline).foregroundStyle(.orange).accessibilityIdentifier("connectionMessage")
            }
            if let command = model.latestCommand {
                VStack(alignment: .leading, spacing: 12) {
                    Label("Latest request", systemImage: command.unresolved ? "questionmark.circle" : "paperplane")
                        .font(.headline)
                    Text(command.message).font(.subheadline).accessibilityIdentifier("commandMessage")
                    if command.unresolved {
                        Button("Check request result") { Task { await model.checkCommand() } }
                            .disabled(model.checkingCommand || model.sending)
                        Button("I’ve checked the car…") { confirmReviewed = true }
                            .disabled(model.checkingCommand || model.sending)
                    }
                }.padding(18).frame(maxWidth: .infinity, alignment: .leading)
                    .background(Theme.card, in: RoundedRectangle(cornerRadius: 18))
            }
            Button { Task { await model.refresh() } } label: { Label("Refresh status", systemImage: "arrow.clockwise") }
                .font(.subheadline).disabled(model.refreshing)
            Text("Home Wi-Fi only. Keep your home server running. Battery readings may stop updating while the car sleeps.")
                .font(.footnote).foregroundStyle(.secondary)
        }.tint(Theme.forest)
    }
    private var heaterNote: String {
        guard let status = model.status else { return "Connect to Leafy before sending a request." }
        if !status.canWriteEnabled { return "Heater controls are locked for commissioning." }
        if status.lastCommandError != 0 { return "Leafy reported a command error (\(status.lastCommandError)). Check the car." }
        if status.requestBusy { return "Leafy is sending a request. Actual heater state is unverified." }
        if status.heater.requested { return "Heat requested or outcome uncertain. Check the car to confirm." }
        return "No local heat request active. Actual heater state is unverified."
    }
    private var settingsView: some View {
        NavigationStack {
            Form {
                Section("Home server") {
                    Text(model.connection?.address ?? "").textSelection(.enabled)
                    Text("Your app token is saved in this device’s Keychain.").font(.footnote).foregroundStyle(.secondary)
                }
                Section {
                    Text("The server connects to Leafy. This address is your home server’s address, not the board’s web page.")
                    Text("BMS battery percentage is available through this API. The separate dashboard percentage is currently shown only on Leafy’s website.")
                }.font(.subheadline)
                Section {
                    Button("Forget connection", role: .destructive) { model.forget(); if model.connection == nil { settings = false } }
                        .disabled(model.sending || model.checkingCommand)
                } footer: { Text("This removes the saved server and token. The last request record is retained to avoid losing an uncertain result.") }
            }.navigationTitle("Connection").navigationBarTitleDisplayMode(.inline)
                .toolbar { ToolbarItem(placement: .confirmationAction) { Button("Done") { settings = false } } }
        }
    }
}
private struct ConnectionView: View {
    @ObservedObject var model: LeafyModel
    @State private var address = ""
    @State private var token = ""
    @FocusState private var focused: Bool
    var body: some View {
        VStack(alignment: .leading, spacing: 24) {
            Image(systemName: "car.side.fill").font(.system(size: 54)).foregroundStyle(Theme.forest).padding(.top, 30)
            Text("Connect your Leafy").font(.largeTitle.bold())
            Text("A warm car, before you step outside.").font(.title3).foregroundStyle(.secondary)
            VStack(alignment: .leading, spacing: 16) {
                Text("HOME SERVER").font(.caption.bold()).foregroundStyle(.secondary).tracking(1)
                TextField("Server address", text: $address)
                    .keyboardType(.URL).textInputAutocapitalization(.never).autocorrectionDisabled().focused($focused)
                    .padding(16).background(Theme.card, in: RoundedRectangle(cornerRadius: 14))
                    .accessibilityIdentifier("serverAddress")
                Text("For example: http://192.168.1.50:8787").font(.caption).foregroundStyle(.secondary)
                SecureField("App token", text: $token).textInputAutocapitalization(.never).autocorrectionDisabled().focused($focused)
                    .padding(16).background(Theme.card, in: RoundedRectangle(cornerRadius: 14))
                    .accessibilityIdentifier("appToken")
                Text("Use the API server’s app token, not the board’s control key. It will be saved securely on this iPhone.")
                    .font(.footnote).foregroundStyle(.secondary)
                Button {
                    focused = false
                    Task { await model.connect(address: address, token: token); if model.connection != nil { token = "" } }
                } label: {
                    HStack { if model.connecting { ProgressView().tint(.white) }; Text(model.connecting ? "Connecting…" : "Connect") }
                        .font(.headline).frame(maxWidth: .infinity).padding(.vertical, 16)
                }.buttonStyle(.plain).foregroundStyle(.white).background(Theme.forest, in: RoundedRectangle(cornerRadius: 16))
                    .disabled(model.connecting || address.isEmpty || token.isEmpty)
                if !model.message.isEmpty { Text(model.message).font(.subheadline).foregroundStyle(.orange).accessibilityIdentifier("setupError") }
            }
            Label("Use your trusted home Wi-Fi. Your server must be running and able to reach the car.", systemImage: "wifi")
                .font(.footnote).foregroundStyle(.secondary)
        }
    }
}
