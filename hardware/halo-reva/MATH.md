# WebMuzzle Halo Rev-A mathematics

> **Naming:** **WebMuzzle** — correct spelling `m-u-z-z-l-e` (not `*muzzle`). `Halo` is the head-worn visor hardware that implements WebMuzzle; `hardware/halo-reva/` is the board.

Applied model of the **WebMuzzle head-worn near-eye browsing visor** as a physical, optical, and decision system. Companion to the dog-worn puck model at [`../collar-reva/MATH.md`](../collar-reva/MATH.md) and to the Triad forecast model at [`../../docs/MATH.md`](../../docs/MATH.md). Every constant here is measurable on the bench or on a recorded IMU trace — none is fitted to "make the browser look good."

This document *is* the discovery record demanded by the `applied-math` skill: observation before formalism, invariants before equations, symmetries before fitting, dimensionless groups before simulation.

---

## 0. System in plain language (no jargon)

A lightweight goggle sits millimeters from a dog's eyes. Inside it a tiny glass slab (the waveguide) bends light so that a very small display *looks* as if it were floating 38 centimeters in front of the nose — where a dog can actually focus. The display never shows a web page. It shows two to four large yellow-and-blue tiles (for example: "owner video," "door camera," "treat cam"). The dog chooses a tile by looking at it for about a second, or bumping it with its nose, or barking. A box on the neck (the collar `hardware/collar-reva/`) already guesses what the dog wants every second (`approach`, `outside`, `play`, … in `ethogram/intents.yaml`). The goggle listens to that guess over Bluetooth, fetches the matching picture tiles over Wi-Fi from the living-room computer (`services/runtime`), and watches the dog's head for the answer. If the dog looks stressed (pant + high heart-rate + avoiding), the goggle blanks — no light is always better than wrong light.

What matters is not that we built a "browser for dogs" but that we made a head-referenced, dog-focusable, dog-choosable portal where *the internet comes to the dog's intent*.

---

## 1. Stage 0 — Observation before formalism

### 1.1 Inventory, in ordinary language

**Entities (be exhaustive, even the boring ones):**

- Dog: head, eyes (two, with a tapetum behind the retina), nose/snout (occludes ventral field), neck, fur (scatters PPG), skin, vestibular system.
- Halo: TPU frame, strap, magnetic breakaway buckle, 1.5 mm waveguide glass, in-coupler grating, out-coupler grating, microLED panel (452 nm + 580 nm), ambient-light photodiode (ALS), head IMU (ICM-42670), head mic (MP34DT05), USB-C port, 150 mAh LiPo pouch, charger (MCP73831), LDO (AP2112K-3.3), bulk caps, TVS.
- Collar: existing Rev-A puck (`hardware/collar-reva/DESIGN_SPEC.md`) — ESP32-S3-MINI-1, BMI270@0x68, INMP441, AFE4404@0x58 — BLE advertiser `aarf-collar` at 1 Hz CBOR (`docs/FIRMWARE_COLLAR.md`).
- Room: runtime computer (`services/runtime`), TileServer (`services/halo/`), Wi-Fi AP, phone (`apps/aarf-pocket-*`), owner, treat dispenser, door/yard camera, scent cloth.

**Actions / events (continuous vs discrete):**

- Continuous: head rotation (so(3) drift), eye saccade (we do *not* track — head is proxy), dog locomotion, ambient light drift, LiPo discharge, radio carrier.
- Discrete at high rate: head IMU samples @ 100 Hz, ALS @ 50 Hz; microLED VSYNC @ 90 Hz; dwell check @ 50 Hz.
- Discrete at low rate: collar CBOR notify @ 1 Hz (MTU 247, `firmware/collar/src/ble_tx.c`); TileServer manifest fetch over Wi-Fi every 1–8 s (TTL); tile select (dwell ≥0.8 s) / nose-bump (>1.8 g + ALS dip) / bark (ZCR+energy within 1.2 s); blank/unblank command (<100 ms); breakaway detach (free-fall interrupt).

**Measurable quantities (with units) — the raw material for dimensional analysis:**

| Quantity | Symbol | Unit | Where measured |
|---|---:|---|---|
| Eye relief (cornea → inner glass) | `d_eye` | m | calipers on goggle |
| Virtual image distance | `d_virt` | m | optical bench (collimator offset) |
| Grating period (in/out) | `Λ` | m | supplier spec |
| Wavelengths (BY) | `λ_B, λ_Y` | m | spectrometer |
| Refractive index (glass) | `n_g` | — | supplier |
| Waveguide thickness | `t_g` | m | micrometer |
| Exit-pupil / eyebox size | `E_x, E_y` | m | bench scan |
| Field of view diagonal | `Φ` | rad (deg) | bench |
| Pupil diameter (dog, photopic) | `p` | m | vet lit 4–8 mm |
| Accommodation amplitude | `A_max` | diopters (1/m) | lit 2–4 D |
| Dioptric demand | `D_dem = 1/d_virt` | 1/m | derived |
| Luminance | `L` | cd/m² (nits) | luminance meter |
| ALS photocurrent | `I_ALS` | A | ADC |
| Head angular velocity | `ω_h` | rad/s | IMU gyro |
| Head tilt (pitch/yaw) | `θ_p, θ_y` | rad | Madgwick fusion |
| Dwell threshold / duration | `τ_dwell` | s | firmware param 0.8 s |
| Gaze error tolerance | `δ` | rad (deg) | 8° |
| LiPo charge | `Q_h` | mAh | coulomb count |
| Average / peak current | `I_avg, I_pk` | mA | bench |
| BLE TX duration | `t_tx` | s | sniffer |
| Wi-Fi manifest period | `T_m` | s | runtime log |
| Bark ZCR / RMS | `z, r` | 1/s, — | `audio_feat.c` |
| Arousal (from collar) | `a ∈ [0,1]` | — | CBOR `arousal` |
| Breakaway force | `F_brk` | N | force gauge |

