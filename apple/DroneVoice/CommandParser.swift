// CommandParser.swift — text -> DroneCommand, two ways.
//
// Phase 2: a bilingual keyword parser (mirrors Lesson 9 / bridge/parse_text.py) —
//   offline, deterministic, the fallback when the LLM is unavailable.
// Phase 3: Apple's on-device Foundation Model with guided generation — it parses
//   free natural language ("nudge forward about two metres") and, because the
//   output is constrained to @Generable DroneCommand, it can ONLY return a
//   schema-valid command. This is the course's "counter-example": here a general
//   model + structured constraints beats training your own small one (Lesson 28).

import Foundation
#if canImport(FoundationModels)
import FoundationModels
#endif

enum CommandParser {
    // Bilingual keyword -> action; turn/land/takeoff before single-word moves.
    private static let keywords: [(DroneAction, [String])] = [
        (.turnLeft, ["turn left", "左轉", "左转"]),
        (.turnRight, ["turn right", "右轉", "右转"]),
        (.takeoff, ["takeoff", "take off", "起飛", "起飞"]),
        (.emergencyStop, ["emergency", "緊急", "紧急"]),
        (.land, ["land", "降落"]),
        (.forward, ["forward", "前進", "前进", "往前", "向前"]),
        (.back, ["back", "後退", "后退"]),
        (.up, ["up", "上升", "向上"]),
        (.down, ["down", "下降", "向下"]),
        (.left, ["left", "向左", "左"]),
        (.right, ["right", "向右", "右"]),
        (.stop, ["stop", "hover", "停"]),
    ]

    /// Phase 2 — offline keyword parse. Returns nil if nothing matched.
    static func keyword(_ text: String) -> DroneCommand? {
        let t = text.lowercased()
        guard let (action, _) = keywords.first(where: { _, kws in kws.contains { t.contains($0) } })
        else { return nil }
        let number = firstNumber(in: text)
        switch action {
        case .turnLeft, .turnRight:
            return DroneCommand(action: action, distance: nil, degrees: number)
        case .forward, .back, .left, .right, .up, .down:
            return DroneCommand(action: action, distance: number, degrees: nil)
        default:
            return DroneCommand(action: action, distance: nil, degrees: nil)
        }
    }

    private static func firstNumber(in text: String) -> Double? {
        let scanner = Scanner(string: text)
        _ = scanner.scanUpToCharacters(from: .decimalDigits)
        return scanner.scanDouble()
    }

    /// Phase 3 — on-device LLM, guaranteed schema-valid output. Falls back to the
    /// keyword parser if Foundation Models isn't available on this device.
    static func parse(_ text: String) async -> DroneCommand? {
        #if canImport(FoundationModels)
        if #available(iOS 26, *) {
            let session = LanguageModelSession()
            let prompt = "Convert this drone flight instruction into a command: \(text)"
            if let result = try? await session.respond(to: prompt, generating: DroneCommand.self) {
                return result.content
            }
        }
        #endif
        return keyword(text)
    }
}
