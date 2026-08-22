# Collar Rev-A mathematics

Applied model of the **dog-worn puck** as a physical sampling system. Not a fit of TriadNet (that is [docs/MATH.md](../../docs/MATH.md)). Every constant here is measurable on the bench.

## System (plain language)

A small box rides on a dog’s neck. It feels shake and hears sound. It cannot shock, buzz, or open a door. Every so often it tells a phone a short summary: “this is what I think the dog is about to do.” The box runs on a battery that slowly empties, and on radio bursts that briefly gulp current.

## Inventory

**Entities:** dog body, puck, LiPo cell, 3.3 V rail, IMU, microphone, radio, phone, (optional) passive ID tag in the plastic.

**Actions:** continuous motion and sound; discrete BLE advertisements and 1 Hz summary frames; discrete clip-upload on a trigger; sleep/wake (Rev-B).

**Measurable quantities (with units):**

| Quantity | Symbol | Unit |
|----------|--------|------|
| Cell voltage | \(V_{BAT}\) | V |
| Cell capacity | \(Q\) | mAh (charge) |
| Rail current, average / peak | \(I_{avg},\ I_{pk}\) | mA |
| IMU sample rate | \(f_{imu}\) | Hz |
| Mic sample rate | \(f_{mic}\) | Hz |
| Summary rate | \(f_{sum}\) | Hz |
| BLE TX duration | \(t_{tx}\) | s |
| Packet size | \(N_{B}\) | bytes |
| Acceleration | \(a\) | m/s² (report as g) |
| Time | \(t\) | s |

**Constraints:** no actuator nets; GPIO0/3/45/46 not live; ADC2 unused; \(V_{ADC} \le 3.1\ \mathrm{V}\); ethics = observation only.

## Representations

**Diagram** — power waterfall then sensors, in [DESIGN_SPEC.md](DESIGN_SPEC.md).

**Time series (Rev-A loop, 1 second):**

```
t=0.00  IMU DMA frame (100 samples queued from last second)
t=0.00  mic hop (16k samples) → bark / RMS features
t=0.05  fuse → 1 Hz CBOR notify
t=0.06  BLE idle / advertising
t=0.10–1.00  boring stretch: sensors run, radio mostly off
```

The boring stretch is where battery life is won or lost. Drama (BLE TX, Wi-Fi clip) is rare.

**Hand-worked energy example.** 180 mAh cell, 12 mA average:

\[
t_{life} = \frac{180\ \mathrm{mAh}}{12\ \mathrm{mA}} = 15\ \mathrm{h}
\]

One 150 mA BLE pulse of 2 ms every second adds average \(150 \times 0.002 = 0.30\ \mathrm{mA}\) — 2.5 % of the 12 mA budget. **Radio is not the average-current story; the IMU+mic always-on path is.** That is the underutilized fact: duty-cycle the mic, not the radio, if you need a second day.

## Candidate invariants

| Kind | Candidate | Break attempt |
|------|-----------|---------------|
| Bounded | \(0 \le V_{ADC} \le 3.1\ \mathrm{V}\) | 4.2 V cell through ½ divider = 2.10 V. Holds. Unbalanced divider or missing bottom R **breaks it** — ERC/firmware clamp. |
| Bounded | \(0 \le \mathrm{conf} \le 1\) | Already in triad spec. Collar must not emit outside. |
| Conserved (approx) | Charge \(Q\) except at USB | USB is the only source. Field: \(Q\) is monotone decreasing. |
| Monotone | Cumulative bark-event count | Firmware counter; never decreases except session reset. |
| Structural | Observational: no energy path from MCU to a coil | `aarf_sch` denylist. Adding a motor net is a hard fail, not a parameter. |

Failed narrow invariant: “current is constant.” False — BLE peaks. Broader: **charge on the cell plus charge into USB** is what accounts. In the field, USB=0 so \(Q\) falls monotonically.

## Candidate symmetries

- **Time-translation of summaries.** A 1 Hz frame should not depend on absolute wall clock, only on the last second of IMU/mic. Rules out firmware that bakes `millis()` into the feature vector.
- **Relabeling of dogs.** Hardware is the same puck; identity is the passive tag + phone pairing, not a resistor. Do not encode “this is Rex” in analog.
- **Description symmetry of acceleration.** Report IMU in g, not raw LSB, so a different full-scale setting does not leak into the model.
- **Broken symmetry:** left vs right mic channel. We tie L/R to GND (left only). That is an explicit, documented break — do not “fix” it with a second mic on Rev-A.

## Dimensionless groups

