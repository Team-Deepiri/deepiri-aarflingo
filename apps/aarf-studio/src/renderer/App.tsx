import React, { useState } from "react";
import { CameraView } from "./components/CameraView";
import { HistoryView } from "./components/HistoryView";
import { IntentDashboard } from "./components/IntentDashboard";

export function App() {
  const [tab, setTab] = useState<"dashboard" | "camera" | "history">("dashboard");

  return (
    <div className="app">
      <header>
        <div className="brand">
          <img src="/logo.png" alt="Deepiri" className="brand-logo" />
          <div className="brand-text">
            <h1>AARF Studio</h1>
            <p className="brand-sub">DeepIRI · Adaptive Animal Response Framework</p>
          </div>
        </div>
        <nav>
          <button onClick={() => setTab("dashboard")}>Dashboard</button>
          <button onClick={() => setTab("camera")}>Camera</button>
          <button onClick={() => setTab("history")}>History</button>
        </nav>
      </header>
      <main>
        {tab === "dashboard" && <IntentDashboard />}
        {tab === "camera" && <CameraView />}
        {tab === "history" && <HistoryView />}
      </main>
    </div>
  );
}