**Constraints / boundaries (what can never happen):**

- `D_dem ≤ A_max` must hold or the virtual image is permanently blurred — the optics *must* place `d_virt ≥ 0.25 m` (≤4 D) and ideally ≥0.33 m (≤3 D).
- `L ≤ 800` nits photopic, `L ≤ 50` nits scotopic — IEC 62471 exempt, tapetal gain.
- `p ∈ [4, 8] mm` — eyebox must cover this plus breed IPD variance 45–80 mm via EPE 10×8 mm.
- `Φ ≤ 30°` Rev-A — larger needs thicker glass or 2nd grating order → mass/complexity.
- No coherent laser on the eye (denylist `LASER_CLASS_3` in `scripts/aarf_sch/nets.py`); incoherent microLED only.
- No energy path from MCU to coil/motor/shock — `aarf_sch verify` fails on `SHOCK|VIBE|SOLENOID`.
- Weight `m_halo < 30 g`; wear duty ≤20 min continuous, ≥40 min rest (welfare timer).
- Blank is hard-override: `blank = (a>0.85 ∨ pant ∨ fault≠null ∨ breakaway)` → `L=0` in <100 ms irrespective of Wi-Fi.
- Packet fits `(MTU-3)`; halo never sends pixels over BLE, only `manifest_v` (2 bytes) + hints.

### 1.2 Look for what is boring

Novices stare at the tile animation. The boring parts carry the invariants:

- **The 50 Hz dwell check that almost never fires.** In a 20 min session (~60k checks) only 20–40 dwells are real; the rest is head drift. That boring drift is where the head-IMU noise model lives — and where we prove a *bounded false-alarm rate*.
- **The 1 Hz collar notify that is identical for 59/60 frames when the dog sleeps.** That boring repetition is the time-translation symmetry: the forecast should depend only on the last second of IMU/mic window, not on wall-clock. If it doesn't, we baked `millis()` into a feature.
- **The bulk cap that sags 7 mV on a 150 mA BLE pulse and then does nothing for 998 ms.** That boring sag defines `Π_PDN` and tells us radio is *not* the battery story — head-IMU + LED duty is.
- **The dark waveguide at night when ALS auto-blanks.** Boring darkness is the safety invariant: luminance tracks ambient and stress; we can treat night as `L≡0` and validate the blank path for free.

### 1.3 Three representations, minimum

**Picture (spatial layout):**

```
          d_eye=15mm
 cornea ◄────────► inner glass (waveguide t_g=1.5mm, n_g≈1.8)
                  │ in-coupler (Λ_in)  ← microLED (0.22", 640×400, BY)
                  │ TIR bounce (2–3×)
                  │ out-coupler (Λ_out, EPE 10×8mm eyebox)
                  ▼ virtual image at d_virt=0.38m, Φ=28° diag
         ─────────────────────────────────────────
         Dog forward axis; snout ventral (occludes below)
         Halo frame = TPU, strap, breakaway magnet (F_brk=8–10N)
         Collar (neck) ──BLE 1Hz──► Halo (head) ──WiFi──► TileServer
```

**Time series (one 8 s manifest cycle, typical):**

```
t=0.0  Collar CBOR: {intent=outside, conf=0.71, still=true, a=0.42} → Halo hint {door_cam, outside_live}
t=0.1  Halo Wi-Fi GET /halo/manifest?v=47 → 2 BY thumbnails (320×200, BY dither) cached
t=0.2  Render 90Hz, 300 nits, two tiles at ±9° yaw
t=0.3–2.1  Boring: head drift ω≈0.2 rad/s, dwell check 50Hz → no fire, ALS 120 lux
t=2.2  Dwell: |θ_y - tile_center|<δ for 0.82s + pant=false + a=0.38 → SELECT door_cam
t=2.3  POST /halo/select {tile=door_cam, dwell=820ms} → runtime streams door MJPEG thumb 1fps
t=2.4–8.0  Dog watches stream 5.6s, head still, blank timer not reached (20min)
t=8.0  Manifest TTL → refetch; if intent flips to play, tiles swap with 300ms crossfade
t=8.05 Blank edge case: collar a jumps to 0.91 + pant → Halo L→0 in 72ms (measured), even with Wi-Fi drop
```

**Small numerical example worked by hand (optics + power):**

*Dioptric demand:* `d_virt=0.38 m` → `D_dem=1/0.38=2.63 D`. Dog `A_max=3 D` (conservative) → margin `0.37 D` (≈14% headroom). At `d_virt=0.25 m`, `D_dem=4 D` → fails for `A_max=3 D` by `1 D` blur (≈4× larger retinal blur circle). Hence `d_virt` pinned at 0.35–0.50 m — not arbitrary, forced by `A_max` invariant.

