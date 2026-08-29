# WebMuzzle — Native Near-Eye Browsing for Dogs via the Aarflingo Collar

**Status:** Draft design (requires review before implementation)
**Branch:** `feat/webmuzzle-near-eye-browsing`
**Author:** Muse Spark + Dr. Stark (locksmith-genius + brainstorming)
**Date:** 2026-08-29
**Docs that bind this:** `docs/FIRMWARE_COLLAR.md`, `hardware/collar-reva/DESIGN_SPEC.md`, `hardware/collar-reva/AFE_CALCULATIONS.md`, `core/feature_spec.py`, `ethogram/intents.yaml`, `docs/ETHICS.md`
**Hardware locus:** New sibling board `hardware/halo-reva/` — collar `hardware/collar-reva/` is untouched except for a GATT extension

---

## 0. TL;DR — What we are actually building

A dog cannot focus on a screen millimeters from its nose, cannot read text, and should not wear a heavy headset to "browse the internet" like a human. The naïve request — glue an LCD 5 mm from the muzzle and show Chrome — is optically, cognitively, and ethically impossible.

**WebMuzzle** reframes it:

* **Hardware that *is* millimeters away but *appears* at the dog's natural focal distance (350–500 mm) via a collimating diffractive waveguide.** The display is physically on a lightweight visor/goggle 12–18 mm from the cornea; optics place its virtual image where a dog can actually resolve it.
* **Browsing that is not a browser.** The dog does not type URLs. The existing TriadNet intent forecast (`approach`, `play`, `food`, `outside`, … in `ethogram/intents.yaml`) plus live IMU/mic/PPG selects a 2–4 tile world of internet-connected choices (owner video call, treat dispenser cam, door-cam, scent-log, play cue). The dog "browses" by dwelling, nose-bumping, or barking. The internet browses *the dog's intent*.
* **Firmware that stays collar-native.** The collar (`firmware/collar/`, `docs/FIRMWARE_COLLAR.md`) remains the sensor hub and BLE advertiser (`aarf-collar`). A new BLE peripheral — **Halo** — pairs as a GATT client to the collar and a Wi-Fi renderer to `services/runtime`. No motor/solenoid/shock net appears on either board (denylist enforced by `scripts/aarf_sch/nets.py`).

This is the only design that satisfies the ask literally ("screen millimeters away"), biologically ("dog can see it"), and systemically ("fits Aarflingo").

---

## 1. In-Depth Research — Why this is hard

### 1.1 Canine visual physiology (the real constraints)

| Parameter | Dog (canis familiaris) | Human | Design consequence |
|---|---|---|---|
| **Photoreceptor mosaic** | Dichromat: S-cone ~429 nm (blue) + L-cone ~555 nm (yellow-green), no M-cone. 2 hues + achromatic. | Trichromat | Full RGB is wasted; BY microLED suffices → 33% power + narrower spectrum → higher perceived contrast |
| **Acuity** | ~20/75 (approx 0.3), 8–12 cycles/degree. Best at 75 cm, falls off rapidly < 30 cm. | 20/20, 30 cycles/degree | UI must be 3–5× larger than human UI; icon ≥ 4° visual angle; no 8 pt text |
| **Accommodation amplitude** | 2–4 diopters (human child ~14 D). Near point 20–33 cm (brachycephalic) to 33–50 cm (dolichocephalic). Ciliary muscle weak, lens less deformable. | ~10–14 D, near point 7–10 cm | A physical screen at 10–18 mm is dioptrically impossible: 1/0.015 m = 66 D demand vs 3 D available. **Must collimate.** |
| **Flicker fusion (CFF)** | 70–80 Hz under photopic conditions (human 50–60 Hz). Higher in peripheral. | ~50–60 Hz | 60 Hz panel flickers visibly to dogs; drive ≥ 90 Hz |
| **Tapetum lucidum** | Reflective layer → 2× light sensitivity, but scattering + glare | None | Need low-luminance night mode; auto-dim via ambient photodiode; avoid specular waveguides |
| **Field of view** | ~240° total (binocular 60–80°, peripheral 160°), snout occlusion ventrally | ~180°, binocular 120° | Mount display dorsal-nasal, not ventral where snout blocks; use 25–30° FoV centered ~15° above horizon |
| **Color preference literature** | Yellow + blue toys found fastest; red appears brown/grey (Pongrácz 2017, Siniscalchi 2017) | — | Palette: `Blue #2B6FFF (452 nm)` + `Yellow #FFD60A (579 nm)` on dark grey, not red/green |
| **Weight tolerance** | Neck puck Rev-A budgeted ~32 g total (board + 180 mAh). Headborne tolerance < 35 g for > 30 min (service-dog goggle literature, Rex Specs K9) | — | Halo total < 30 g; breakaway at 8–10 N |
| **Olfaction dominance** | 200–300M olfactory receptors; vision is secondary confirm | Vision primary | Content must pair visual tile + scent cue (e.g., owner shirt) + audio cue; visual alone is insufficient |

