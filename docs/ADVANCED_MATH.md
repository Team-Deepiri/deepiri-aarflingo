# Advanced Emotion Math (AARFLingo)

Research-backed mathematics for moving AARFLingo past "tail-wag = happy":
canine biomechanics, psychoacoustics, physiological signals, and multimodal
fusion. Each section states the equations, cites the source, and — where a
section already has a home in this repo — names the exact file/function to
land it in.

Companion to `docs/MATH.md` (current Triad math). Everything here is a
*proposal* to be wired through `core/feature_spec.py`; nothing below is
implemented yet.

---

## 1. Tail biomechanics (beyond wag rate)

**Base paper:** Ren, W., Wei, P., Yu, S., & Zhang, Y. Q. (2022). *Left-right
asymmetry and attractor-like dynamics of dog's tail wagging during dog-human
interactions.* iScience, 25(8), 104747.

### Kinematic state vector

Track the tail tip and build the per-frame state

\[
x(t) = \bigl[\theta(t),\ \omega(t),\ \alpha(t),\ h(t)\bigr]^{\mathsf T}
\]

where \(\theta\) is the wag angle (right = positive), \(\omega = d\theta/dt\)
angular velocity, \(\alpha = d^2\theta/dt^2\) angular acceleration, and \(h\)
the tail height relative to the spine horizontal.

Derived scalars per window:

- **Wag rate** — zero crossings of \(\theta(t)\) per second.
- **Amplitude** — \(\max_t \theta(t) - \min_t \theta(t)\) over the window.
- **Rhythmicity** — coefficient of variation of inter-wag intervals
  \(\mathrm{CV} = \sigma_{I} / \mu_{I}\); low CV with high rate → focused
  arousal, high CV → excitement/uncertainty.
- **Height** — mean \(\bar h\); above horizontal → confident/aroused, below →
  submissive/fearful.

### Lateralisation (valence bias)

From Quaranta et al. (2007) *Current Biology* — wag bias tracks emotional
valence. Over a window of length \(T\):

\[
\mathrm{AI}(t) =
\frac{\int_{t-T}^{t} \bigl[\theta_{\mathrm{right}}(\tau) -
\theta_{\mathrm{left}}(\tau)\bigr]\,d\tau}
{\int_{t-T}^{t} \bigl[\theta_{\mathrm{right}}(\tau) +
\theta_{\mathrm{left}}(\tau)\bigr]\,d\tau}
\]

\(\mathrm{AI} > 0\) → approach/positive; \(\mathrm{AI} < 0\) →
withdrawal/negative. A practical substitute for the camera when the collar
IMU is the only sensor: estimate \(\theta\) from body yaw acceleration
(outsider loop — see §7).

### Attractor-like dynamics: Lyapunov exponent

Wagging is not a stable oscillator; it visits stable and transitional states.
The largest Lyapunov exponent is

\[
\lambda = \lim_{t\to\infty}\lim_{\delta x(0)\to 0}
\frac{1}{t}\ln\frac{\|\delta x(t)\|}{\|\delta x(0)\|}
\]

- \(\lambda < 0\) → stable attractor (relaxed, predictable wagging)
- \(\lambda > 0\) → chaotic / transitional (emotional shift, uncertainty)
- \(\lambda \approx 0\) → marginal, on the boundary between states