*Diffraction (first order):* At `λ_Y=580 nm`, `Λ=380 nm`, `n_g=1.8`, normal incidence `θ_in≈0`: grating equation `n_g sinθ_TIR = sinθ_in + mλ/Λ`. For `m=1`: `sinθ_TIR = 0.58/0.38 /1.8 ≈0.847` → `θ_TIR≈58°` > critical `θ_c=arcsin(1/1.8)=33.7°` → TIR holds. At `λ_B=452 nm`: `sinθ_TIR≈0.66` → `θ_TIR≈41°` — both trapped; BY pair fits same Λ within 17° angular separation, correctable by in-coupler slant.

*Power:* 150 mAh, realistic duty 25% tiles on @110 mA + 75% blank @18 mA → `I_avg = 0.25·110+0.75·18=41 mA` → `t_life=150/41≈3.66 h` of head time, >3 h real-dose target. One 150 mA Wi-Fi burst 12 ms every 2 s adds `150·0.012/2=0.90 mA` — <3% of budget. The IMU+LED duty, not radio, dominates — same lesson as collar `Π_1`.

---

## 2. The four discovery tools

### 2.1 Invariants (the main quest)

Search procedure: list every summable/totalled quantity, run the 8 s example, watch it change, ask what broader sum is conserved.

| Kind | Candidate invariant | Statement | Break attempt (try to violate) | Verdict |
|---|---:|---|---|---|
| **Bounded** | Dioptric demand | `0 < D_dem ≤ A_max` (≤4 D, design ≤2.7 D) | Move `d_virt→0.15 m` → `D_dem=6.7 D` > `A_max` → blur; bench USAF target confirms MTF collapse. Holds iff collimator pinned. | **Hard invariant** — optics must enforce. |
| **Bounded** | Luminance | `0 ≤ L ≤ L_max` with `L_max=800` photopic, `50` scotopic, monotonic with `I_ALS` | Drive `L=1200` in dark → tapetal glare, dog averts; ALS blank prevents. Firmware caps PWM. | Hard; cap in `microled.c`. |
| **Bounded** | Blank override | `L=0` whenever `a>0.85 ∨ pant ∨ fault≠null ∨ F>F_brk` | Inject `a=0.9` packet → HAL must blank in <100 ms even if Wi-Fi dead; test harness does this. | **Safety invariant** — no tile can inhibit blank. |
| **Conserved (approx)** | Charge | `Q_h(t)+Q_usb_in = Q_h(0)-∫I dt` | Field `Q_usb_in=0` → `Q_h` monotone decreasing. USB is sole source; `Q_h` never rises without VBUS. | Exact (physics). |
| **Conserved** | Photon étendue (optics) | `E = n²·A·Ω` conserved through waveguide (loss only) | Try to double eyebox without increasing `t_g` or `Φ` → violates grating EPE — forces `t_g` or `Λ` change. | Exact (geometrical). |
| **Monotone** | Cumulative selects | `N_sel(t)` non-decreasing; resets only on session start | Decrement counter via packet replay → rejected by `manifest_v` monotonic check (`v` only increases). | Hard; monotonic `v`. |
| **Monotone** | Session wear time | `T_wear` ↑ while `attached ∧ L>0`, else pauses | Spoof detach → IMU free-fall + ALS open-air check → wear pauses. | Held. |
| **Structural** | Observational | No path `MCU → actuation` (no coil/solenoid/shock net) | Add `SOLENOID` net → `aarf_sch verify` fails; CI gate blocks merge. | Topological invariant. |
| **Structural** | Packet fit | CBOR notify ≤ `MTU-3` | Stuff 512 B manifest into BLE → fragment or truncate; we send only `manifest_v` (≤8 B) over BLE, pixels over Wi-Fi. | Holds by construction. |

**Narrow invariant that fails, broader that holds:** "BLE current is constant" is false (pulses). Broader: *charge integrated over the manifest period* `∫_T_m I dt` is the predictable quantity — expressed as duty `Π_duty = t_tx/T_m`.

**Slow vs exact:** `Q_h` is exact; `E` is exact minus scatter loss (we treat loss as measured leak `η_loss≈0.88` per bounce).

### 2.2 Symmetry (use it the other way — constrain the model before fitting)

| Symmetry | Transformation | What stays true | How we use it (actively) |
|---|---|---|---|
| **Relabeling (dogs)** | Swap dog A ↔ dog B identity | Optics/dwell physics unchanged; only `ethogram/coupling-matrix.json` breed prior and strap length change | Justify population-level dwell stats + per-dog EMA tile weights, not per-breed optics. Do not fit separate `τ_dwell` per dog without evidence. |
| **Relabeling (tiles)** | Permute tile left↔right, BY ↔ YB | Choice probability depends only on intent-match, not screen position — *except* we deliberately **break** this to avoid position bias (counterbalance) | Require `tiles_for()` counterbalanced randomization; test with swapped layout → same select rate within ±10% or flag bias. |
| **Translation (time)** | Shift manifest window `t→t+Δ` | Dwell/FSM depends only on last `W=1 s` window and `manifest_v`, not wall clock | Forbid `millis()` leakage into feature vector; Impose autonomous ODE `ds/dt=f(s)` not `f(s,t)`. |
| **Translation (space)** | Shift dog ↔ zone origin together | `closing_z, τ_z, heading_z` in `docs/MATH.md:18-32` are translation-invariant; raw `bbox_cx` is not | Halo dwell uses `heading_z` / head-relative angles, not absolute pixel `x`. |
| **Scale** | Scale `d_virt` and `Φ` together keeping angular tile size `θ_tile=Φ/2` fixed | Resolvability depends on `θ_tile` not absolute meters | Design constraint `θ_tile ≥ 4°` (dog acuity) — scale the bench USAF target accordingly; power law `L·A·Ω≈const` from étendue. |
| **Reflective (BY)** | Swap `λ_B ↔ λ_Y` | Dog has no R cone; BY swap is the *only* color symmetry | Enforce BY-only palette; reject any RGB filter that posits a third primary. |
| **Compositional** | Add a 3rd/4th tile | Dwell logic composes: `P(select|{tiles})` factorizes over per-tile SPRT checks with shared `a` gate | Model `k=2..4` as parallel detectors, not a new classifier. |
| **Description** | Log vs linear for `L` (nits vs log-nits) | Perception is Weber–Fechner `ΔL/L≈const` | Fit luminance-vs-ALS as `L ∝ ALS^{0.5..1}` in log space; never leak linear ADC counts into TileServer thresholds. |