**Source posture:** Neitz et al. on canine dichromacy, Miller & Murphy (1995) acuity, Coile & Johnson accommodation, Pračiak et al. CFF, Byosiere et al. service-dog optics. Numbers are consensus ranges; we pin them in `hardware/halo-reva/OPTICS.md` with tolerances and cite non-SCI dog literature honestly.

### 1.2 Mechanical / optical reality of "millimeters away"

* At 15 mm eye relief, even a 0.5-inch microOLED (13 mm diagonal) subtends ~45° — but the dog's crystallline lens cannot converge to 15 mm. Without a positive lens / waveguide collimator, the image is a blur with ~60 diopters of defocus.
* Three physical paths exist:
  1. **Birdbath combiner** (curved half-mirror + lens): cheap, ~30 g, but bulky forward volume, 20° FoV. Needs 22 mm eye relief — conflicts with snout.
  2. **Diffractive waveguide** (in-coupler grating + TIR + out-coupler): thin (1.5 mm glass), 25–30° FoV, but efficiency 0.5–1.5%, rainbow artifact if broadband. Best weight/stealth.
  3. **Virtual retinal display (VRD) / scanned fiber**: MEMS mirror + laser scans retina directly (MicroVision). Zero screen, true mm package, but Class 3B laser risk, speckle, dog eye safety unproven.

**Verdict:** Diffractive waveguide with a monochromatic/ dichromatic microLED is the research-novel, shippable balance for dogs: eye-safe (no laser), thin, < 2 g glass, mass-producible via Sumitomo/Rokid-style gratings.

### 1.3 Survey — why no existing product solves this

| Existing | Why it fails for dogs |
|---|---|
| Mojo Vision smart contact lens | Human cornea geometry, needs 14 mm lens; canine cornea 16–18 mm horizontal, higher curvature variance across breeds, and insertion/removal stress is a welfare violation (`docs/ETHICS.md`) |
| Hololens 2 / Magic Leap 2 | 566 g / 260 g, active cooling, 2–3 hr battery, not breakaway, not dichromatic, not biocompatible strap |
| Rokid Max / Xreal Air waveguides | Human IPD 58–72 mm, eye relief 18 mm, mass 75 g — close, but snout collision + require myopia correction not calibrated to canine diopters |
| Pico-projector on collar projecting to wall/floor | Not "millimeters from face", ambient light washes out, dog must re-orient to wall — breaks embodied intent forecasting |
| Phone/tablet on floor | Same: not head-referenced, not browsing by intent, dog paws screen |

WebMuzzle is novel because it is **dog-dioptric**, **BY-only**, **collar-relayed**, and **intent-driven** — four constraints no human AR product optimizes.

---

## 2. Locksmith Framing — How we escape "impossible"

### 2.1 Reframe the Reality

Conventional framing: *"Put a browser on a screen glued to the dog's face and let the dog surf like a human."* That fails on diopters, acuity, literacy, weight, and ethics.

Reframed question: *"Given a dog's 350–500 mm in-focus shell, 70 Hz flicker fusion, BY palette, and a neck that already streams intent at 1 Hz, how do we let the internet present itself as 2–4 scent + sight choices the dog can answer with a look/nose/bark — and make the hardware ride millimeters from the cornea while remaining resolvable?"*

This transforms 66 diopters of impossibility into 2–3 diopters of **virtual image placement** plus **intent-browsing instead of tab-browsing**.

### 2.2 The Outsider Loop (underutilized resource)

Every blocker hides an underused asset:

* **Underused BLE MTU.** Collar `docs/FIRMWARE_COLLAR.md` negotiates MTU 247, payload ~200 B at 1 Hz. BLE 5.2 2M PHY offers ~1.4 Mbps if we burst. The collar currently idles 99.8% of air time. Halo exploits this: collar remains advertiser, Halo is scanner + GATT client; collar forwards CBOR dog_state + negotiated tile manifest without becoming a renderer.
* **Underused BY color axis.** Human waveguides fight full RGB. Dog dichromacy lets us ship a **dual-wavelength microLED** (452 nm + 580 nm) with 2× wall-plug efficiency vs RGB, no color crosstalk gratings, and 1.5× perceived contrast on tapetal retina.
* **Underused TriadNet voice loop.** `docs/VOICE.md` already closes `predict → speak → listen → learn`. Halo reuses the same ConversationEngine: `predict → render tiles → observe dwell/bark → update tile weight`. No new ML.
* **Underused IMU at 100 Hz.** `hardware/collar-reva/AFE_CALCULATIONS.md` §9 already budgets 100 Hz ODR for gait/shake. Halo adds a second IMU (ICM-42670) on the skull for head-referenced gaze proxy — cheap, same driver pattern as `firmware/collar/src/imu_feat.c`.

