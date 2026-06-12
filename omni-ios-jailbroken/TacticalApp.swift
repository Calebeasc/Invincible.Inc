import SwiftUI

/**
 * OMNI-iOS-JAILBROKEN: Core Tactical Shell
 * Optimized for iPhone SE (1st Gen) - 4-inch display.
 * Gotham Aesthetic | Sovereign Logic
 */

@main
struct OMNIApp: App {
    var body: some Scene {
        WindowGroup {
            MainTacticalView()
                .preferredColorScheme(.dark)
        }
    }
}

struct MainTacticalView: View {
    @State private var selectedTab = 0
    
    var body: some View {
        TabView(selection: $selectedTab) {
            DashboardView()
                .tabItem {
                    Image(systemName: "gauge")
                    Text("DASH")
                }.tag(0)
            
            NFCCopierView()
                .tabItem {
                    Image(systemName: "antenna.radiowaves.left.and.right")
                    Text("NFC")
                }.tag(1)
            
            SignalSniperView()
                .tabItem {
                    Image(systemName: "dot.radiowaves.left.and.right")
                    Text("RADIO")
                }.tag(2)
            
            SystemStatusView()
                .tabItem {
                    Image(systemName: "terminal")
                    Text("SYS")
                }.tag(3)
        }
        .accentColor(.blue)
    }
}

// Optimized for 4-inch screen density
struct DashboardView: View {
    var body: some View {
        VStack(alignment: .leading, spacing: 8) {
            HeaderView(title: "OMNI KINETIC NODE", subtitle: "A9-SE // LATTICE ACTIVE")
            
            ScrollView {
                VStack(spacing: 6) {
                    StatCard(label: "UPLINK", value: "CONNECTED", color: .green)
                    StatCard(label: "NFC CHIP", value: "GOD MODE", color: .blue)
                    StatCard(label: "WI-FI", value: "PROMISCUOUS", color: .orange)
                    StatCard(label: "BATTERY", value: "88% / 32C", color: .white)
                }
            }
            
            Spacer()
        }
        .padding(.horizontal, 16)
        .padding(.top, 12)
        .background(Color.black)
    }
}

struct HeaderView: View {
    let title: String
    let subtitle: String
    
    var body: some View {
        VStack(alignment: .leading, spacing: 2) {
            Text(title)
                .font(.custom("Courier New", size: 18))
                .fontWeight(.bold)
                .tracking(2)
            Text(subtitle)
                .font(.custom("Courier New", size: 8))
                .foregroundColor(.gray)
                .tracking(1)
            Rectangle()
                .frame(height: 1)
                .foregroundColor(Color(white: 0.1))
        }
    }
}

struct StatCard: View {
    let label: String
    let value: String
    let color: Color
    
    var body: some View {
        HStack {
            Text(label)
                .font(.custom("Courier New", size: 10))
                .foregroundColor(.gray)
            Spacer()
            Text(value)
                .font(.custom("Courier New", size: 10))
                .fontWeight(.bold)
                .foregroundColor(color)
        }
        .padding(10)
        .background(Color(white: 0.05))
        .border(Color(white: 0.1), width: 1)
    }
}

// Mock views for architectural representation
struct NFCCopierView: View { var body: some View { Text("NFC COPIER") } }
struct SignalSniperView: View { var body: some View { Text("SIGNAL SNIPER") } }
struct SystemStatusView: View { var body: some View { Text("SYSTEM") } }
