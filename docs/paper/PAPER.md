# AARFLingo: An Observational System and Evaluation Protocol for Multimodal Canine Intent Forecasting

**Deepiri**  
Correspondence: `dev@deepiri.dev`  
Preprint · 21 August 2026 · Apache-2.0 code in [github.com/Team-Deepiri/deepiri-aarflingo](https://github.com/Team-Deepiri/deepiri-aarflingo)

This manuscript describes a working system and a scoring rule. It does **not** claim 95% home-dog accuracy. That bar is defined below and is currently unmet (\(N=0\) labeled home dogs).

---

## Abstract

Owners and researchers need a forecast of what a dog is about to do, not a shock after the fact. AARFLingo predicts a coupled triad — intent × emotion × surface behavior — from a room camera, an optional vocal encoder, and a notify-only neck-worn sensor puck. A 73-dimensional perception vector, stacked over 15 frames, feeds a multi-head classifier whose illegal combinations are rejected by an ethogram coupling matrix. The wearable is an ESP32-S3 puck (IMU, I2S microphone, dual-wavelength neck photoplethysmography, skin thermistor). It advertises Bluetooth Low Energy notifies and has no writable actuation characteristic.

We report only numbers that exist in this repository. Stanford Dogs breed top-1 is 74.6% on public photographs. Barkopedia-held-out vocal accuracy is 34.5% (298 real clips; synthetic vocal accuracy is 80.9% and does not count). Triad and vitals checkpoints reach validation accuracy 1.0 on synthetic rows; those scores do not count toward v1.0. The v1.0 field bar is dog-held-out intent accuracy \(\ge 0.95\) on at least three home dogs. As of this writing the home eval file is empty, so `bar_met` is false. The contribution of this preprint is the system, the ethics constraint, and the evaluation protocol a later labeled set must pass.

## 1. Introduction

Canine affect work often stops at a single axis (arousal, “happy/sad”) or a single sensor (a camera, a bark classifier, a heart-rate strap). Intent is a destination: the door, the toy, the bowl, withdrawal. AARFLingo treats intent, emotion, and behavior as one structured prediction so a play-bow cannot be paired with rest, and a door-oriented freeze can be read as “wants out” rather than as generic anxiety.

Three design choices follow from that framing.

First, the label space is an ethogram, not a free-text caption. Ten intents, seven emotions, and ten behaviors are listed in `ethogram/`. A coupling matrix names the triples that are allowed and the pairs that a runtime gate must reject.

Second, the wearable is observational. The Rev-A collar streams inertial, acoustic, and neck-photoplethysmographic features at 1 Hz over a notify-only GATT map. Firmware and schematic tests fail if shock, vibe, motor, or solenoid nets appear. Inference stays on a laptop, phone, or Jetson-class hub. The puck does not run a detector.

Third, the accuracy bar is dog-held-out. Random-frame splits and synthetic validation accuracy can be perfect while every new dog fails. `scripts/v1_gate.py --require-bar` is the test that a later home set must pass. It fails today.

This paper is the methods record for that system. Protocol files that a reviewer can run without reading the prose live beside it: `METHODS.md`, `RESULTS.md` (generated), `DATASHEET.md`, and `reproduce.md`.

## 2. Related work

**Vision.** Khosla et al. released Stanford Dogs, 120 breeds and 20,580 photographs, as a fine-grained categorization set [1]. We use it to pre-train a MobileNetV3 breed head (held-out top-1 74.6%) and as a source of real feature rows through the perception pipeline. Detection at runtime is YOLOv8n, class dog, with an OpenCV motion fallback when the ONNX weights are absent [2].

**Vocal affect.** Barkopedia / EmotionalCanines and DogSpeak provide labeled canine vocalizations [3,4]. Our vocal encoder is trained on all 298 real Barkopedia clips available in-tree plus synthetic fillers; checkpoint selection uses real held-out accuracy (34.5%), not the mixed 18.3% figure stored on an older manifest field.

**Physiology.** PhysioZoo publishes canine ECG with R-peaks and heart-rate variability (HRV) annotations [5]. Public neck and harness inertial sets exist on Mendeley [6]. The in-repo vitals encoder (`lib/aarf-physio`) is shaped after those corpora; the shipped `vitals.pt` was trained on synthetic windows and reports validation accuracy 1.0, which we treat as a smoke test.

**Tail and face.** Quaranta et al. showed that tail laterality tracks approach versus withdrawal [7]. Ren et al. measured attractor-like wag dynamics [8]. DogFACS catalogs facial action units for dogs [9]. AARFLingo reserves named slots for wag rate, amplitude, laterality, a Lyapunov-style rhythmicity proxy, and a small facial set (AU intensity, ear angle, sclera, blink, mouth tension). Those slots are computed by `services/perception/app/deepfusion.py` when pose and face estimates exist; they are zeros when the camera cannot see the dog.

**Time-to-contact.** Lee’s \(\tau\) is the distance-over-closing-rate used here as an approach feature toward annotated gaze zones (door, toy, bowl) [10].

What we do not claim is a prior field study of this triad on home dogs. That study is the v1.0 bar, and it has not been run.

## 3. Ethics and scope

AARFLingo is observational. It does not automate punishment, vibration, or restraint. The GATT map is notify-only; pocket clients do not write actuation characteristics. Owner opt-in is required. Clinic recordings need an IRB or equivalent. Delete-on-request is 30 days (`docs/ETHICS.md`).

Collar proxies named `arousal`, `still`, and `red` are autonomic or contact correlates. They are not valence, core temperature, cortisol, or SpO2. The red LED path is a second photoplethysmographic perfusion index, not a blood-gas measurement.

Low-confidence or forbidden triples default to human review. The runtime never opens a door or fires a stimulator.

## 4. System overview

A live session is a loop:

1. A USB or MIPI camera on a laptop or Jetson hub produces frames. On WSL the camera is an MJPEG bridge from Windows.
2. Perception emits the 55-dimensional visual base vector (presence, box, gaze zones, approach geometry, optional tail/face/gait).
3. Optional `POST /infer/audio` writes vocal arousal, valence, and bark probability into the shared modality block.
4. Optional `POST /infer/collar` maps the puck’s 1 Hz Concise Binary Object Representation (CBOR) map onto the existing electrocardiogram and inertial slots. No fourth wire protocol, and no new feature dimension.
5. Cross-modal synchrony (phase-locking value, lag correlation, a two-state Kalman fusion) fills `sync_*` when both streams are present.
6. Fifteen frames are flattened and scored by TriadNet (or a heuristic if the checkpoint is missing).
7. A coupling gate returns `pass`, `review`, or `reject`.
8. A human can correct the triad; `POST /live/retrain` fine-tunes from that SQLite log.

The Jetson image (`infra/docker/jetson.Dockerfile`) is an L4T hub. It does not run on the ESP32.

## 5. Ethogram and coupling

Intents: `approach`, `avoid`, `solicit_play`, `rest`, `guard_resource`, `explore`, `alert`, `outside`, `play`, `food`.

Emotions: `calm`, `content`, `excited`, `anxious`, `fearful`, `frustrated`, `conflicted`, each with a prior valence and arousal in `ethogram/emotions.yaml`.

Behaviors: `tail_wag_loose`, `tail_tucked`, `play_bow`, `lip_lick`, `whale_eye`, `hard_stare`, `yawning`, `sniff_ground`, `freeze`, `bark`.

The coupling matrix lists weighted triples (for example play + excited + play-bow at 0.9) and forbidden pairs (rest + play-bow; avoid + play-bow; rest + excited). Training adds a coupling loss \(\lambda \mathcal{L}_c\) with default \(\lambda = 0.3\). At inference, `gate_decision` rejects forbidden pairs and only passes a listed triple when mean-head confidence is at least 0.55.

## 6. Features

Let \(x_t \in \mathbb{R}^{73}\) be the concatenated vector at frame \(t\). `core/feature_spec.py` is the layout. The first 55 names are visual; the last 18 are modality outputs (`core/modality_spec.py`). A window of \(T=15\) frames is left-padded and flattened to \(\mathbb{R}^{1095}\).

**Approach geometry.** For each zone \(z\) with center \(c_z\), dog position \(p\) and velocity \(v\):

\[
d_z = \|c_z - p\|,\quad
\hat{u}_z = (c_z - p)/d_z,\quad
\dot{d}_z = v \cdot \hat{u}_z.
\]

Closing rate is a clamped \(\dot{d}_z\). Time-to-contact is \(\tau_z = d_z / \max(\dot{d}_z, \varepsilon)\), then inverted against a 60-frame horizon so that a large `tau_*` means imminent arrival. Heading is \(\hat{v} \cdot \hat{u}_z\). These quantities are camera-translation invariant; raw `bbox_cx` and `edge_*` are not.

**Vocal.** The audio encoder emits arousal, valence, bark probability, and four psychoacoustic descriptors (\(f_0\), harmonics-to-noise, first formant, burstiness). The collar’s bark flag is not allowed to overwrite vocal arousal or valence.

**Physiology from the puck.** The 1 Hz CBOR map is projected onto slots the triad already has:

| Collar key | Slot | Scale |
|------------|------|--------|
| `hr_bpm` | `ecg_hr_norm` | \(/180\), clamp \([0,1]\) |
| `rmssd_ms` | `ecg_rmssd_norm` | \(/150\), clamp \([0,1]\) |
| `arousal` | `ecg_stress` | clamp \([0,1]\) |
| `imu_rms` | `imu_activity` | clamp \([0,1]\) |
| `still` | `imu_posture_static` | \(\{0,1\}\) |

Laptop path: `python3 scripts/collar_listen.py --runtime http://HOST:8000` posts each notify to `POST /infer/collar`. The hub also reads `artifacts/eval/collar_latest.json` when the file is younger than three seconds.

**Synchrony.** Phase-locking value between two instantaneous-phase series, a lagged correlation, and a random-walk Kalman filter into latent arousal and valence (`core/synchrony.py`). These are cheap fusion features, not a claim that tail and voice are locked in the field.

## 7. Models

**Shipped TriadNet.** A two-layer multilayer perceptron (hidden 128, dropout 0.15) over the flattened window, with three linear heads [11]. Confidence is the mean of the three selected softmax masses. Margin is the mean top-1 minus top-2 gap across heads; a small margin is treated as review even when confidence is high.

**Temporal variant.** `TriadNetTemporal` is a bidirectional long short-term memory encoder with Bahdanau attention and extra arousal/valence regression heads (`services/forecast/app/temporal_math.py`). It is separately trainable. Promoting it would break the shipped `triad.pt` layout, so it is not the default.

**Vocal and vitals encoders.** Small in-repo networks in `services/audio` and `lib/aarf-physio`. Vision uses YOLOv8n plus a Stanford Dogs breed head.

**Heuristic fallback.** If no checkpoint loads, gaze zones and motion pick a triple (door + motion \(\rightarrow\) outside / anxious / freeze, and so on). That fallback is a bring-up aid, not a reported model.

Training:

```bash
./scripts/train_aarflingo.sh
```

`python3 scripts/verify_artifacts.py` checks that a checkpoint loads. It is not the v1.0 bar.

## 8. Wearable hardware

Rev-A board: 40 mm × 32 mm. Microcontroller ESP32-S3-MINI-1. Inertial measurement unit Bosch BMI270 on I2C (`0x68`). Microphone INMP441 on I2S. Neck photoplethysmography Texas Instruments AFE4404 (`0x58`) with infrared and 660 nm emitters and a photodiode. Contact temperature is a 10 kΩ β3950 thermistor on ADC1 GPIO10. Battery sense is ADC1 GPIO1. Charge default is 100 mA (`R1 = 10 kΩ`). Identity is a passive NFC tag in the enclosure, not a PCB net.

Firmware 0.3.0 advertises `aarf-collar`, requests MTU 247, and notifies a 23-key CBOR map at 1 Hz (`source`, `v`, `ts_ms`, inertial and audio RMS, bark, battery, heart rate, RMSSD, perfusion, still / shake / pant, pitch, respiratory rate, arousal, gyro RMS, die temperature, skin temperature, red perfusion). The serialized map must fit in negotiated MTU minus three bytes. On bark, optional Wi-Fi CLIP posts the existing studio JSON to `POST /infer/audio`.

Schematic and GPIO live in `scripts/aarf_sch/nets.py` and `hardware/collar-reva/`. Signals on the printed circuit board are not yet routed; the board is not fab-ready. The enclosure is not designed.

## 9. Evaluation protocol

The only number that can satisfy v1.0 is **dog-held-out intent accuracy** on a home set:

- at least three dogs;
- split by `dog_id`, never by random frame;
- labels from `ethogram/`;
- rows in `data/dog/eval/dog_split.jsonl`;
- scored by `python3 scripts/v1_gate.py --require-bar`.

A row is `{"dog_id","y_true","y_pred","ts_ms"}` with an optional `"collar"` object. Camera-only rows are valid. Target: accuracy \(\ge 0.95\) and macro-F1 reported beside it. Calibration (expected calibration error) and coupling-corrected accuracy are required before a venue submission; they are not in the gate yet.

What does not count: synthetic triad or vitals `best_val_acc`, mixed vocal accuracy, Stanford Dogs breed top-1, and collar proxies used as intent labels.

Inter-rater Cohen’s \(\kappa\) on behavior is specified at \(\ge 0.75\) and is not yet logged.

## 10. Results

Table 1 is copied from `docs/paper/RESULTS.md` after `python3 scripts/v1_gate.py` on 21 August 2026. That file is generated. Do not treat a hand edit of this section as the score.

| Metric | Value | Split | Counts toward v1.0? |
|--------|------:|-------|---------------------|
| Home dog-split accuracy | — | dog-held-out | yes |
| Home dog-split macro-F1 | — | dog-held-out | yes |
| Home dogs / rows | 0 / 0 | dog-held-out | yes |
| Home rows with collar CBOR | 0 | dog-held-out | no |
| Rev-A puck contract | ok | hardware | yes |
| Triad `best_val_acc` | 1.0 | synthetic (\(n_\mathrm{val}=40\)) | no |
| Vocal `best_val_acc` (manifest mixed) | 0.183 | mixed | no |
| Vocal real held-out | 0.345 | Barkopedia clips | no |
| Vocal synthetic held-out | 0.809 | synthetic | no |
| Vitals `best_val_acc` | 1.0 | synthetic (\(n_\mathrm{val}=80\)) | no |
| Breed top-1 | 0.746 | Stanford Dogs | no |
| Jetson hub image | ok | L4T, not wearable | yes |
| Paper protocol files | ok | this directory | yes |

**bar_met:** false.

Blocker: write `data/dog/eval/dog_split.jsonl` with a dog-held-out eval on at least three dogs at \(\ge 95\%\).

Context, not the bar: the vocal encoder beats chance on 298 real clips (about \(3.1\times\) a uniform 10-way prior if one pretends the label set is that large; the actual Barkopedia label cardinality is the emotion set used in that trainer). The breed head is a public-photo number. The triad checkpoint memorizes its synthetic draw. None of those sentences is a home-dog result.

## 11. Limitations

The home set does not exist yet. Until it does, this is a methods paper with public-corpus side numbers.

Several named visual features (DogFACS-style units, Lyapunov wag, gait phase) are estimated from a 2D box and a lightweight pose, not from a motion-capture lab. When the dog leaves frame they are zero, and the model must not treat zero as “calm.”

The collar heart-rate and RMSSD estimators assume a still neck and a seated photodiode. Motion, fur, and melanin will corrupt peaks. Gyro RMS is not a behavior classifier. Package temperature is not skin; skin is not core.

`TriadNetTemporal`, PhysioZoo-trained `vitals.pt`, and a routed, fab-ready board are unfinished. The 95% target may be too high for dog-held-out intent with \(N=3\); the gate will say so if the labeled file exists and falls short.

## 12. Reproducibility

From a clone, without a GPU:

```bash
python3 -m pytest -q core/tests/test_v1_gate.py core/tests/test_collar_features.py
python3 scripts/v1_gate.py
python3 scripts/v1_gate.py --require-bar   # exits 1 until the bar is real
```

Train and load-check:

```bash
./scripts/train_aarflingo.sh
python3 scripts/verify_artifacts.py
```

Hub and puck:

```bash
PYTHONPATH=.:services/edge-runtime python3 -m app.cli status
./scripts/flash_collar.sh
python3 scripts/collar_listen.py --runtime http://127.0.0.1:8000
```

LaTeX source for this manuscript is `docs/paper/aarflingo.tex`. Dataset notes are in `docs/DATASETS.md`. Hardware contract: `./kicad-launcher --sch verify`.

## 13. Conclusion

AARFLingo is an observational triad forecaster with a room camera, a vocal encoder, and a notify-only neck puck, scored by a dog-held-out gate that synthetic accuracy cannot pass. The software and the Rev-A contract are in this repository. The home-dog measurement is not. That is the next experiment, not a number we will invent.

## Acknowledgements

Public corpora: Stanford Dogs, Barkopedia / EmotionalCanines, DogSpeak, AudioSet (whimper), PhysioZoo, Mendeley inertial sets. No animal was stimulated by this system.

## References

1. A. Khosla, N. Jayadevaprakash, B. Yao, and L. Fei-Fei, “Novel dataset for Fine-Grained Image Categorization,” FGVC Workshop, CVPR, 2011. [Stanford Dogs](http://vision.stanford.edu/aditya86/ImageNetDogs/).
2. G. Jocher, A. Chaurasia, and J. Qiu, *Ultralytics YOLOv8*, 2023. https://github.com/ultralytics/ultralytics
3. Arlington Computational Linguistics, *Barkopedia: Dog Emotion Classification*, Hugging Face dataset `ArlingtonCL2/BarkopediaDogEmotionClassification_Data`.
4. Arlington Computational Linguistics, *DogSpeak*, Hugging Face dataset `ArlingtonCL2/DogSpeak_Dataset`.
5. J. Behar et al., *PhysioZoo*, PhysioNet, https://physionet.org/content/physiozoo/1.0.0/
6. Mendeley, canine posture and behavior inertial datasets, https://data.mendeley.com/datasets/mpph6bmn7g/1 and https://data.mendeley.com/datasets/vxhx934tbn/3
7. A. Quaranta, M. Siniscalchi, and G. Vallortigara, “Asymmetric tail-wagging responses by dogs to different emotive stimuli,” *Current Biology*, 17(6), R199–R201, 2007.
8. W. Ren, P. Wei, S. Yu, and Y. Q. Zhang, “Left-right asymmetry and attractor-like dynamics of dog’s tail wagging during dog-human interactions,” *iScience*, 25(8), 104747, 2022.
9. C. C. Caeiro, A. M. Burrows, and B. M. Waller, “Development and application of CatFACS: Are human cat adopters influenced by cat facial expressions?” and the DogFACS manual (Waller, Caeiro, et al.) for canine facial action units.
10. D. N. Lee, “A theory of visual control of braking based on information about time-to-collision,” *Perception*, 5(4), 437–459, 1976.
11. Implementation: `services/forecast/app/triad_model.py`, `core/feature_spec.py`, `core/v1_gate.py`, `firmware/collar`.
