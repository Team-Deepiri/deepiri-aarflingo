import React, { useState } from "react";
import aarflingoLogo from "@brand/Aarflingo-logo.png";
import { LiveView } from "./components/CameraView";
import { HistoryView } from "./components/HistoryView";
import { IntentDashboard } from "./components/IntentDashboard";
import { VoiceView } from "./components/VoiceView";
import { DogProfileView } from "./components/DogProfileView";

type Tab = "dashboard" | "camera" | "history" | "voice" | "dog";

const NAV: { id: Tab; label: string; icon: string }[] = [
  { id: "camera", label: "Live", icon: "◉" },
  { id: "dashboard", label: "Dashboard", icon: "▤" },
  { id: "history", label: "History", icon: "≋" },
  { id: "voice", label: "Voice", icon: "♪" },
  { id: "dog", label: "Dog profile", icon: "🐾" },
];

export function App() {
  const [tab, setTab] = useState<Tab>("camera");

  return (
    <div className="app-shell">
      <aside className="sidebar">
        <div className="brand">
          <img src={aarflingoLogo} alt="Aarflingo" className="brand-logo" />
          <div className="brand-text">
            <h1>Aarflingo</h1>
            <p className="brand-sub">canine intent studio</p>
          </div>
        </div>
        <nav className="sidebar-nav">
          {NAV.map(({ id, label, icon }) => (
            <button
              key={id}
              type="button"
              className={tab === id ? "nav-item active" : "nav-item"}
              onClick={() => setTab(id)}
            >
              <span className="nav-icon" aria-hidden="true">{icon}</span>
              <span>{label}</span>
            </button>
          ))}
        </nav>
        <div className="sidebar-foot">
          <p className="meta">Deepiri · AARF runtime</p>
          <p className="meta">TriadNet intent forecast</p>
        </div>
      </aside>
      <main className="app-main">
        {tab === "dashboard" && <IntentDashboard />}
        {tab === "camera" && <LiveView />}
        {tab === "history" && <HistoryView />}
        {tab === "voice" && <VoiceView />}
        {tab === "dog" && <DogProfileView />}
      </main>
    </div>
  );
}
