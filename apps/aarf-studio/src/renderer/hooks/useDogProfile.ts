import { useCallback, useEffect, useState } from "react";

import type { DogProfile } from "../lib/platform";
import { fetchDogProfile, saveDogProfile } from "../lib/platform";

export function useDogProfile() {
  const [profile, setProfile] = useState<DogProfile | null>(null);
  const [dirty, setDirty] = useState(false);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const refresh = useCallback(async () => {
    const p = await fetchDogProfile();
    if (p) setProfile(p);
  }, []);

  useEffect(() => {
    void refresh();
  }, [refresh]);

  const update = useCallback((patch: Partial<DogProfile>) => {
    setProfile((prev) => (prev ? { ...prev, ...patch } : prev));
    setDirty(true);
  }, []);

  const save = useCallback(async () => {
    if (!profile || !dirty) return;
    setSaving(true);
    setError(null);
    try {
      const updated = await saveDogProfile({
        name: profile.name,
        breed: profile.breed,
        age_years: profile.age_years,
        weight_kg: profile.weight_kg,
        traits: profile.traits,
        personality: profile.personality,
        notes: profile.notes,
      });
      if (updated) {
        setProfile(updated);
        setDirty(false);
      } else {
        setError("Failed to save dog profile");
      }
    } catch {
      setError("Failed to save dog profile");
    } finally {
      setSaving(false);
    }
  }, [profile, dirty]);

  return { profile, dirty, saving, error, refresh, update, save };
}