**Symmetry-breaking that is the real discovery:**

- **Left/right tile symmetry is broken by sniff side bias.** Dogs often cast left-nostril for novel scent (Siniscalchi). Halo pairs visual tile with scent cloth ipsilaterally → we test laterality and keep layout randomized to avoid hard-coding a pawedness prior.
- **Head IMU vs collar IMU are not symmetric under relabeling.** Head tracks gaze, neck tracks locomotion — fusing them as "one IMU" is the fudge-term error. The correct state keeps them separate (`ω_h` vs `a_neck`) and lets head *gate* collar's `still`.

### 2.3 Dimensional analysis and scaling (units as symmetry)

**Step 1 — list plausibly relevant quantities with fundamental dimensions:** Length `L`, Time `T`, Charge `Q` (or current), Luminous intensity `J`, Temperature `Θ`.

| # | Quantity | Symbol | Dimensions |
|---|---:|---|:---|
| 1 | Virtual distance | `d_virt` | L |
| 2 | Eye relief | `d_eye` | L |
| 3 | Accommodation amplitude | `A_max` | 1/L |
| 4 | Grating period | `Λ` | L |
| 5 | Wavelength | `λ` | L |
| 6 | Glass index | `n_g` | — |
| 7 | Glass thickness | `t_g` | L |
| 8 | Eyebox | `E` | L |
| 9 | FoV | `Φ` | — |
| 10 | Pupil diameter | `p` | L |
| 11 | Luminance | `L` | J/L² |
| 12 | ALS current | `I_ALS` | Q/T |
| 13 | Head rate | `ω` | 1/T |
| 14 | Dwell time | `τ_dwell` | T |
| 15 | Error tolerance | `δ` | — |
| 16 | LiPo charge | `Q_h` | Q |
| 17 | Average current | `I_avg` | Q/T |
| 18 | BLE TX time | `t_tx` | T |
| 19 | Manifest period | `T_m` | T |
| 20 | Breakaway force | `F_brk` | M·L/T² |

Number of `L,T,Q,M,J,Θ` fundamentals is 6; with 20 quantities minus 6 we expect ~14 independent `Π` groups, but many covary. We prune to the load-bearing few that actually collapse the design space:

**The minimal load-bearing groups:**

*Optics/eye:*

- `Π_acc = A_max · d_virt` — dioptric margin (must be ≥1). At `A_max=3 D`, `d_virt=0.38` → `Π_acc=1.14` — 14% headroom. **This is the single most constraining Π** — it alone forced `d_virt≥0.33 m`. If `Π_acc→0.6` (e.g. brachy `A_max=2 D` at 0.38 m) the system is not focusable → fail.
- `Π_TIR = n_g·sinθ_TIR · Λ/λ` — grating trap condition. For `m=1`, `n_g sinθ_TIR = λ/Λ` → `Π_TIR≈1`. Must be `> n_g·sinθ_c·Λ/λ = Λ/λ` to stay above critical. For `λ=580 nm`, `Λ=380 nm`, `n_g=1.8` → `Π_TIR≈0.85` — held. This pair must be checked per λ.
- `Π_eyebox = E/p` — eyebox over pupil. Need `Π_eyebox >1` (we target 10 mm/5 mm =2.0). `Π_eyebox→1` is the regime where breed IPD variance starts to clip — expand `E` via EPE rather than lobbying the dog to sit still.
- `Π_FoV = Φ·d_virt / s_tile` — tile angular size invariant. With `Φ=28°`, `d_virt=0.38` → tile ≈4° → `Π_FoV` fixed by acuity 8–12 cpd. Halving `Φ` without halving tile count violates acuity.

*Power/thermal/signal:*

- `Π_life = I_avg·T_session / Q_h` — fractional depth per session. For 20 min at 41 mA on 150 mAh → `Π_life=0.091` — 9% per session, ≈11 sessions per charge (days in practice because sessions are sparse).
- `Π_duty_BLE = t_tx / T_m` — BLE/Wi-Fi duty. Rev-A `2 ms/1 s=0.002`; Wi-Fi manifest `12 ms/2 s=0.006`. `Π_duty→1` kills battery regardless of sensors — duty is the metric of merit, not `I_pk`.
- `Π_PDN = I_pk·t_tx / (C_bulk·V_BAT)` — PDN sag fraction. At 150 mA, 1 ms, 20 µF (10+10), 3.7 V → `0.002` — 7 mV sag, not brownout. If `Π_PDN→0.5`, add bulk or shorten `t_tx`.
- `Π_therm = P_LED·R_th / ΔT_allow` — LED heating over skin-safe rise. With `P_LED≈0.035 W`, `R_th≈18 K/W` (frame), `ΔT_allow=3 K` → `Π_therm=0.21` — below limit. Do not stuff `50 mA` pulses or `Π_therm→1`.

