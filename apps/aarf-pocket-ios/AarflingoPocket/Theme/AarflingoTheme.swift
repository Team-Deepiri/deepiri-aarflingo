import SwiftUI

enum AarflingoTheme {
    static let bg = Color(red: 0.04, green: 0.055, blue: 0.07)
    static let card = Color(red: 0.08, green: 0.12, blue: 0.16)
    static let border = Color(red: 0.16, green: 0.22, blue: 0.28)
    static let text = Color(red: 0.91, green: 0.93, blue: 0.96)
    static let muted = Color(red: 0.56, green: 0.64, blue: 0.71)
    static let accent = Color(red: 0.24, green: 0.84, blue: 0.55)
    static let warn = Color(red: 0.94, green: 0.78, blue: 0.45)
    static let danger = Color(red: 0.94, green: 0.44, blue: 0.47)
    static let info = Color(red: 0.42, green: 0.71, blue: 1.0)

    static let gradient = LinearGradient(
        colors: [Color(red: 0.1, green: 0.16, blue: 0.21), bg],
        startPoint: .topLeading,
        endPoint: .bottomTrailing
    )
}

struct CardStyle: ViewModifier {
    func body(content: Content) -> some View {
        content
            .padding()
            .background(AarflingoTheme.card)
            .overlay(RoundedRectangle(cornerRadius: 14).stroke(AarflingoTheme.border, lineWidth: 1))
            .clipShape(RoundedRectangle(cornerRadius: 14))
    }
}

extension View {
    func aarflingoCard() -> some View { modifier(CardStyle()) }
}
