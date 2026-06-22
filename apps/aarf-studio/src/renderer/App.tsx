import React, { useState } from "react";
import aarflingoLogo from "@brand/Aarflingo-logo.png";
import { CameraView } from "./components/CameraView";
import { HistoryView } from "./components/HistoryView";
import { IntentDashboard } from "./components/IntentDashboard";

type Tab = "dashboard" | "camera" | "history";

export function App() {
  const [tab, setTab] = useState<Tab>("camera");

  return (
    <div className="app">
      <header className="app-header">
        <div className="brand">
          <img src={aarflingoLogo} alt="Aarflingo" className="brand-logo" />
          <div className="brand-text">
            <h1>Aarflingo Studio</h1>
            <p className="brand-sub">Deepiri · canine intent forecasting</p>
          </div>
        </div>
        <nav className="nav-tabs">
          {(
            [
              ["camera", "Live camera"],
              ["dashboard", "Dashboard"],
              ["history", "History"],
            ] as const
          ).map(([id, label]) => (
            <button
              key={id}
              type="button"
              className={tab === id ? "nav-tab active" : "nav-tab"}
              onClick={() => setTab(id)}
            >
              {label}
            </button>
          ))}
        </nav>
      </header>
      <main className="app-main">
        {tab === "dashboard" && <IntentDashboard />}
        {tab === "camera" && <CameraView />}
        {tab === "history" && <HistoryView />}
      </main>
    </div>
  );
}