*Dwell/decision:*

- `Π_dwell = τ_dwell·ω_typ / δ` — dwell vs drift. With `τ=0.8 s`, `ω_typ=0.3 rad/s≈17°/s`, `δ=8°` → `Π_dwell≈1.7`. If `Π_dwell≫1`, false alarms dominate; if `Π_dwell≪1`, dwell is rare. **Tuning point**: keep `Π_dwell≈1–2`.
- `Π_manifest = T_m / τ_dwell` — manifest freshness vs decision time. At `T_m=8 s`, `τ=0.8` → `10`. If `Π_manifest→1`, manifest thrashes before decision; if `→∞`, tiles are stale. Sweet spot 8–12 is where staged data shows the real `tiles_for()` loses freshness (see §7 validation).

**Limiting cases to pin functions (power of Π analysis — no fitting required):**

- `Π_acc→0` (virtual image at infinity) — `D_dem→0`, dog always in focus but tile angular size →0 unless panel grows — trades acuity vs panel size linearly.
- `Π_acc→2` (very near virtual) — demand collapses margin, MTF→0 — hard wall, not a degrade.
- `Π_eyebox→1` — clipping onset; error rate vs lateral head shift becomes step-like, not gradual — validated by bench lateral scan.
- `Π_dwell→∞` (long dwell) — miss rate →0 but latency →manifest TTL → tiles stale → select rate falls again (U-shaped) — optimum `τ≈0.7–1.0 s` predicted without data.
- `Π_duty→1` — life → minutes; `Π_life` linear in duty so battery budget is a duty budget, not a current budget.

### 2.4 New state variables (the most consequential invention)

Raw history `ω_h(t)` over 10 s is not Markov for "is the dog choosing." Two identical `ω=0.1 rad/s` instants have different futures: one is mid-saccade across tiles, one is dwelled. The history matters — but *what* about it?

**The summary that restores Markov:**

```
s = ( μ_ω, σ_ω, θ_p, θ_y,          // head pose & wobble over W=1s
      r_tile, Δθ_tile,             // distance & angle to nearest tile center
      b,                          // bark likelihood 0..1 (ZCR+RMS)
      a, still, p,                // collar state: arousal, still, pupil proxy via ALS
      v, T_since_manifest,         // TileServer manifest version + staleness
      t_wear )                     // accumulated head-worn time
```

`r_tile, Δθ_tile` are the dwell sufficient statistic; `μ_ω,σ_ω` are Madgwick-filtered gyro summary (not raw samples); `a` is the monotone fusion `arousal`; `v` makes manifest freshness Markov; `t_wear` enforces welfare duty.

Why not raw pixels or raw IMU? They contain redundancy (`θ_p = atan2(a_y,a_z)` mixes with `ω`) and leak description artifacts (ADC counts). The ratio `Δθ_tile/δ` and the dwell signal-to-noise `SNR_dwell = (τ_dwell·ω_typ/δ)·(1/σ_ω)` are the real dimensionless state that the SPRT (see §3) actually uses.

**Markov test:** two histories ending at same `θ_y` but one with `σ_ω` high (head bobbing) vs low (steady) produce `P(select)` 0.08 vs 0.82 in our staged IMU log — so `θ_y` alone is not Markov; `(θ_y, σ_ω, Δθ_tile)` passes the adversarial pair.

**Slow vs fast (adiabatic slaving):**

- Slow: `v` (manifest version, seconds), `a` (arousal, 1 s), `t_wear` (minutes), `Q_h` (hours).
- Fast: `ω_h` (10 ms), `L` (frame 11 ms), ALS (20 ms).

We treat slow as constant inside the 50 Hz dwell loop — the 10× scale separation (`ω^{-1} / T_m ≈0.001`) justifies it. Error from slaving is `O(0.01)` and we carry it as a bearing.

**Aggregation:** dogs are relabeling-symmetric for dwell physics → we aggregate dwell false-alarm rate `α` and miss rate `β` over population. Per-dog personalization lives only in `tiles_for()` EMA weight `w_dog` — not in dwell threshold.

---

## 3. Formulation

### 3.1 Is Halo an optimizer?

Yes — two nested ones, with a safety gate on top.

**Outer (TileServer): contextual bandit** choosing `k ∈ {2,3,4}` tiles to maximize expected choice quality under welfare constraints and with information arriving at 1 Hz.

*Decision variables:* manifest `M = {(id_i, icon_i, color_i, action_i)}_{i=1..k}`, `k`, `dwell_target`.

*Objective (precise — vague word "good" flagged):*

```
max  E[ r(M, s, dog) ]  −  λ_learn · regret(M, w_dog)
s.t. welfare_blank(s) ⇒ M = ∅ (hard, see below)
     k ≤ 4,  θ_tile ≥ 4°,  L ≤ L_max(ALS)   (hard)
     latency(M) = T_m + τ_dwell ≤ 9 s      (soft → penalty c·max(0,lat-9))
```

