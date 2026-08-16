import { runtimeUrl } from "./platform";

export type ZoneRect = { x: number; y: number; w: number; h: number };
export type Zones = Record<string, ZoneRect>;

export type ZonesResponse = {
  ok: boolean;
  zones: Zones;
  path: string;
  reloaded?: boolean;
};

export async function fetchZones(): Promise<ZonesResponse | null> {
  try {
    const res = await fetch(`${runtimeUrl()}/gaze/zones`);
    if (!res.ok) return null;
    return (await res.json()) as ZonesResponse;
  } catch {
    return null;
  }
}

export async function saveZones(zones: Zones): Promise<ZonesResponse | null> {
  try {
    const res = await fetch(`${runtimeUrl()}/gaze/zones`, {
      method: "PUT",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ zones }),
    });
    if (!res.ok) return null;
    return (await res.json()) as ZonesResponse;
  } catch {
    return null;
  }
}