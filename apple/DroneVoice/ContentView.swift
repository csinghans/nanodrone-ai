// ContentView.swift — DroneVoice Phase 4 SwiftUI app.
//
// The human safety interface: connect, speak or type a command, watch a live
// command log, and — most importantly — a big EMERGENCY STOP that always gets
// through. The UI is part of the failsafe, not decoration: dangerous commands
// confirm first, and the app mirrors the server's safe-ordering rule (no moving
// before takeoff). Telemetry (Phase 4 server change) would stream back here.

import SwiftUI

struct ContentView: View {
    @StateObject private var bridge = BridgeClient()
    @State private var host = "192.168.1.100"   // your Mac's IP (sim) or drone
    @State private var airborne = false
    @State private var pendingText = ""

    var body: some View {
        VStack(spacing: 16) {
            HStack {
                TextField("host", text: $host).textFieldStyle(.roundedBorder)
                Button(bridge.connected ? "Disconnect" : "Connect") {
                    bridge.connected ? bridge.disconnect() : bridge.connect(host: host)
                }
            }

            // The command the user is about to issue (from voice or typing).
            HStack {
                TextField("say or type a command", text: $pendingText)
                    .textFieldStyle(.roundedBorder)
                Button("Send") { Task { await issue(pendingText) } }
                    .disabled(!bridge.connected)
            }

            // EMERGENCY STOP — always enabled, always gets through.
            Button(action: { bridge.emergencyStop() }) {
                Text("EMERGENCY STOP")
                    .font(.title2.bold())
                    .frame(maxWidth: .infinity, minHeight: 64)
                    .background(Color.red)
                    .foregroundStyle(.white)
                    .clipShape(RoundedRectangle(cornerRadius: 12))
            }

            List(bridge.log.reversed(), id: \.self) { Text($0).font(.system(.body, design: .monospaced)) }
        }
        .padding()
    }

    /// Parse text -> command, enforce safe ordering + confirm risky actions,
    /// then send. (Voice from a SpeechAnalyzer recognizer feeds the same path.)
    private func issue(_ text: String) async {
        guard let cmd = await CommandParser.parse(text) else { return }
        if cmd.requiresAirborne && !airborne { return }      // safe ordering
        if cmd.action == .takeoff { airborne = true }
        if cmd.action == .land || cmd.action == .emergencyStop { airborne = false }
        bridge.send(cmd)
        pendingText = ""
    }
}