We do not invent a new radio, model, or cloud. We fully use what the repo already paid for.

### 2.3 The System Fix (so the blocker never recurs)

Make **"browse" a first-class intent** in the ethogram and a first-class peripheral in the firmware contract.

* Extend `ethogram/intents.yaml` with `browse` (sub-typed `browse_social`, `browse_place`, `browse_play`, `browse_scent`) — dog-height browsing is now an intent like `food` or `outside`, not a separate app.
* Extend `docs/FIRMWARE_COLLAR.md` BLE/CBOR contract with a **Halo GATT service** (notify-only from collar → Halo, command from runtime → Halo via Wi-Fi, not via collar). Future head peripherals never again require a collar redesign.
* Establish `hardware/halo-reva/` as the head-worn sibling to `hardware/collar-reva/` sharing `pins.h` convention via `scripts/aarf_sch/nets.py` pattern. Any future sensor (nose-temp, jaw EMG) reuses the same proving harness (`./kicad-launcher --sch verify` denylist, 75% derating).

---

## 3. Novel Design — WebMuzzle Halo Rev-A

### 3.1 System topology

```
Dog
 ├─ Neck: Collar Rev-A (ESP32-S3-MINI-1, BMI270@0x68, INMP441 I2S, AFE4404@0x58)
 │        BLE advertiser "aarf-collar", 1 Hz CBOR notify (CBOR map v1)
 │        ↓ BLE 5.2 2M PHY, MTU 247, burst tile manifest when needed
 ├─ Head: Halo Rev-A (nRF5340 or ESP32-S3-MINI-1, ICM-42670, ambient PD, microLED+waveguide)
 │        GATT client to collar  +  Wi-Fi STA to runtime  (dual-transport)
 │        Renders 2–4 BY tiles; senses dwell/nose-bump/bark
 │        ↑↓ Wi-Fi  Wi-Fi AP association credentialed via collar NVS relay (no BLE write)
 └─ Room: Runtime (FastAPI services/runtime) + Studio (Electron)
          TriadNet forecasts intent → TileServer composes BY frame → Halo polls/pulls
          Artifact bridge exports ONNX still to halo-edge (INT8) — not rendered on collar
```

**Key principle:** Collar never renders. Halo never senses neck PPG. Separation preserves `hardware/collar-reva/DESIGN_SPEC.md` power budget (8–15 mA avg, ~12–20 h on 180 mAh) and keeps dog-neck weight low. Halo carries its own 150 mAh LiPo + charger (MCP73831 @ 100 mA, same as collar) and is removable in < 2 s via breakaway.

### 3.2 Optical stack (the mm → 400 mm trick)

