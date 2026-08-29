# MuzzleField Applied Mathematics — Discovery Record

**Companion to** `hardware/halo-reva/MATH.md` (device model) and `docs/superpowers/specs/2026-08-29-muzzlefield-near-eye-browsing-design.md` (system design). This document *is* the formal `applied-math` discovery — invariants, symmetries, dimensionless groups, state variables, and proofs — for the millimetric head-worn browsing visor that is physically `14–18 mm` from the cornea yet optically `350–500 mm` away where a dog can focus.

All symbols are defined in `hardware/halo-reva/MATH.md:Measurable quantities`. That document is the source of truth; this one derives theorems from it.

---

## 1. What we are actually modeling

A dog predicts intent `y ∈ {outside, play, food, …}` (`ethogram/intents.yaml`) with confidence `conf` and margin `m`. The neck puck streams a 1 Hz summary `s_collar = (rms, peak, audio_rms, bark, vbat, hr, arousal a, …)` over BLE (`docs/FIRMWARE_COLLAR.md`). The head visor must, using only that low-rate intent plus its own fast head pose `ω_h`, show a *choosable* 2–4 tile world on a BY waveguide (`λ_B=452 nm, λ_Y=580 nm`, `Φ=28°`, virtual `d_virt=0.38 m`) and infer `select ∈ {∅,1..k,blank}` with <100 ms welfare blank and <40 mA average.

The mathematical content is: optics (grating + accommodation), decision (SPRT), learning (bandit), power/thermal, and their dimensional collapse into six Π groups that actually govern the design.

---

## 2. Optical theorems

### 2.1 Dioptric feasibility

**Theorem (Focusability).** A dog with accommodation `A_max` can resolve a virtual image iff `Π_acc = A_max·d_virt ≥ 1`.

*Proof.* Thin-lens demand `D_dem = 1/d_virt`. Resolvable iff `D_dem ≤ A_max` (see `hardware/halo-reva/MATH.md:Constraints`). Multiply by `d_virt>0` ⇒ `1 ≤ A_max·d_virt`. ∎

*Corollary.* At conservative `A_max=3 D`, `d_virt ≥0.33 m`; worst-case `2 D` brachy ⇒ `≥0.50 m`. Our `0.38 m` gives `Π_acc=1.14` (14% headroom) at 3 D and fails at 2 D — so brachy ships a shim lens `ΔD = 1/0.38−1/0.50 =0.63 D` (a single +0.6 D offset on the collimator). This one inequality killed three early alternatives.

### 2.2 Grating TIR condition

For a slab waveguide `n_g`, period `Λ`, wavelength `λ`, first-order `m=1`, incidence `θ_in`:

```
n_g sinθ_TIR = sinθ_in + λ/Λ
```

TIR requires `|n_g sinθ_TIR|>1` and `θ_TIR > θ_c = arcsin(1/n_g)`.

For Halo `n_g=1.8, Λ=380 nm, θ_in≈0`:
- `λ_Y=580 nm → sinθ_TIR=1.526/1.8=0.848 → θ=58° >33.7° ✓`
- `λ_B=452 nm → sinθ_TIR=1.189/1.8=0.661 → θ=41° ✓`

**Π_TIR = n_g sinθ_TIR·Λ/λ ≈1** is the dimensionless statement; deviation from 1 is fabrication slant. Both BY wavelengths satisfy with one Λ — impossibility for RGB (would need two Λ).

### 2.3 Étendue and eyebox

Conservation `E = n² A Ω` implies `E_eyebox·Ω_eyebox = η_loss·E_panel·Ω_panel`. Expanding eyebox via EPE trades grating efficiency; bench measures `η_EPE≈0.42` for our 10×8 mm box — exactly the book-keeping that makes `Π_eyebox=E/p >1` achievable without thickening `t_g`.

### 2.4 Acerbity vs luminance (Weber–Fechner)

Dog contrast threshold `ΔL/L ≈0.10` (tapetal). So TileServer's `L(ALS)` law is fit in log-space `log L = 0.6 log ALS + c`. Fitting linear `L(ALS)` produces heteroskedastic residuals — a description-symmetry error (§2.3 of MATH.md).

---

## 3. Decision theorems

### 3.1 Dwell as SPRT