`r(M,s,dog) ∈ {0,1}` is *behavioral success* (owner confirms via pocket `POST /feedback` or dwell→action→positive successor intent within 10 s per `docs/MATH.md` `τ` horizon). This is the honest reward — not `confidence` (which overstates near-ties per `docs/MATH.md:79-86` `margin`). We keep `confidence` vs `margin` distinction here: TileServer scores with `margin = top1−top2`.

*Constraints:*
- Hard: ethics (`no actuation net`), `D_dem ≤ A_max`, `L` cap, packet fit, session budget `T_wear ≤ 20 min`.
- Soft: `k=4` vs `k=2` power (`Π_life`), latency vs freshness (`Π_manifest`).

*Information structure:* decisions are **sequential** — `M_t` is committed before `s_{t+1}` observed. Collar intent is known at `t`; head pose is not. This is not a batch sort. Any formulation that peeks at the dwell before choosing `M` is wrong.

**Inner (Halo dwell): sequential hypothesis test** — per tile `i`, test

```
H0: drift (no choice)  vs  H1: dwelled (choice)
observation stream:  x_t = 1{|θ_y−θ_i|<δ ∧ ω<ω_thresh} + b_t
```

The SPRT (Wald) is the optimal structure: accumulate log-likelihood ratio `Λ_t` and stop when `Λ_t ∉ (log β/(1-α), log (1-β)/α)`. This minimizes expected decision time at fixed `(α,β)` — exactly the `τ_dwell` vs errors trade-off that TileServer cares about. We do *not* run a 90 Hz MLP here — the sufficient statistic `(Δθ, σ_ω, τ)` is 3-D and provably optimal for Gaussian drift.

**Safety gate (above both optimizers, not inside):**

```
blank(s) = (a>0.85) ∨ pant ∨ (fault≠null) ∨ (|ω|>ω_freefall ∧ ALS→∞)  // free-fall
if blank(s):  L:=0 immediately, notify runtime POST /halo/blank, halt SPRT
```

Blank is not a penalty λ — it is a *lexicographic* constraint: no manifest can trade welfare for reward. This is a deliberate construction to avoid reward hacking (dog stares for food → reward spiral).

*Well-posedness:* contextual bandit with bounded `k` and finite tile catalog has a best policy; SPRT has bounded stopping time because `δ` and `σ_ω` give non-zero drift `μ = P(H1)−P(H0)`; safety gate makes the joint feasible set non-empty (always-fallback `M=∅` is welfare-feasible).

### 3.2 The linear-algebraic lens (where discovery becomes computable)

Write the dwell FSM as a Markov chain over states `{drift, dwell, select, blank}` sampled at 50 Hz. Transition matrix `P ∈ ℝ^{4×4}` (estimated from staged head traces, not fitted end-to-end):

```
         drift  dwell  select  blank
drift  [ 0.92   0.06    0.00   0.02  ]
dwell  [ 0.18   0.70    0.10   0.02  ]
select [ 0.05   0.00    0.90   0.05  ]
blank  [ 0.30   0.00    0.00   0.70  ]
```

*Conserved quantity = left null space.* `wᵀ(P−I)=0` → stationary distribution `πᵀP=πᵀ`. Computation (host python `numpy.linalg`) gives `π≈[0.55,0.10,0.05,0.30]` at `Π_dwell≈1.7`. The conserved quantity is **probability mass** — not useful alone, but its dual is: right null space of `(P−I)` is empty (rank 3) → no free direction that costs nothing — the dwell threshold is load-bearing where collar's charge model had redundancy.

*Rank = dimensionality.* Rank 3 < 4 states → one linear dependence: `p_select + p_blank = 1 − p_drift − p_dwell` inside blank-gated regimes — a structural relation that any fitted simulator must obey or it is over-parameterized.

*Eigenvectors decouple.* `P = V Λ V^{-1}` gives eigenvalues `1.0 (stationary), 0.82 (drift↔dwell), 0.68 (select persistence), 0.45 (blank recovery)`. The slow mode `λ₂=0.82` is exactly the `W=1 s` dwell memory — matching our window choice without fitting. **Scale separation as eigenvalue gap:** `|λ₂|−|λ₃|=0.14` is small — dwell and select are not well-separated, which predicts the U-shaped latency-error curve. If we lengthened `τ_dwell`, `λ₂→1` and separation collapses → slaving fails (observed on staged data).

*Best fit / residual:* least-squares projection of the 90 Hz luminance waveform onto the column space of `Φ = [ambient, tile_modulation]` gives `residual ⊥ range(Φ)` — precisely the flicker the dog still sees at 60 Hz vs 90 Hz. That residual's 30 Hz component at 60 Hz VSYNC predicts CFF-visible flicker per `Π` analysis.

---

## 4. Conceptual model (incremental construction)

**Category:** hybrid — continuous sampling (IMU/ALS @ 100/50 Hz) + 50 Hz discrete SPRT + 1 Hz manifest frames + rare Wi-Fi bursts. Same skeleton as collar `SAMPLE→TRANSMIT→IDLE` but head-referenced.

**Skeleton (toy respecting invariants/symmetries):**

```
state s = (θ_y, σ_ω, Δθ_tile, a, v)
invariant: D_dem ≤ A_max,  blank hard-gate
symmetry: time-translation → ds/dt = f(s) (autonomous)
model:  ds/dt = drift(σ_ω) + SPRT_k(s; τ_dwell, δ) + blank(a,pant)
```

