import React from "react";

export function CameraView() {
  return (
    <section className="card">
      <h2>Camera</h2>
      <p>Connect capture device or load clip JSON from ingest.</p>
      <div className="camera-placeholder">No signal</div>
    </section>
  );
}