**Attractor reconstruction** (Takens' theorem): embed the scalar series
\(\theta(t)\) into phase space with delay \(\tau\) and dimension \(m\):

\[
X(t) = \bigl[x(t),\ x(t+\tau),\ x(t+2\tau),\ \dots,\ x(t+(m-1)\tau)\bigr]
\]

The attractor's geometry shifts with emotional state; a shift in shape is a
state-change signature. The iScience study found each dog has a stable,
individual wagging signature, and that right-side bias developed over ~3 days
of human interaction — a time-sensitive familiarity signal.

### Where it lands

- New module `services/perception/app/tail.py`:
  `TailTrack` (state dataclass), `asymmetry_index(series)`, `wag_metrics(series)`,
  `lyapunov_estimator(series)`.
- Feature names appended to `core/feature_spec.py` `BASE_FEATURE_NAMES`:
  `tail_wag_rate`, `tail_amplitude`, `tail_velocity`, `tail_rhythmicity`,
  `tail_height`, `tail_asymmetry`, `tail_lyapunov`.
- Needs a tail-tip keypoint. `services/perception/app/pose.py` is bbox-geometry
  only today; `PoseEstimate` already documents a "keypoint head can override
  these" contract — implement the keypoint head here.

---

## 2. Face & mouth (DogFACS)

**Papers:** Waller, B. M., et al. (2013). *Paedomorphic facial expressions
give dogs a selective advantage.* PLOS ONE. — Boneh-Shitrit, T., et al.
(2022). *Explainable automated recognition of emotional states from canine
facial expressions.* Scientific Reports. — *Automated analysis of emotional
expressions in dogs based on geometric morphometrics* (2025), Sci. Rep. 15,
32331.

### Landmark displacement (geometric morphometrics)

Given \(L_j(t)\), the 2D position of landmark \(j\) at time \(t\), and a
neutral reference frame \(t_0\), the displacement for action unit (AU) \(j\) is

\[
d_j(t) = \bigl\| L_j(t) - L_j(t_0) \bigr\|_2
\]

Normalized AU intensity controls for breed morphology:

\[
I_j^{\mathrm{norm}}(t) = \frac{d_j(t)}{\bar d_{j,\mathrm{ref}}}
\]

where \(\bar d_{j,\mathrm{ref}}\) is the mean inter-landmark distance of that
dog's neutral face.

### Decision-tree classifier (Boneh-Shitrit et al., 2022)

Each node \(n\) splits on a DogFACS variable \(v\) with threshold \(\tau_v\):

\[
v \le \tau_v \rightarrow S_1, \qquad v > \tau_v \rightarrow S_2
\]

Deep learning reached >89% accuracy vs. 71% for the FACS decision tree, so
treat the tree as an explainable fallback, not the primary estimator.

### Linear predictive model

\[
P(\mathrm{emotion}) = \beta_0 + \beta_1 \cdot \mathrm{RbrowVar}
+ \beta_2 \cdot \mathrm{EarBaseDist} + \beta_3 \cdot \mathrm{MouthOpen} + \dots
\]

where \(\mathrm{RbrowVar}\) = variance of right-eyebrow→inner-eye distance
normalized by eye size. Reported ~83% accuracy for emotion condition.

### Mouth & tongue signals

- **Tongue protrusion** — slight, relaxed → contentment; wide panting tongue →
  stress/overheat (tongue temperature tracks sympathetic activation in
  thermal-imaging studies).
- **Licking frequency** — rapid repeated lip-licks → anxiety/appeasement; a
  2018 *Behavioural Processes* study used lick rate as a stress marker in
  unfamiliar environments.
- **Mouth corner tension** — retracted corners (smile-like) → affiliative;
  tight lips → fear/aggression.

### Where it lands

- Replace heuristics in `services/perception/app/face.py`
  (`estimate_face_signals` currently returns `whale_eye_likelihood` and
  `lip_lick_likelihood` as pure functions of `arousal_proxy`).
- New module `services/perception/app/facs.py`: `landmark_displacement`,
  `normalized_au_intensity`, `ear_angle`, `sclera_exposure`, `blink_rate`,
  `mouth_tension`.
- New `BASE_FEATURE_NAMES`: `facs_au_intensity_*`, `ear_angle`,
  `sclera_exposure`, `blink_rate`, `mouth_tension`.

---

## 3. Head angle & orientation

Track pitch \(\theta_p\) (up/down), yaw \(\theta_y\) (left/right), roll
\(\theta_r\) (tilt) relative to the spine.

### Rotation representation

\[
R_{\mathrm{head}} = R_z(\theta_y)\, R_y(\theta_p)\, R_x(\theta_r)
\]

Pitch down → submissive/sniffing, up → alert/dominant. Yaw away → avoidance;
direct stare → threat or interest. Combine yaw with gaze to quantify
attention-to-stimulus via cosine similarity between head vector and object
vector.

### Head cock (roll) as cognitive processing

From a 2020 *Animal Cognition* study — head-tilting correlates with auditory
attention. Quantify via roll-angle variance over a window:

\[
\sigma_{\theta_r}^2 = \frac{1}{T}\int_{t-T}^{t}
\bigl(\theta_r(\tau) - \bar\theta_r\bigr)^2\,d\tau
\]

Elevated \(\sigma_{\theta_r}^2\) → cognitive processing / auditory attention.

### Where it lands

- `PoseEstimate` in `services/perception/app/pose.py` gains
  `pitch/yaw/roll` (keypoint head) and `roll_variance` (needs the temporal
  buffer that `services/perception/app/temporal.py` already maintains for
  velocity).
- New `BASE_FEATURE_NAMES`: `head_pitch`, `head_yaw`, `head_roll_var`.

---

## 4. Psychoacoustics & audio features

### Classical acoustic descriptors

- **Fundamental frequency \(F_0\)** — perceived pitch; the lowest peak of the
  short-frame power spectrum. Higher \(F_0\) → arousal/distress; lower →
  threat/calm. (Yin & McCowan 2004, *Animal Behaviour*.)
- **Harmonic-to-noise ratio (HNR)** — tonality vs. noise via cepstral
  analysis. Counter-intuitively, dogs in positive contexts (food anticipation)
  showed *lower* HNR than negative contexts (separation). Do not read HNR as
  monotonic in valence.
- **Formants \(F_1, F_2\)** — vocal-tract resonances shaping sound color;
  snarling/howling have lower \(F_1\).
- **MFCCs** — standard spectral envelope coefficients (already extracted in
  `services/audio/app/mfcc.py`).
- **Burstiness** — model barks as a point process; inter-burst
  \(\mathrm{CV} = \sigma / \mu\). Short rapid barks → alarm; long spaced barks →
  loneliness/boredom.

### Cepstral representation

\[
c(n) = \mathrm{IDFT}\Bigl(\log \bigl| \mathrm{DFT}\bigl(x(t)\bigr) \bigr|^2 \Bigr)
\]

### Waveform-cepstrum dual-modal model (2026, EAAI)

"Decoding dog barking emotion from non-periodicity" — two complementary paths.

**Time-domain: Temporal Dynamic Graph (TDG).** Graph \(G=(V,E,W)\), nodes
\(v_t\) = time frames, edges connect nodes by rhythmic similarity. Node
feature:

\[
v_t = [\mathrm{RMS}_t,\ \mathrm{ZCR}_t,\ \Delta\mathrm{RMS}_t,\ \Delta\mathrm{ZCR}_t]
\]

Dynamic edge weight (Gaussian kernel × time-varying adaptation \(\alpha(t)\)):

\[
w_{ij} = \exp\!\left(-\frac{\|v_i - v_j\|_2^2}{2\sigma^2(t)}\right)\cdot\alpha(t)
\]

**Frequency-domain: Frequency-Harmonic Enhanced Selective State Space Model
(FH-Mamba).** Selective SSM with input-dependent state matrices:

\[
h'(t) = A(\Delta t)\,h(t) + B(\Delta t)\,u(t)
\]
\[
y(t) = C(\Delta t)\,h(t) + D(\Delta t)\,u(t)
\]

\(A,B,C,D\) depend on the input \(u(t)\), so the model dynamically focuses on
emotion-relevant mid/high harmonics and corrects spectral distortion.

**Fusion: 4D Bidirectional Weighted Frequency-Time Fusion (4D-BWFTF).**

\[
F_{\mathrm{fusion}} = W_f \cdot F_{\mathrm{freq}} \oplus W_t \cdot F_{\mathrm{time}}
\]

\[
W_f = \mathrm{softmax}\bigl(F_{\mathrm{time}}^{\mathsf T} W F_{\mathrm{freq}}\bigr),
\qquad
W_t = \mathrm{softmax}\bigl(F_{\mathrm{freq}}^{\mathsf T} W^{\mathsf T} F_{\mathrm{time}}\bigr)
\]

Reported 92.71% on DogEmotionSound (4,230 samples).

### Label generation (regression targets, 2026 arXiv)

Arousal from RMS energy (log mapping):

\[
A_{\mathrm{label}} = \log_{10}(\mathrm{RMS} + \epsilon)
\]

Valence as a weighted spectral combo plus emotion prior:

\[
V_{\mathrm{label}} = \alpha\cdot\mathrm{centroid} + \beta\cdot\mathrm{ZCR}
+ \gamma\cdot\log(\mathrm{RMS}) + \mathrm{prior}(\mathrm{emotion})
\]

This frames bark emotion as **continuous arousal/valence regression** instead
of discrete classes (see §9). The *EmotionalCanines* dataset (1,400
husky/shiba clips, continuous labels) is the reference corpus.

### Where it lands

- Extend `services/audio/app/mfcc.py` / new `services/audio/app/prosody.py`:
  `estimate_f0` (autocorrelation/YIN), `harmonic_to_noise_ratio` (cepstral),
  `formants`, `burstiness`, `audio_arousal_continuous`, `audio_valence_continuous`.
- The TDG + FH-Mamba stack is a new encoder path in `services/audio/app/train.py`
  alongside the existing MLP (`infer_vocal` at `train.py:169`).
- New `MODALITY_NAMES` in `core/modality_spec.py`: `audio_f0`, `audio_hnr`,
  `audio_formant_f1`, `audio_burstiness`, plus `audio_arousal` /
  `audio_valence` already present.

---

## 5. Ears & facial muscles

- **Ear angle** — geometric landmarks (ear base, tip) give an "ear-angle"
  relative to the skull. Forward → attention/interest; flattened → fear/
  submission; relaxed → neutral.
- **Sclera exposure ("whale eye")** — measure exposed sclera area via semantic
  segmentation; increased exposure → stress/anxiety (known in horses and dogs).
  Already surfaced as `whale_eye_likelihood` (heuristic) in `face.py`.
- **Blink rate** — video blink detection; rate > baseline by \(2\sigma\) flags
  distress:

\[
\mathrm{blink\_flag} = \bigl(\dot b(t) > \mu_b + 2\sigma_b\bigr)
\]

### Where it lands

- `services/perception/app/facs.py` (see §2). `ear_angle`, `sclera_exposure`,
  `blink_rate` computed from keypoints; keep the `face.py` heuristics as
  no-keypoint fallbacks.

---

## 6. Whole-body posture & gait

### Full kinematic state

\[
S(t) = \bigl[x_{\mathrm{COM}}, y_{\mathrm{COM}}, z_{\mathrm{COM}},
\dot x_{\mathrm{COM}}, \dot y_{\mathrm{COM}}, \dot z_{\mathrm{COM}},
\theta_{\mathrm{head}}, \phi_{\mathrm{head}}, \psi_{\mathrm{head}},
\theta_{\mathrm{tail}}, \omega_{\mathrm{tail}}, h_{\mathrm{tail}}\bigr]^{\mathsf T}
\]

### Center of mass (COM) shift

\[
\mathrm{COM}(t) = \frac{\sum_{i=1}^{N} m_i\, p_i(t)}{\sum_{i=1}^{N} m_i}
\]

with landmark positions \(p_i\) and estimated segment masses \(m_i\). Forward
lean → approach, backward lean → avoidance:

\[
\mathrm{AA}(t) = \frac{\mathrm{COM}_x(t) - \mathrm{COM}_x(t_0)}
{\bigl\| \mathrm{COM}(t) - \mathrm{COM}(t_0) \bigr\|_2}
\]

\(\mathrm{AA}>0\) → approach; \(\mathrm{AA}<0\) → avoidance.

### Gait: pacing vs. trotting

Foot-fall phase per limb:

\[
\phi_{\mathrm{limb}}(t) = \mathrm{atan2}\bigl(\dot y_{\mathrm{limb}},
\dot x_{\mathrm{limb}}\bigr)
\]

- Trot (diagonal, relaxed): \(\bigl|\phi_{LF} - \phi_{RH}\bigr| \approx \pi\)
- Pace (lateral, anxious/tense): \(\bigl|\phi_{LF} - \phi_{LH}\bigr| \approx \pi\)

### Freezing & piloerection

- **Freezing duration** — zero-velocity intervals from optical flow; sudden
  immobility → high alert/fear.
- **Piloerection** — sympathetic activation along the back; approximated by
  contour-deformation analysis.

### Where it lands

- COM: from keypoints in `services/perception/app/pose.py`; `AA(t)` needs the
  reference frame `t0` from `temporal.py`.
- Gait phase: from limb keypoints, new `services/perception/app/gait.py`.
- New `BASE_FEATURE_NAMES`: `com_shift_x`, `approach_avoid`,
  `gait_phase_trot`, `gait_phase_pace`, `freeze_duration`.

---

## 7. System-level: cross-modal synchrony & physiology

Instead of each signal in isolation, model *coupling*:

- **Tail-wag ↔ respiration synchrony** — aligned phases → coherent emotional
  state; desync → conflict. Compute a phase-locking value or cross-correlation
  over a window.
- **Heart rate variability (HRV)** — low LF/HF → chronic stress; high HRV with
  appropriate movement → relaxation.
- **Galvanic skin response (GSR)** — sympathetic sweat; gold-standard arousal
  channel. Physio module today is ECG+IMU only
  (`lib/aarf-physio/aarf_physio/`); GSR is a sensor addition plus a new
  feature source.

**Fusion options:** latent emotional state via Kalman filter (linear-Gaussian
assumption, cheap, online) or a recurrent network (TriadNet upgrade, §9).
Treat each signal as a continuous trajectory in a high-dimensional phase
space, then cluster trajectories on labelled events (feeding, playing,
stranger, …).

### Architect reframe

1. **Reframe reality** — stop asking "is the dog happy?"; ask "what is the
   dog's arousal–valence state in real time?". Continuous 2D space, not a
   binary label.
2. **Outsider loop** — collar (IMU + mic + ECG) makes the dog itself the
   sensor; tail lateralisation can be inferred from body accelerations when
   the camera can't see the tail.
3. **System-level fix** — active learning: feedback buttons
   (`services/feedback/`) continuously map behaviour → human corrections,
   building a personalized per-dog "emotional signature". The feedback loop
   exists; expand it to capture the §1–§6 metrics.

---

## 8. HRV & physiological math

NN intervals (normal-to-normal): \(\{RR_1, \dots, RR_N\}\).

**SDNN** (overall HRV):

\[
\mathrm{SDNN} = \sqrt{\frac{1}{N-1}\sum_{i=1}^{N}(RR_i - \overline{RR})^2}
\]

**rMSSD** (short-term, parasympathetic):

\[
\mathrm{rMSSD} = \sqrt{\frac{1}{N-1}\sum_{i=1}^{N-1}(RR_{i+1} - RR_i)^2}
\]

**LF/HF ratio** (spectral power ratio; dog bands ~0.04–0.15 Hz LF,
0.15–0.40 Hz HF):

\[
\frac{\mathrm{LF}}{\mathrm{HF}} =
\frac{\int_{0.04}^{0.15} \mathrm{PSD}(f)\,df}
{\int_{0.15}^{0.40} \mathrm{PSD}(f)\,df}
\]

Low LF/HF → parasympathetic (relaxed); high → sympathetic (stress/arousal).
HRV alone: 88% within-dog, 72% across-subjects emotion classification.

**Caveat:** SDNN is inflated by physical activity, so HRV must be read against
IMU activity (`imu_activity`) — a motion artifact correction, not optional.

### Where it lands

- `lib/aarf-physio/aarf_physio/ecg.py`: add `lf_hf_ratio(rr_ms, sample_rate)`
  (Welch/FFT PSD). SDNN/rMSSD already in `hrv_features` at `ecg.py:60`.
- Extend `VitalsEncoder.features_to_tensor` in
  `lib/aarf-physio/aarf_physio/model.py:29` and
  `modality_from_vitals` at `model.py:43`.
- New `MODALITY_NAMES`: `ecg_lfhf`, `ecg_rmssd_norm`.

---

## 9. Model-level math

### BiLSTM + attention (canine audio; HIT paper)

Forward/backward LSTM states:

\[
\vec h_t = \mathrm{LSTM}(x_t, \vec h_{t-1}), \qquad
\overleftarrow{h}_t = \mathrm{LSTM}(x_t, \overleftarrow{h}_{t+1}),
\qquad H_t = [\vec h_t; \overleftarrow{h}_t]
\]

Gates (forget \(f\), input \(i\), candidate \(\tilde C\), output \(o\)):

\[
f_i = \sigma(W_f[h_{i-1}, x_i] + b_f), \quad
i_i = \sigma(W_i[h_{i-1}, x_i] + b_i), \quad
\tilde C_i = \tanh(W_c[h_{i-1}, x_i] + b_c)
\]

\[
C_i = f_i \cdot C_{i-1} + i_i \cdot \tilde C_i, \qquad
o_i = \sigma(W_o[h_{i-1}, x_i] + b_o), \qquad
h_i = o_i \cdot \tanh(C_i)
\]

Bahdanau attention over encoder states \(H = \{h_1,\dots,h_T\}\):

\[
e_{ij} = \tanh(W_f h_i + b_j), \qquad
a_{ij} = \frac{\exp(e_{ij})}{\sum_{k=1}^{n}\exp(e_{ik})}, \qquad
h_i' = a_{ij}\, h_i
\]

### Multimodal fusion: window statistics + PCA + ExtraTrees (PRL 2025, F1 = 0.96)

Per window \(X_{\mathrm{window}} = \{x(t), \dots, x(t+T-1)\}\):

\[
\mu = \frac{1}{T}\sum_{t=1}^{T} x(t), \qquad
\sigma^2 = \frac{1}{T}\sum_{t=1}^{T}(x(t)-\mu)^2
\]

\[
\mathrm{skew} = \frac{1}{T}\sum_{t=1}^{T}\left(\frac{x(t)-\mu}{\sigma}\right)^3,
\qquad
\mathrm{kurt} = \frac{1}{T}\sum_{t=1}^{T}\left(\frac{x(t)-\mu}{\sigma}\right)^4 - 3
\]

plus zero-crossing rate and energy \(E = \sum_t x(t)^2\). Concatenate all
modality stats, PCA-reduce, classify:

\[
Z = X\,W_{\mathrm{pca}}, \qquad
\hat y = \frac{1}{M}\sum_{m=1}^{M} T_m(X)
\]

Key finding: inertial + physiological data *outperform* visual data for
emotion detection. PATITA device streams: skin potential (SP), muscle
potential (MP), respiration frequency (RF), voice pattern (VP).

### MoCo unsupervised pretraining (MDPI 2024)

InfoNCE contrastive loss:

\[
\mathcal{L}_{\mathrm{contrast}} = -\log
\frac{\exp(q\cdot k^+/\tau)}
{\exp(q\cdot k^+/\tau) + \sum_{i=1}^{K}\exp(q\cdot k_i/\tau)}
\]

with momentum update of the key encoder:

\[
\theta_k \leftarrow m\,\theta_k + (1-m)\,\theta_q, \qquad m \approx 0.999
\]

Reported 43.2% vs. 14% baseline on the 7 Panksepp emotions — useful as
unsupervised pretraining for TriadNet backbones.

### Continuous arousal/valence regression

The consensus upgrade: predict \(A \in [0,1]\), \(V \in [-1,1]\) (see §4 label
generation) as regression heads alongside (or instead of) the discrete
intent/emotion/behavior heads. Uses MSE loss instead of cross-entropy per head.

### Where it lands

- `services/forecast/app/triad_model.py`: TriadNet is currently a flat MLP
  (`input_dim = FEATURE_DIM * SEQUENCE_LEN` at `triad_model.py:39`). A temporal
  backbone (LSTM/GRU + attention) replaces or augments it; new
  `TriadNet.arousal_head`/`valence_head` for regression.
- `services/forecast/app/losses.py`: add MSE + combined classification/
  regression loss.
- `services/forecast/app/dataset.py`: synthetic rows
  (`_modality_for_intent` at `dataset.py:27`, `_synth_row` at `dataset.py:42`)
  must populate every new feature name, or they silently vectorize to 0.0.

---

## 10. Cross-cutting: where every change lands

The canonical vector lives in `core/feature_spec.py`
(`BASE_FEATURE_NAMES` + `MODALITY_NAMES` = `FEATURE_DIM`) and is consumed by:

| Consumer | File | Action on feature addition |
|---|---|---|
| Vector flatten | `core/triad_math.py:47` | auto (dim reads from spec) |
| Training model | `services/forecast/app/triad_model.py:39` | auto (input dim from `FEATURE_DIM`) |
| Synthetic training data | `services/forecast/app/dataset.py:44` | populate new names |
| ONNX export | `services/forecast/app/export_onnx.py:48` | auto (dummy input from spec) |
| ONNX decode | `core/onnx_decode.py` | verify dimension |
| Runtime audio merge | `services/runtime/app/engine.py:147` (`update_audio_modality`) | extend to `update_modalities` |
| Edge loop | `services/edge-runtime/app/loop.py:50` | auto (via `vectorize`) |
| Artifact verification | `scripts/verify_artifacts.py:55` | update sample row |
| Studio UI rail | `apps/aarf-studio/src/renderer/lib/labels.ts:86` | add labels for new features |

**Rule:** extend `BASE_FEATURE_NAMES` and `MODALITY_NAMES` *in the same commit*
— the invariant `FEATURE_DIM == len(BASE) + MODALITY_DIM` in
`core/tests/test_modality_spec.py:8` enforces it. Any spec change renumbers
every checkpoint/ONNX bundle and invalidates saved `feedback/store.py`
sequences — a versioned feature-spec bump, not a silent append.

---

## 11. References

- Quaranta, A., Siniscalchi, M., & Vallortigara, G. (2007). *Asymmetric
  tail-wagging responses by dogs to different emotive stimuli.* Current Biology.
- Ren, W., Wei, P., Yu, S., & Zhang, Y. Q. (2022). *Left-right asymmetry and
  attractor-like dynamics of dog's tail wagging during dog-human interactions.*
  iScience, 25(8), 104747.
- Waller, B. M., et al. (2013). *Paedomorphic facial expressions give dogs a
  selective advantage.* PLOS ONE.
- Boneh-Shitrit, T., et al. (2022). *Explainable automated recognition of
  emotional states from canine facial expressions.* Scientific Reports.
- Yin, S., & McCowan, B. (2004). *Barking in domestic dogs: context specificity
  and individual identification.* Animal Behaviour.
- Kujala, M. V., et al. (2017). *Emotion perception in dogs: a multimodal
  approach.* Frontiers in Psychology.
- Garcia-Loya, E., & Lopez-Nava, I. H. (2025). *Automatic canine emotion
  recognition through multimodal approach.* Pattern Recognition Letters, 196,
  351–357. (PATITA, F1 = 0.96)
- *Multi-Epiphysiological Indicator Dog Emotion Classification System* (2025).
  MDPI. (skin + muscle potential, XGBoost, 90.54%)
- *Decoding dog barking emotion from non-periodicity* (2026). Engineering
  Applications of Artificial Intelligence. (TDG + FH-Mamba, 92.71%)
- *Automated analysis of emotional expressions in dogs based on geometric
  morphometrics* (2025). Scientific Reports, 15, 32331. (DogFLW, 46 landmarks)
- *Investigating the capabilities of large vision language models in dog
  emotion recognition* (2025). Scientific Reports. (LVLM caution)
- Bhave, A., Hafner, A., Bhave, A., & Gloor, P. A. (2024). *Unsupervised
  Canine Emotion Recognition Using Momentum Contrast.* MDPI.