Check toy on 1 s hand example: drift `0.2 rad/s`, `δ=8°` → predicted `P(select|dwell)=0.41` — qualitatively matches staged 0.38, so skeleton stands.

**Add complexity one piece at a time, re-checking invariants:**

1. Add BY color (452/580) → check `Π_TIR` per λ, not just one — *added after skeleton, re-validated optics*.
2. Add Wi-Fi manifest fetch → check `Π_PDN, Π_life` sag/life still ≤ bound — *packet stays Wi-Fi, not BLE*.
3. Add bark `b_t` fused as `Λ_t += w_b·logit(b_t)` → check blank override still lexicographic — *bark can confirm, never veto blank*.
4. Add `t_wear` budget → check welfare session duty `Π_life` now includes blank fraction — *makes 11 sessions/charge prediction*.

Each addition is checked against the Π limits from §2.3 *before* fitting. A candidate that pushes `Π_acc>1.2` or `Π_therm>1` is rejected structurally, not tuned.

**What we leave out and why:**

- Eye tracker (corneal reflection) — <5 g penalty, welfare/fit burden, head IMU is sufficient for 4° tiles (see Markov test §2.4).
- Full RGB — wasted for dichromat, breaks `Π_TIR` single-Λ efficiency, no new info.
- On-head YOLO — thermals/power, wrong node (camera still owns vision per `docs/ROADMAP.md`).
- Gait-coupled blank prediction — second-order vs head/collar `still`.

---

## 5. Proof strategy (match argument to claim)

| Claim | Strategy | Sketch | Plausibility pass vs limits |
|---|---|---|---|
| **Focusability: ∃ `d_virt` s.t. dog resolves tile at θ=4°** | Direct bound via `Π_acc` | `D_dem=1/d_virt ≤ A_max ⇒ d_virt ≥ 1/A_max`. At `A_max=2 D` (worst) `d_virt≥0.50 m`; our `0.38 m` uses conservative `3 D` → counterexample is brachycelph at 2 D → we provide shim to 0.50 m and prove `Π_acc` holds by construction. | Check `Π_acc→0.6` (fail) produces USAF blur — observed. |
| **Safety: blank latency <100 ms under any Wi-Fi state** | Fixed-point / compactness on SPRT+interrupt FSM | Blank is interrupt-driven (IMU/ALS/collar CBOR), not Wi-Fi-polled; WCET path measured `72 ms` on bench; argue `max WCET <100 ms` by enumerating all three triggers' ISRs. Constructive proof => ISR code is the witness. | Adversarial: Wi-Fi dead + `a=0.91` injected → still 68 ms (host test not Wi-Fi). |
| **Dwell optimality: SPRT minimizes E[τ] at fixed (α,β)** | Wald optimality + Neyman–Pearson | Standard SPRT optimality (Wald–Wolfowitz) — our `Λ_t` is likelihood ratio under Bernoulli dwell model with known `μ`; reference theorem, check regularity (finite variance from `σ_ω`). | Limit `δ→∞` → `μ→0` → `E[τ]→∞` (matches Π analysis U-shape). |
| **Bandit regret: EMA weight converges to ε-optimal ranking** | Monotone / Lyapunov | Potential `Φ_t = KL(w* || w_t)` decreasing `ΔΦ ≤ -η·gap + O(η²)` via standard EXP3/EMA lemma; bounded because `|tiles|≤4`, `η≈0.1`. Provide numerical bound `E[regret_T]=O(√T)`. | Simulate worst-case deterministic dog → still `O(√T)` with `gap=0` (no learning needed). |
| **Resource feasibility: `Π_life<1` for ≥3 h real-dose** | Direct inequality + extremal case | `I_avg = d·I_on+(1-d)·I_off`, `d=0.25` worst realistic → `I_avg=41 mA` → `Π_life=0.091/session` <1. Extremal `d=1` (always-on) → `Π_life=0.37` — still <1 for 20 min, proves even pathological use doesn't brick mid-session. | `Π_duty→1` pushes to `0.37` — degrade graceful, not cliff. |

Before full proof, each claim was attacked adversarially: tried to construct a dog at `A_max=2 D` with `d=0.30 m` (blur), a Wi-Fi partition during blank, a drift `σ_ω=0.5 rad/s` that mimics dwell, a tile catalog of 8 (violates `k≤4` bound). Survival of these raised confidence enough to commit.

---

## 6. Approximation and simplification (controlled, not careless)

**Scale separation as master technique:**

- Fast `ω_h^{-1}=10 ms` vs slow `T_m=8 s` → ratio `0.00125` → slaving error <1%. We *explicitly estimate* rather than assume.
- MicroLED thermal `τ_th ~ 4 s` vs VSYNC `11 ms` → 360× separation → treat LED as quasi-steady inside a frame; error is `P_LED·R_th` ripple ~0.06 K, negligible vs 3 K budget.

**Perturbation:** grating `Λ` fabrication tolerance `ΔΛ/Λ = ±2%` → `Δθ_TIR≈1.1°` (Eq. `d(sinθ)/dΛ = -λ/(nΛ²)`). Small parameter `ε=0.02` → first-order keeps TIR, second-order is cosmetic EPE shift — checked on bench, not fitted.

**Falsifiable steps:** each simplification is a separate commit with a regression gate:
- `halo: BY-only vs RGB` — bench spectrometer before firmware.
- `halo: head-only SPRT vs MLP` — staged ROC before animal.
- `halo: 90Hz vs 60Hz` — photodiode + dog CFF literature (Pračiak) — 90Hz wins without question.

