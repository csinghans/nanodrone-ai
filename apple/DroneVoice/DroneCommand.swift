// DroneCommand.swift — the flight protocol, mirrored from nanodrone/protocol.py.
//
// This is the single Swift source of truth for the 13 actions the bridge accepts.
// Phase 3 makes it a guided-generation target so the on-device LLM can ONLY emit
// a schema-valid command. jsonLine() is byte-identical to bridge/send.py.
//
// NOTE: requires the FoundationModels framework (iOS 26+, Apple-Intelligence
// devices). API names reflect WWDC25 / knowledge cutoff Jan 2026 — confirm
// against the current Apple docs in Xcode before relying on them.

import Foundation
#if canImport(FoundationModels)
import FoundationModels
#endif

/// The 13 agreed actions (must match nanodrone.protocol.ACTIONS exactly).
enum DroneAction: String, Codable, CaseIterable {
    case takeoff, land, forward, back, left, right, up, down
    case turnLeft = "turn_left"
    case turnRight = "turn_right"
    case stop, hover
    case emergencyStop = "emergency_stop"
}

#if canImport(FoundationModels)
@Generable
struct DroneCommand: Codable {
    @Guide(description: "one of the 13 flight actions")
    var action: DroneAction
    @Guide(description: "distance in metres for moves (default 0.5)")
    var distance: Double?
    @Guide(description: "degrees for turns (default 30)")
    var degrees: Double?
}
#else
struct DroneCommand: Codable {
    var action: DroneAction
    var distance: Double?
    var degrees: Double?
}
#endif

extension DroneCommand {
    /// Newline-delimited JSON over TCP — identical to bridge/send.py's wire format.
    func jsonLine() -> String {
        var obj: [String: Any] = ["action": action.rawValue]
        if let d = distance { obj["distance"] = d }
        if let g = degrees { obj["degrees"] = g }
        let data = (try? JSONSerialization.data(withJSONObject: obj)) ?? Data()
        return (String(data: data, encoding: .utf8) ?? "{}") + "\n"
    }

    /// Movement commands need to be airborne first — the app mirrors the
    /// server-side safe-ordering check in bridge/validate_protocol.py.
    var requiresAirborne: Bool {
        switch action {
        case .forward, .back, .left, .right, .up, .down, .turnLeft, .turnRight:
            return true
        default:
            return false
        }
    }
}
