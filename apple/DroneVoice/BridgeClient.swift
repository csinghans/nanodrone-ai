// BridgeClient.swift — send commands to the bridge / a real drone over TCP.
//
// Speaks the exact same newline-JSON protocol as bridge/send.py, to the same
// port 9000 — whether the other end is bridge/sim_server.py, hardware/
// tello_server.py, or hardware/crazyflie_server.py. Only the server changes.

import Foundation
import Network

final class BridgeClient: ObservableObject {
    @Published var connected = false
    @Published var log: [String] = []
    private var conn: NWConnection?

    func connect(host: String, port: UInt16 = 9000) {
        let c = NWConnection(host: .init(host), port: .init(rawValue: port)!, using: .tcp)
        c.stateUpdateHandler = { [weak self] state in
            DispatchQueue.main.async { self?.connected = (state == .ready) }
        }
        c.start(queue: .global())
        conn = c
    }

    func send(_ command: DroneCommand) {
        let line = command.jsonLine()
        conn?.send(content: line.data(using: .utf8), completion: .contentProcessed { _ in })
        DispatchQueue.main.async { self.log.append(line.trimmingCharacters(in: .whitespacesAndNewlines)) }
    }

    /// The one command that must always get through.
    func emergencyStop() {
        send(DroneCommand(action: .emergencyStop, distance: nil, degrees: nil))
    }

    func disconnect() {
        conn?.cancel()
        conn = nil
        DispatchQueue.main.async { self.connected = false }
    }
}
