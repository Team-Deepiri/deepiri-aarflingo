import SwiftUI

struct ContentView: View {
    @StateObject private var vm = IntentViewModel()

    var body: some View {
        NavigationStack {
            VStack(spacing: 16) {
                Text("AARF Pocket")
                    .font(.title2)
                Label(vm.intent, systemImage: "pawprint")
                Text("Emotion: \(vm.emotion)")
                Text("Behavior: \(vm.behavior)")
                Text(String(format: "Confidence: %.0f%%", vm.confidence * 100))
                Text("Gate: \(vm.gateStatus)")
                    .foregroundStyle(vm.gateStatus == "pass" ? .green : .orange)
                Button("Run inference") {
                    vm.runInference()
                }
            }
            .padding()
        }
    }
}

#Preview {
    ContentView()
}