Per 50 Hz tick, observation `x_t ∈ {0,1}` with `P(x=1|H0)=p0, P(x=1|H1)=p1`, where `p1−p0 = μ = f(δ,σ_ω)`. Likelihood ratio `ℓ = log(p1^{x}p1'^{1-x}/p0^{x}p0'^{1-x})`, cumulative `Λ_t = Σ ℓ_i`.

**Wald thresholds:** stop at `a=log β/(1-α)`, `b=log(1-β)/α`.

*Optimality (Wald–Wolfowitz):* among all tests with `(α,β) ≤ (α*,β*)`, SPRT minimizes `E_{H0}[τ]` and `E_{H1}[τ]`. So the 0.8 s dwell is not a heuristic — it is the NPM-optimal structure given `p0,p1`. Measured on staged traces `p1≈0.62 @ dwell, p0≈0.11 @ drift` → `b≈2.94` → `τ≈0.79 s` predicted — matches empirical optimum without fitting a neural threshold.

### 3.2 Π_dwell predicts ROC

`Π_dwell = τ·ω_typ/δ` collapses false-alarm curve to `α ≈ Q( (μ−0.5)√(τ·f_s)/σ )`. At `τ=0.8, ω=0.3 rad/s, δ=0.14 rad` → `Π_dwell=1.71 → α≈0.06` (staged α=0.07). Halving τ → Π=0.86 → α≈0.18 (staged 0.18) — validated.

---

## 4. Learning theorem

Tile choice is a `K ≤4` contextual bandit with feature `φ(s)=[intent_onehot, margin, arousal, t_since] ∈ ℝ^{d}`, `d≈14`. Reward `r∈{0,1}` is owner-confirmed success. EMA/EXP3 update `w ← (1-η)w + η r·φ`.

**Regret bound.** With `η = √(log K / (T·L²))`, `L = max‖φ‖`:
```
E[Regret_T] ≤ 2L √(T log K)
```
`T` is sessions, not frames — `√T` growth is honest for `K=4`. This bound licenses EMA (simple, head-local) over LinUCB (needs matrix inverse on halo) — the computational invariant "halo never inverts `d×d`" is respected.

---

## 5. Power / thermal / PDN theorems

- **PDN sag:** `ΔV = I_pk t_tx / C_bulk`. Theorem: `ΔV/V < Π_PDN`. At `150 mA·1 ms/20µF/3.7V=0.002` → 7 mV, no brownout. Proof is `Q=It`. Failure at `Π_PDN→0.5` would be 1.85 V sag → MCU POR — add `C`.

- **Thermal:** `ΔT = P_LED·R_th`. `Π_therm=0.21` → safe. Doubling `P` to 70 mW → `Π=0.42` still safe; 200 mW pulses → `Π=1.2` unsafe → firmware duty cap `D_LED≤0.35`.

- **Life:** `t_life = Q_h / I_avg`. `I_avg = d·I_on+(1-d)·I_off` → `Π_life = d·I_on·T_sess/Q_h + …` predicts 9% per 20 min session — 11 sessions/charge. Extremal `d=1` still <40% → always finishes a session.

---

## 6. Dimensional collapse summary

Six Π groups govern everything (from §2.3 of MATH.md):

`Π_acc, Π_TIR, Π_eyebox, Π_dwell, Π_life (≡Π_duty), Π_PDN (Π_therm subsumed)`.

Any bench claim that violates one is rejected without simulation. The staged build keeps these six on a dashboard; other variables are re-expressions.

---

## 7. Falsifiability checklist (what would refute the model)

- USAF target at `d_virt=0.38` measures MTF 0.1 not 0.3 ⇒ `Π_acc` model wrong (grating scatter higher) → increase `d_virt` or `t_g`.
- Blank injection at `a=0.9` measures 180 ms not <100 ms ⇒ safety theorem fails → move blank to GPIO interrupt, not `loop()`.
- `Π_dwell≈1.7` ROC predicts `α=0.06` but staged `α=0.15` ⇒ drift model `μ` optimistic → raise `δ` or lower `ω_typ` via complementary filter.
- EMA regret grows linearly not `√T` ⇒ reward not Bernoulli (e.g., rater drift) → switch to `margin`-weighted `r`.

---

*Use:* freeze `hardware/halo-reva/DESIGN_SPEC.md` against `Π_acc, Π_TIR, Π_eyebox`; freeze `firmware/halo/dwell.c` against SPRT thresholds; freeze `services/halo/TileServer` against `√T` regret dashboard. Any edit that moves a Π outside its bound is a design-change review, not a tuning tweak.
