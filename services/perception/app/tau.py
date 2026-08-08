"""Approach geometry toward configured scene zones.

Intent is a destination, not a class: a dog approaching the door is
becoming an "outside" dog, and approaching the toy an "explore/play"
dog. The natural state variables are therefore:

- closing rate  d'_z = v . u_z          (approach speed toward zone z)
- Lee's tau     tau_z = d_z / max(d'_z, eps)   (time-to-contact)
- heading       cos(angle between velocity and the dog->zone vector)

All three depend only on the *relative* geometry between the dog and a
zone, so they are invariant under camera translation (moving/zooming the
camera changes absolute bbox coordinates but not approach intent).
"""
from __future__ import annotations

from dataclasses import dataclass

from .dog_detect import BBox
from .gaze import Zone, load_zones

EPSILON = 1e-6
CLOSING_SCALE = 0.04
TAU_HORIZON = 60.0


@dataclass
class ApproachScores:
    tau: dict[str, float]
    closing: dict[str, float]
    heading: dict[str, float]


def _zone_center(zone: Zone) -> tuple[float, float]:
    return zone.x + zone.w / 2, zone.y + zone.h / 2


def score_approach(
    bbox: BBox,
    vx: float,
    vy: float,
    zones: dict[str, Zone] | None = None,
) -> ApproachScores:
    zones = zones or load_zones()
    speed = (vx * vx + vy * vy) ** 0.5
    if speed > EPSILON:
        u_vel = (vx / speed, vy / speed)
    else:
        u_vel = (0.0, 0.0)

    tau: dict[str, float] = {}
    closing: dict[str, float] = {}
    heading: dict[str, float] = {}
    for name, zone in zones.items():
        cx, cy = _zone_center(zone)
        dx, dy = cx - bbox.cx, cy - bbox.cy
        dist = (dx * dx + dy * dy) ** 0.5
        if dist < EPSILON:
            tau[name] = 0.0
            closing[name] = 0.0
            heading[name] = 0.0
            continue
        ux, uy = dx / dist, dy / dist
        closing_rate = vx * ux + vy * uy
        closing[name] = max(0.0, min(1.0, closing_rate / CLOSING_SCALE))
        tau_abs = dist / max(closing_rate, EPSILON)
        tau[name] = max(0.0, min(1.0, 1.0 - tau_abs / TAU_HORIZON))
        heading[name] = max(-1.0, min(1.0, u_vel[0] * ux + u_vel[1] * uy))
    return ApproachScores(tau=tau, closing=closing, heading=heading)