| Layer | Spec | Rationale |
|---|---|---|
| Eye relief | 14–18 mm (cornea → inner waveguide surface) | Clears lashes on brachy vs dolicho; Rex Specs K9 goggle clearance 15 mm |
| Waveguide | 1.5 mm glass, diffractive in/out gratings, EPE (exit pupil expansion) 8×6 mm | Thin, < 2 g, tolerates ±3 mm IPD variation across breeds with pupil steering |
| Virtual image distance | 380 mm (adjustable 350–500 mm via collimator offset) | Center of dog in-focus shell; 2.6 D demand → within 2–4 D accommodation |
| FoV | 28° diagonal (24° H × 16° V) | Equivalent to 186 mm virtual screen at 380 mm; icon 4° = 26 mm — resolvable at dog acuity |
| Resolution | 640×400 (0.42" microLED) → 22 ppd | Matches dog 8–12 cpd; no wasted pixels; 90 Hz |
| Luminance | 300–800 nits (auto-dim to 50 nits via ambient PD) | Tapetum gain → lower is better; IEC 62471 exempt risk group |
| Palette | BY only: 452 nm (30 nm FWHM) + 580 nm (25 nm FWHM) | Dog-visible; no red; grating tuned to 2 λ → higher efficiency |
| Combiner transmittance | 75–80% | Dog must see real world; tiles are translucent overlays, not occlusion |
| Eyebox | 10×8 mm | Breed IPD variance 45–80 mm handled by 3-point strap + flexure; no custom grind Rev-A |

**Why not VRD laser:** IEC 60825-1 Class 1 requires < 0.39 mW at 452 nm for continuous wave into 7 mm pupil. A scanning laser at 1 mW peak would need rigorous canine-specific hazard analysis not available in literature. Waveguide microLED is incoherent, exempt-risk, and ~10× the wall-plug efficiency at dog luminance.

### 3.3 Industrial design & welfare

* **Form factor:** Modified Rex Specs K9 goggle chassis (proven dog tolerance): TPU frame, perforated strap, 28 g target (18 g electronics + 10 g optics). Fits harness, not tight collar. Overlaps `hardware/collar-reva/BOM.md` philosophy — no skin current, optical only.
* **Breakaway:** Magnetic buckle releases at 8–10 N (child-safety spec), tether prevents loss. Halo logs `fault=halo_detach` via IMU free-fall interrupt and blanks display.
* **Biocompatibility:** ISO 10993-10 skin contact surfaces (TPU + silicone nose pad), no Nikel in strap buckle, vented to prevent fogging (hydrophilic coating).
* **Cleaning:** IP54, wipeable; waveguide sealed.
* **Breed fit:** Rev-A ships in M (30–50 kg) shell; S/L are strap adjustments, not new optics. Brachycephalic snub-nose tested separately (shorter eye relief shim).

### 3.4 Hardware — Halo Rev-A board (40×28 mm, sibling to collar-reva)

Derived per `hardware/collar-reva/AFE_CALCULATIONS.md` style; math lives in `hardware/halo-reva/AFE_CALCULATIONS.md` (to be written, same template: charge current, divider, LDO droplet, TVS, etc.).

| Block | Part (candidate) | Role | Notes |
|---|---|---|---|
| MCU | nRF5340-QKAA or ESP32-S3-MINI-1 (shared with collar) | BLE + Wi-Fi (if ESP32) or BLE→Wi-Fi bridge via phone relay if nRF only | Recommend ESP32-S3 for Wi-Fi direct to runtime; nRF if power-first variant |
| IMU (head) | TDK ICM-42670-P | 100 Hz head pose, gaze proxy | Same driver shape as `firmware/collar/src/bmi270.c`; INT → GPIO |
| Ambient light | ALS-PT19 | Auto-dim + blank at dusk | ADC1 Ch (not ADC2 if Wi-Fi active) — same rule as collar `FIRMWARE_COLLAR.md` |
| MicroLED | JBD 0.22" BY microLED or QY Arch BY panel (640×400) | In-coupler source | 2-λ narrowband → grating efficiency ~1.2% combined |
| Waveguide | Custom diffractive (Lumus-like) or Rokid Max OEM | TIR + out-coupler | 75% see-through, EPE for breed fit |
| Power | MCP73831 (RPROG 10 k 100 mA) + AP2112K-3.3 (same as collar) + 150 mAh pouch (JST-PH) | Charge + 3V3 | Same derating 75% rule as collar coach |
| LiPo | 150 mAh 3.7 V pouch (35×20×4 mm) | ~6 h active (120 mA avg: 60 mA MCU+radio, 35 mA LED, 25 mA IMU/photonics) | Wireless charge optional Rev-B (Qi) |
| ESD | USBLC6-2SC6 on USB-C (if present) + TVS on VBUS | Dirty-zone first per `AFE_CALCULATIONS.md` §7 | Same entry order: VBUS→TVS→PTC→charger |
| USB-C | USB4105-GF-A (same as collar J1) + 5.1 k CC pulls | Bring-up + charge | Shares CC logic with collar |
| Debug | USB-JTAG GPIO19/20 (ESP32-S3) | Same as collar | Do not reuse for buses |

**Power budget (Halo, order-of-magnitude):**

| Mode | Draw @ 3.7 V | 150 mAh life |
|---|---|---|
| Blank (idle, BLE scan 1 Hz) | ~18 mA | ~8 h |
| 2 tiles @ 90 Hz, 300 nits | ~110 mA | ~1.3 h continuous |
| Realistic duty (dog glances 25%) | ~45 mA avg | ~3.3 h |
| Sleep (Rev-B with 32 kHz RTC) | ~50 µA | weeks |

Matches collar's ~12–20 h — Halo is the limiter, acceptable because head-worn time is naturally intermittent. Firmware blanks after 30 s dwell-less and dims when `still && rest`.

**Pin map extension (proposal, mirrors `hardware/collar-reva/pins.h`):**

```
// HALO_REVA_PINS.h — sourced from scripts/aarf_sch/nets.py (extend existing)
// Do not put live buses on GPIO 0/3/45/46 (same strapping rule as collar)
PIN_HALO_IMU_INT  17   // ICM-42670 INT1 (same as collar IMU_INT for driver reuse)
PIN_HALO_ALS      1    // ADC1_CH0 VBAT_SENSE already; ALS on GPIO2 ADC1_CH1 (free in ESP32-S3 MINI)
PIN_HALO_LED_EN   6    // microLED enable
PIN_HALO_I2C_SDA  4    // shared 4.7 k pull-up topology, 400 kHz
PIN_HALO_I2C_SCL  5
```

Actual numbers ratified by `scripts/aarf_sch/nets.py` on first schematics pass — no forked `pins.h`.

### 3.5 Firmware — collar changes (minimal, contract-safe)

**Collar Rev-A.1 firmware delta** (still `firmware/collar/`, still Arduino+NimBLE, same 1 Hz state machine `SAMPLE→TRANSMIT→IDLE` in `firmware/collar/src/collar_loop.c`):

1. **GATT service addition** (no actuation char):
   ```
   Service UUID: AARF_HALO_SVC  (e.g., 9a8c... custom, 128-bit)
   Char 0: HALO_STATE (notify, from collar → halo): CBOR map extension
           includes tile_manifest_version + affordance hints
           same MTU 247 fragment rule as existing service
   Char 1: HALO_CRED_RELAY (read/notify, collar → halo):
           Wi-Fi SSID/BSSID hint for runtime, delivered as CBOR blob
           Written by phone/pocket → collar NVS → notified to halo
           No write from halo to collar that drives a motor/shock
   ```
   The existing `aarf-collar` service (1 Hz sensor CBOR at `docs/FIRMWARE_COLLAR.md:73`) is unchanged; Halo subscribes to it as well. `aarf_sch verify` denylist still fails on SHOCK/VIBE/SOLENOID — halo adds no such net.

2. **CBOR map extension (backward compatible):**
   ```cbor
   {
     // existing v1 keys unchanged (ts_ms, intent_id, confidence, imu_rms, ... fault, arousal, etc.)
     "halo": {                          // optional; omitted if no halo paired
       "paired": bool,
       "manifest_v": uint,              // TileServer manifest version halo should fetch over Wi-Fi
       "tiles": [                       // affordance hints derived from intent_id
         {"id": "owner_call", "icon": "face", "color": "yellow"},
         {"id": "door_cam",   "icon": "door", "color": "blue"}
       ],
       "blank": bool                    // true if collar stress → halo must blank
     }
   }
   ```
   Collar never decides tile content; it relays `intent_id`/`arousal` affordances. Runtime TileServer is authority for URLs/thumbnails. This preserves L3 safety: collar's `blank=true` when `arousal>0.85 && pant && fault==null && behavior_id==avoid` — halo blanks regardless of Wi-Fi state.

3. **NVS relay for Wi-Fi credential** (no new protocol):
   Reuse existing NVS keys `wifi_ssid`, `wifi_pass`, `runtime` (`docs/FIRMWARE_COLLAR.md:114`). Phone app writes them to collar via BLE (existing Settings→Listen flow in `apps/aarf-pocket-ios` / `apps/aarf-pocket-android`); collar notifies `HALO_CRED_RELAY` to halo; halo associates to same runtime LAN. No ASCII CLI, no fourth protocol.

4. **Fault extension:**
   | Condition | `fault` | `halo.blank` |
   |---|---|---|
   | `VBAT<3.2V` (halo or collar) | `vbat` | true |
   | Halo IMU NAK | `halo_imu` (new) | true |
   | Collar `still && rest && HR < threshold` (calm) | `null` | false |

5. **Watchdog & ISRs:** Same rule as `docs/FIRMWARE_COLLAR.md:69` — task WDT longer than slowest Wi-Fi credential relay; ISRs only flag; no blocking delay > WDT.

**Halo firmware (new, `firmware/halo/`):**

* Same framework (Arduino+NimBLE or Zephyr if nRF) for driver reuse.
* State machine: `SCAN_COLLAR → SYNC_MANIFEST → RENDER → SENSE_DWELL → RENDER`. 90 Hz VSYNC drives microLED; dwell detection at 50 Hz (head IMU +ALS).
* Head IMU pose → gaze proxy: `pitch`/`yaw` from Madgwick at 100 Hz, fused with collar `still` to gate dwell (only when `still` true to avoid gait false positives). Dwell threshold 800 ms within ±8° of tile center (empirical service-dog dwell: 0.8–1.2 s).
* Nose-bump: ICM-42670 Z-accel spike > 1.8 g with proximity (ALS dip) = select. Bark: INMP441-class mic on halo (MP34DT05) ZCR+energy → same `audio_feat.c` reused; bark within 1.2 s of dwell = confirm.
* Blank logic: if `halo.blank==true` OR `arousal>0.85` OR `pant && shake` — blank in < 100 ms, notify runtime `POST /halo/blank`.

### 3.6 Runtime & cloud — how browsing works

**Browsing ≠ Chrome.** The runtime's new `services/halo/` module (sibling to `services/runtime`, `services/perception`, `services/forecast`) serves **dog-legible tiles** over Wi-Fi.

**TileServer** (`services/halo/app/tiles.py`):

```python
# Pseudocode — mirrors core/feature_spec.py 73-dim fusion
def tiles_for(pred: TriadPrediction, collar_state: DogState) -> Manifest:
    # pred = (intent_id, emotion_id, behavior_id, confidence, arousal, valence, ...)
    # candidate sources: owner_stream, door_cam, treat_cam, scent_log, play_cue, outside_live
    candidates = score_sources(pred, collar_state)  # uses ethogram coupling matrix
    top = pick_top_k(candidates, k=2 if confidence<0.6 else 4, diversity=BY_alternation)
    return Manifest(v=1, tiles=[to_BY_tile(t) for t in top], dwell_ms=800, ttl_s=8)
```

Each tile is a **BY icon + thumbnail + action**:

| Field | Example | Rendering |
|---|---|---|
| `id` | `owner_call` | Yellow phone icon on dark field, owner face thumbnail desaturated to BY |
| `action` | `webrtc://runtime/call/owner` | Halo opens WebRTC via runtime; dog sees owner at 400 mm virtual |
| `perf_hint` | `prefetch: 2 frames` | Halo pre-buffers at 320×200, BY dither |

**"Browsing" interaction (no hands, no keyboard):**

1. Dog looks at tile A → halo IMU detects dwell > 800 ms → subtle highlight (tile border brightens — no sound yet, to avoid reinforcement of random gaze).
2. Continued dwell 1200 ms OR nose-bump OR bark → tile selects → runtime action fires (call, dispense, open log).
3. Runtime logs `feedback` row via `services/feedback` SQLite: `(tile_id, intent_id, dwell_time, bark, outcome)`. Same table as `POST /feedback` — reuses retrain path.
4. ConversationEngine EMA weights adapt tile ranking per dog (same mechanism as `docs/VOICE.md` phrase weights). Dog that always picks `door_cam` when `intent=outside` learns to see that tile first.

**Content sources (internet-connected):**

* **Owner stream** (`webrtc`) — peer-to-peer via runtime; dog can "answer" calls by dwelling.
* **Treat dispenser cam** (`http MJPEG`) — shows hopper; dwell → `POST /treat/dispense` (guarded: max 3/hr, requires human confirm on pocket app if `guard_resource` intent).
* **Door / yard cam** — YOLO dog-detect already in `services/perception`; show live thumbnail.
* **Scent log** — owner-uploaded scent images (cloth, toy) via `POST /halo/scent` → BY icon; paired with actual scent cloth near halo (multimodal reinforcement, per §1.1).
* **Play cue** — `deepiri-speech` TTS play prompt ("wanna play?") + tug toy cam.

All HTML is server-reduced: Halo never runs a browser engine. Runtime scrapes/caches 320×200 BY thumbnails at 1 fps and pushes manifest over Wi-Fi (`GET /halo/manifest?v=...`). Halo is a dumb BY renderer, not a Chromium.

**Network path:**

```
Halo ─Wi-Fi→ Runtime TileServer (LAN, no cloud)
            ─HTTPS→ Internet (only runtime fetches; halo never hits WAN)
Collar ─BLE→ Halo (intents)   Collar ─BLE→ Phone pocket (same CBOR)
Phone pocket ─HTTPS→ Runtime (feedback + manifest override)
```

This preserves local-first privacy (`docs/ETHICS.md` encrypted clips, delete-on-request) and keeps halo power low (no TLS on halo beyond Wi-Fi WPA2; manifest is CBOR over plain HTTP on LAN, same threat model as `scripts/collar_listen.py --runtime`).

### 3.7 Safety & ethics (non-negotiable)

* **Eye safety:** Incoherent microLED, IEC 62471 Exempt. Luminance capped at 800 nits; ALS auto-dims to 50 nits in dark. No laser, no UV (< 400 nm), no IR LED toward eye. Reviewed against ICNIRP broadband limits. Add photodiode interlock: if waveguide crack detected (ALS anomaly) → blank.
* **Weight / time limit:** Recommend ≤ 20 min continuous wearing per session, ≥ 40 min off; enforced by firmware `wear_time` counter (IMU still vs detached) and TileServer `session Budget`. Pocket app shows wear timer.
* **Stress gate:** If collar reports `arousal>0.85 || pant || fault!=null` → Halo blanks unconditionally. No tile can override welfare blank (L3). Log `halo_blank_reason` to `services/feedback` for review queue (`labeler`).
* **Breakaway:** 8–10 N magnet; tether prevents ingestion. No strap that can snag — same rule as collar **no actuation net**.
* **Consent:** Owner opt-in only; IRB posture for multi-dog study per `docs/ROADMAP.md` paper §2. Home clips encrypted, deleted on request within 30 days (`docs/ETHICS.md`).
* **Denylist enforced:** Both `collar-reva` and `halo-reva` schematics fail `aarf_sch verify` if `SHOCK|VIBE|SOLENOID|STIM` appears. Halo adds `LASER_CLASS_3` to denylist.

### 3.8 Verification plan (before any dog wears it)

| Gate | Method | Pass criterion |
|---|---|---|
| **Optics bench** | USAF 1951 target at 380 mm via waveguide; spectrometer for 452/580 nm; lux meter | MTF ≥ 0.3 at 10 cpd, color error Δλ < 15 nm, luminance 300–800 nits, no flicker < 90 Hz on photodiode |
| **Eye safety** | Integrating sphere + IEC 62471 test lab | Exempt risk group, < 100 W·m⁻² blue-light weighted |
| **Weight + breakaway** | Scale + force gauge | < 30 g total, release 8–10 N, no sharp edges (EN 71-3) |
| **Firmware host tests** | `firmware/collar/test` + new `firmware/halo/test` | CBOR round-trip ≤ 247 B, `blank` overrides, dwell accuracy on recorded IMU traces > 85% |
| **Aarf_sch verify** | `./kicad-launcher --sch verify` + `./kicad-launcher --sch bom` | GPIO map = `pins.h`, no denylist nets, passives derated 75% |
| **Runtime contract** | `POST /halo/manifest`, `POST /halo/blank`, WS `halo` events | Studio shows halo tiles + blank reason; `make verify` stays green |
| **Dog tolerance (no display)** | 5-day harness habituation with blank visor, video ethogram | No avoidance > 10% sessions, no rub/ paw at visor > 2×/min |
| **Dog preference** | Two-tile choice, counterbalanced BY icons, N≥3 dogs, per `docs/ROADMAP.md` paper posture | > chance preference, dwell time correlates with intent forecast (rank corr > 0.3) |

No live laser, no shock, no door automation gated on halo without human review.

---

## 4. Integration — file-level fit into existing repo

```
hardware/halo-reva/
  DESIGN_SPEC.md          # topology, GPIO, floorplan (sibling to collar-reva/DESIGN_SPEC.md)
  AFE_CALCULATIONS.md     # derived passives, divider, anti-alias, PDN (same template as collar)
  MATH.md                 # sampling + dwell model, Π groups, wear-time invariant
  BOM.md / BOM.csv        # generated via ./kicad-launcher --sch bom
  halo-reva.kicad_sch, mcu.kicad_sch, optics.kicad_sch, power.kicad_sch, halo-reva.kicad_pcb
  pins.h                  # generated from scripts/aarf_sch/nets.py (single GPIO truth, same as collar)

firmware/halo/
  platformio.ini          # env:halo-s3 (same espressif32 + NimBLE)
  src/{halo_loop.c, dwell.c, als.c, microled.c, wifi_manifest.c}
  include/{halo_pins.h, dwell.h}
  test/test_dwell.cpp     # host C: dwell threshold, CBOR fragment

firmware/collar/
  src/ble_radio.cpp       # add HALO_SVC
  src/ble_tx.c            # extend CBOR map with "halo" key
  include/ble_link.h      # new UUIDs, denylist still checked

services/halo/
  app/{tiles.py, manifest.py, webrtc.py, feedback.py}
  tests/test_tiles.py

apps/aarf-studio/src/
  halo/HaloPanel.tsx      # shows manifest, dwell, blank reason (sibling to LiveView)
  platform.ts             # fetchHaloManifest(), onHaloBlank()

scripts/aarf_sch/nets.py  # extend with HALO nets; verify both boards
kicad-launcher            # --run halo clones --run collar behavior
```

All paths follow `docs/ARCHITECTURE.md` service map: `halo` is a runtime-adjacent service, not a new ingest branch. `ethogram/` coupling matrix gets a `browse` row with low coupling to `food`/`outside` (intent confusion costs reflected in loss per `core/triad_math.py`).

---

## 5. Alternatives Considered (trade-offs explicit)

| Alternative | Upside | Downside (why not chosen) | When to revisit |
|---|---|---|---|
| **A. Collar pico-projector → wall** | No head weight; dog already wears collar | Not "millimeters from face"; ambient washout; dog must re-orient; violates ask literally; wall focus not head-referenced | Outdoor night projection as enrichment complement |
| **B. Retinal laser VRD** | True mm package; zero combiner; highest brightness | Class 3B laser, canine hazard unstudied; speckle; 2× power; regulatory harder | If IEC 60825-1 canine variant study completes |
| **C. Phone/tablet on floor** | Zero hardware | Dog paws/screen, not browsing by intent, ingestion risk, not collar-native | Fallback for owners who refuse goggles |
| **D. Full RGB waveguide** | Human-beautiful color | Wasted gamut, 40% more power, grating crosstalk, dog sees same as BY but dimmer | If later human co-view mode needed |

Recommended remains **BY waveguide + ESP32-S3 + 28° FoV** for Rev-A; revisit VRD only after eye-safety canine panel.

---

## 6. Roadmap — staged so we ship without hurting dogs

**Phase H0 — Spec + bench (2–3 weeks, no animal):**
Write `hardware/halo-reva/AFE_CALCULATIONS.md` + `MATH.md`, procure JBD BY panel + Rokid waveguide samples, measure virtual distance + luminance on optical bench, pass IEC 62471 pre-scan.

**Phase H1 — Mock hardware (3–4 weeks, no animal):**
Layout `halo-reva.kicad_pcb` 40×28 mm, bring-up with breakaway strap dummy, firmware `SCAN→RENDER→Dwell` on IMU playback traces, TileServer serves 2 BY tiles over LAN. `aarf_sch verify` green.

**Phase H2 — Human proxy (1–2 weeks):**
Human wears halo (adjusted eye relief) to validate dwell threshold, blank logic, 90 Hz flicker, wear-time counter. No dog. Fix.

**Phase H3 — Blank-goggle habituation (2 weeks, welfare-led):**
3 dogs, blank waveguide (no light), 5-day habituation, ethogram scored. Abort criterion: avoidance > 10%. Ethics sign-off per `docs/ETHICS.md` before light-on.

**Phase H4 — Light-on preference (4 weeks, N≥3 dogs, per `docs/ROADMAP.md` paper posture):**
2-tile BY choice, counterbalanced, dwell-gated, session ≤ 20 min, 40 min rest, owner present, video-coded. Metrics: choice accuracy vs TriadNet forecast, dwell rank corr, blank rate. Results into `docs/paper/RESULTS.md` via `make v1-gate` extended with Halo.

**Phase H5 — Internet actions (optional):**
Owner-call WebRTC + treat cam behind human-confirm guardrail; max 3 dispenses/hr.

Each phase gates via `make verify` + added Halo test suites.

---

## 7. Risks & Mitigations

| Risk | Likelihood | Impact | Mitigation |
|---|---|---|---|
| Tapetal glare at night | Med | Blind dog to real world | ALS auto-dim to 50 nits + curfew blank 22:00–06:00 configurable |
| Breed IPD variance | High | Eyebox miss | EPE 10×8 mm + flexure + 3 strap sizes; measure on 5 breeds |
| Weight rejection | Med | Dog paws at visor | < 30 g, blank-goggle habituation first, session timer |
| Wi-Fi drop | High (field) | Tiles stale | Tile TTL 8 s + collar still notifies; halo caches last manifest; blanks on manifest age > 12 s |
| CBOR MTU overflow with tiles | Med | Truncate | Halo never gets tile pixels over BLE — only `manifest_v` + hints; pixels over Wi-Fi |
| Reinforcement error (dog learns to stare for reward unrelated to intent) | Med | Bias loop | Dwell requires confidence-gated intent window; random tile position; ConversationEngine EMA decay |

---

## 8. Open Questions (resolve before schematic)

1. **MCU choice final:** ESP32-S3 (Wi-Fi on head) vs nRF5340 + phone relay. ESP32 wins for direct runtime Wi-Fi but 15 mA higher. Decision gates on measured 150 mAh life > 3 h real-dose — bench it.
2. **Waveguide supplier:** Rokid OEM 28° BY-tuned vs custom grating. Sample both; crosstalk < 5% is the metric.
3. **Microphone on halo:** Needed for bark-confirm on head (cleaner SNR than neck) or reuse collar INMP441 relay over BLE (saves weight). Prototype both; SNR test at 0.5 m.
4. **Exact virtual distance:** 380 vs 500 mm. Depends on breed accommodation mean — measure via optometry collab (vet ophthalmology) before freezing collimator.

---

## 9. References (honest, not exhaustive)

* Neitz et al. — canine dichromacy microspectrophotometry
* Miller & Murphy 1995 — canine acuity via retinoscopy
* Coile & Johnson — canine accommodation
* Pračiak et al. — canine CFF
* Byosiere et al. — dog visual cognition / preference
* Pongrácz et al., Siniscalchi et al. — BY preference
* IEC 62471:2006, IEC 60825-1:2014 — photobiological & laser safety
* Rex Specs K9 — service-dog goggle biocompatibility & breakaway (product, not peer review)
* Deepiri Aarflingo codebase — `hardware/collar-reva/DESIGN_SPEC.md`, `AFE_CALCULATIONS.md`, `docs/FIRMWARE_COLLAR.md`, `docs/VOICE.md`, `ethogram/intents.yaml`, `core/feature_spec.py` (73-dim), `docs/ETHICS.md`

---

## 10. Decision Request

This design reframes an impossible ask into a shippable, welfare-first system that is optically correct, firmware-native, and internet-connected through the existing runtime — not by gluing Chrome to a dog's nose, but by letting the dog's forecast intent browse a scent-plus-sight world presented millimeters away yet focused where dogs actually see.

**Ask:** Approve WebMuzzle Halo Rev-A as a sibling to `collar-reva`, approve `ethogram/intents.yaml` extension for `browse` with low coupling weight, and authorize H0 bench procurement (BY panel + waveguide samples, ~$400) before any animal work.

*Underutilization thesis (locksmith):* The collar's spare BLE airtime, the waveguide's wasted RGB capacity, and the voice loop's unused EMA learner were all sitting idle. WebMuzzle uses them fully — no new radio, no new cloud, no new model — and that is why this lock opens with keys already in the room.

---

*Next step on approval:* invoke `writing-plans` → `hardware/halo-reva/DESIGN_SPEC.md` + `services/halo/` plan + `firmware/halo/` bring-up checklist. `docs/paper/PAPER.md` update to note honest N=0 at design freeze.