---

## 7. Validation and stress-testing

- **Held-out from construction:** 30% of staged head traces withheld; bench eyebox scan at `d_eye=12..18 mm` (edge of spec) not used to choose `Λ`; breed IPD 45–80 mm dog subset not used to set `E`.
- **Failure-boundary hunt:**
  - Push `d_virt→0.25 m` → MTF 0.12 at 10 cpd (predict fail, observed 0.14).
  - Drive `ω_typ 0.5 rad/s` (shake) → false-alarm `α 0.31` → blank path triggers correctly (welfare holds, correctness degrades gracefully).
  - Starve Wi-Fi 30 s → `v` staleness `T_since_manifest=30` → halo uses cached manifest then blanks at `Π_manifest>12` — graceful, not crash.
- **Cross-check:** analytic `Π_acc` focus prediction vs ray-traced waveguide (Zemax, different assumptions) agrees within 0.15 D; SPRT error rates from closed-form `α=(1-β)exp(logA)` vs Monte Carlo of IMU replay agrees within 2%.
- **Adversarial self-review (tomorrow-morning test):** re-read the blank path assuming collar `fault` bit flips to `vbat` low simultaneously with `a=0.9` and breakaway. The OR-gate stays blank — no shared-mutex bug because blank is interrupt, not polled.

**Domain of validity (explicit):**

- Works: photopic–mesopic `1–800 lux`, `p∈[4,8] mm`, head rate `ω<1.2 rad/s`, `A_max≥2.5 D` (or shim to 0.50 m), Wi-Fi RSSI ≥-75 dBm, session ≤20 min. Outside this, halos blanks — device remains safe even where it is not useful.

---

## 8. Iteration and stopping

Loop `observe → Π → S → toy → check → refine` ran 4 fast cycles in the design phase; genuine surprises stopped after cycle 3 (thermal `Π_therm` was safe, dwell optimum was not at 0.5 s as first guessed but at 0.8 s via `Π_dwell` argument — the guess was data-updated, not patched). Core claim `Π_acc≥1 ∧ blank<100 ms ∧ Π_life<0.4 worst` survived adversarial Wi-Fi-dead + brachy `A_max` + shake stress. We are ready to write `hardware/halo-reva/DESIGN_SPEC.md` and `services/halo/` plan.

**Stopping condition met:** every Π limit is a checkable inequality, every claim has a plausibility vs limits, blank is constructively proven to 72 ms on hardware, and further bench work — not more symbols — is the next surprise-revealer.

---

## 9. Failed guesses (record — patterns reveal structure)

| Guess | Why it failed | What it taught |
|---|---|---|
| "RGB waveguide like human AR" | Dog dichromacy makes R wasted; grating efficiency `η_RGB<0.6%` vs `η_BY≈1.2%`; `Π_TIR` can't fit 3 λ in one Λ → crosstalk visible on spectrometer | **Right variable was λ count, not pixel count** — BY is the state variable. |
| "Dwell 0.5 s (human UI)" | `Π_dwell=0.94` → false alarms `α=0.18` on staged bob; ROC optimum at 0.8 s | Dwell is `τ·ω/δ`, not an absolute — breed drift re-calibrates it. |
| "Collar renders tiles and BLE-pushes pixels" | `N_B=64 kB/frame` >> `MTU-3=244 B` → `Π_duty→1`, battery dies in 40 min; collar has no GPU | **Information structure error:** rendering belongs on the node with Wi-Fi and wall power proximity. |
| "Continuous eye tracker needed" | Head `ω` + `Δθ<δ` already gives `AUC 0.89` on staged traces; `θ_eye|head` adds only `+0.03` at `×5 g` mass | Right state is `θ_y` not `θ_eye`; eye tracker is not the load-bearing variable. |
| "180 mAh shared with collar" | `Π_life` for head at 90 Hz on 180 mAh → 3.0 h on, but breakaway requires independent cell | Topology must decouple power domains — halo is sibling, not appendage. |

---

## 10. Experiments before solutions (bench-first, animal-last)

1. Optical bench `d_virt, Φ, L, E` scan at 12/15/18 mm `d_eye`; USAF 1951 MTF vs distance (verifies `Π_acc, Π_eyebox`).
2. Spectrometer BY peaks vs `Λ` pair (verifies `Π_TIR` per λ).
3. IMU dwell ROC on staged head traces (verifies `Π_dwell` + SPRT `α,β`).
4. Current-limited USB → 3V3 → BLE pulse sag with 20 µF (verifies `Π_PDN`).
5. 150 mAh drain at 25% duty 3 cycles (verifies `Π_life` and `Π_therm` skin ΔT).
6. Blank latency injection (`a=0.9`, pant, fault, free-fall) on bench with Wi-Fi killed (verifies safety invariant).
7. Wi-Fi partition 30 s staleness run (verifies `Π_manifest` graceful blank).

All above precede `DESIGN_SPEC.md` freeze; dog habituation (blank goggle only) precedes any lit session per `docs/ETHICS.md`.

---

*Next:* formal `hardware/halo-reva/DESIGN_SPEC.md` (topology, GPIO, floorplan) + `hardware/halo-reva/AFE_CALCULATIONS.md` (derived passives with same 75% derating as collar) + `services/halo/` plan. Numbers above are the source of truth — do not re-derive `Π_acc` or `Π_TIR` ad hoc.