Relevant set: \(\{I_{avg}, Q, t, f_{sum}, N_B, V_{BAT}, C_{bulk}\}\).

1. **Depth of discharge per hour:** \(\Pi_1 = I_{avg} / Q\) with \(Q\) in mA and hours implicit → life in hours is \(1/\Pi_1\).
2. **Radio duty:** \(\Pi_2 = t_{tx} f_{sum}\) (dimensionless). Rev-A target \(\Pi_2 \ll 1\) (2 ms × 1 Hz = 0.002).
3. **PDN sag:** \(\Pi_3 = I_{pk} t_{tx} / (C_{bulk} V_{BAT})\). With 10 µF, 150 mA, 1 ms, 3.7 V: \(\Pi_3 \approx 0.004\) — sag is millivolts, not brownout.

Limiting cases: \(\Pi_2 \to 1\) (radio always on) kills the battery in hours even if sensors are off. \(\Pi_3 \to 1\) means the bulk cap cannot feed a pulse — add capacitance or shorten \(t_{tx}\).

## State variables

Raw IMU history is **not** Markov for intent (“was the dog walking toward the door”). The summary that restores a usable state for the 1 Hz frame:

\[
s = \big(\mathrm{RMS}(a),\ \mathrm{peak}(a),\ \mathrm{band\ energy},\ \mathrm{audio\ RMS},\ \mathrm{bark\ flag},\ V_{BAT}\big)
\]

over the last 1 s window. That matches the existing physio/vocal encoders on the phone/runtime. The collar does **not** run full TriadNet on Rev-A; it ships \(s\) (and optional 1 Hz triad if an on-puck ONNX path lands later).

Markov test: two windows with the same RMS but one “start of a jump” vs “end of a jump” differ in **peak and kurtosis**. So RMS alone is insufficient — keep peak. That is why the IMU path copies the JetPuck-style feature set, not a single accelerometer magnitude.

Slow variable: \(V_{BAT}\) (minutes). Fast: IMU (10 ms). Slaving: treat \(V_{BAT}\) constant inside a 1 s window.

## Is this optimization?

Rev-A firmware is **not** an optimizer. The only decision is “emit summary vs stay quiet,” and even that is a fixed 1 Hz. Clip-upload is a **soft** preference (Wi-Fi when RSSI allows) with a **hard** constraint (never actuate).

Information structure: the puck does not know the camera picture. It must not open a door. Identity+intent+human confirm live on other nodes.

## Conceptual model

**Category:** hybrid — continuous sampling (IMU/I2S) + discrete 1 Hz frames (CBOR notify) + rare Wi-Fi bursts.

Skeleton: `IDLE → SAMPLE → TRANSMIT → (SLEEP stub) → IDLE` with a 1 s cycle and a task watchdog > cycle.

Add complexity one piece at a time: IMU first, then mic, then BLE, then Wi-Fi clips. Re-check: still no actuator; still ADC1; still packet fits MTU.

## Simplifications and cost

| Simplification | Estimated cost |
|----------------|----------------|
| No 32 kHz crystal | Sleep clock ~5 %; Rev-A barely sleeps |
| No fuel gauge | SoC error ~5–10 % vs 1 % |
| 1 Hz triad, not 15 fps | Misses sub-second intent flips; camera still owns that |
| Mic always-on | Dominant mA; see \(\Pi_1\) |

## Domain of validity — where this should fail

- Soaking wet enclosure (mic port).
- Two dogs, one puck (identity is the tag, not the IMU).
- Sprint + BLE + Wi-Fi at once on a 100 mA USB current limit (brownout) — use the cell.
- Treating collar confidence as a door-open command (ethics + information structure).

## Failed guesses

| Guess | Why it failed |
|-------|----------------|
| “ESP32-CAM can run YOLO on the collar” | Compute/thermals; collar is IMU+mic |
| “Classic ESP32 strapping map” | Wrong silicon; S3 GPIO15 is legal for I2S |
| “Radio is what drains the cell” | Hand example: \(\Pi_2=0.002\); sensors win |
| “Auto-open the gate from intent” | Missing information (whose dog, pinch, owner) and ethics |

## Experiments before solutions

1. Current-limited USB bring-up (see DESIGN_SPEC).
2. I2C scan 0x68; 100 Hz IMU RMS while walking the board in a pocket.
3. I2S RMS clap test.
4. BLE notify 1 Hz; confirm payload \(\le\) MTU−3.
5. DMM vs ADC at three cell voltages.

See [AFE_CALCULATIONS.md](AFE_CALCULATIONS.md) and [docs/FIRMWARE_COLLAR.md](../../docs/FIRMWARE_COLLAR.md).
