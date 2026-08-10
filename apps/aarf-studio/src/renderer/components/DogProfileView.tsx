import React from "react";

import { useDogProfile } from "../hooks/useDogProfile";
import { TRAIT_LABELS } from "../lib/labels";

export function DogProfileView() {
  const { profile, dirty, saving, error, update, save, refresh } = useDogProfile();

  if (!profile) {
    return (
      <div className="dashboard-grid">
        <section className="card">
          <h2>Dog profile</h2>
          <p className="meta">No profile loaded.</p>
          <button type="button" className="btn" onClick={() => void refresh()}>Retry</button>
        </section>
      </div>
    );
  }

  const traitKeys = profile.trait_keys ?? Object.keys(profile.traits);

  return (
    <div className="dashboard-grid">
      <section className="card">
        <h2>Dog profile</h2>
        <p className="meta">
          Traits persist per dog under <code>artifacts/dog/{profile.dog_id}.json</code>.
        </p>

        <div className="profile-fields">
          <label>
            Name
            <input value={profile.name} onChange={(e) => update({ name: e.target.value })} />
          </label>
          <label>
            Breed
            <input value={profile.breed} onChange={(e) => update({ breed: e.target.value })} />
          </label>
          <label>
            Age (years)
            <input
              type="number"
              step="0.1"
              min="0"
              value={profile.age_years}
              onChange={(e) => update({ age_years: Number(e.target.value) })}
            />
          </label>
          <label>
            Weight (kg)
            <input
              type="number"
              step="0.5"
              min="0"
              value={profile.weight_kg}
              onChange={(e) => update({ weight_kg: Number(e.target.value) })}
            />
          </label>
        </div>

        <p className="eyebrow">Personality archetype</p>
        <div className="personality-picker">
          {(profile.personalities ?? []).map((p) => (
            <button
              key={p}
              type="button"
              className={`btn ${profile.personality === p ? "primary" : ""}`}
              onClick={() => update({ personality: p })}
            >
              {p}
            </button>
          ))}
        </div>

        {error ? <div className="alert alert-error">{error}</div> : null}
        <div className="toolbar">
          <button type="button" className="btn primary" onClick={() => void save()} disabled={!dirty || saving}>
            {saving ? "Saving…" : dirty ? "Save changes" : "Saved"}
          </button>
        </div>
      </section>

      <section className="card">
        <h3>Traits</h3>
        <div className="trait-grid">
          {traitKeys.map((k) => (
            <div key={k} className="trait-edit">
              <div className="trait-edit-head">
                <span>{TRAIT_LABELS[k] || k}</span>
                <strong>{profile.traits[k] ?? 5}</strong>
              </div>
              <input
                type="range"
                min="1"
                max="10"
                step="1"
                value={profile.traits[k] ?? 5}
                onChange={(e) => update({ traits: { ...profile.traits, [k]: Number(e.target.value) } })}
              />
            </div>
          ))}
        </div>
        <p className="meta">
          Baseline HR {profile.baseline_hr_bpm} bpm · tail {profile.baseline_tail_deg}°
        </p>
      </section>
    </div>
  );
}
