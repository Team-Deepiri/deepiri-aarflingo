import type { CaptureMode } from "./platform";

export const INTENT_LABELS: Record<string, string> = {
  approach: "Approach",
  avoid: "Avoid",
  solicit_play: "Solicit play",
  rest: "Rest",
  guard_resource: "Guard resource",
  explore: "Explore",
  alert: "Alert",
  outside: "Wants outside",
  play: "Wants to play",
  food: "Wants food",
};

export const EMOTION_LABELS: Record<string, string> = {
  calm: "Calm",
  content: "Content",
  excited: "Excited",
  anxious: "Anxious",
  fearful: "Fearful",
  frustrated: "Frustrated",
  conflicted: "Conflicted",
};

export const BEHAVIOR_LABELS: Record<string, string> = {
  tail_wag_loose: "Loose tail wag",
  tail_tucked: "Tail tucked",
  play_bow: "Play bow",
  lip_lick: "Lip lick",
  whale_eye: "Whale eye",
  hard_stare: "Hard stare",
  yawning: "Yawning",
  sniff_ground: "Sniff ground",
  freeze: "Freeze",
  bark: "Bark",
};

export const SPEECH_WORDS: Record<string, string> = {
  outside: "outside",
  play: "play",
  food: "food",
  avoid: "help",
  rest: "rest",
};

// Feature order matches core/feature_spec.py BASE_FEATURE_NAMES + MODALITY_NAMES.
// Used to index the `sequence` array into the tokenization heatmap.
export const FEATURE_NAMES: string[] = [
  "dog_present",
  "bbox_cx",
  "bbox_cy",
  "bbox_w",
  "bbox_h",
  "motion",
  "velocity_x",
  "velocity_y",
  "gaze_door",
  "gaze_toy",
  "gaze_bowl",
  "gaze_center",
  "edge_left",
  "edge_right",
  "edge_top",
  "edge_bottom",
  "brightness",
  "contrast",
  "aspect_ratio",
  "arousal_proxy",
  "pose_head_y",
  "pose_head_gaze_x",
  "pose_body_stretch",
  "pose_play_bow",
  "n_dogs",
  "track_stability",
  "tau_door",
  "tau_toy",
  "tau_bowl",
  "closing_door",
  "closing_toy",
  "closing_bowl",
  "heading_door",
  "heading_toy",
  "heading_bowl",
  "vision_yolo_dog_conf",
  "audio_arousal",
  "audio_valence",
  "audio_bark_prob",
  "ecg_hr_norm",
  "ecg_stress",
  "imu_activity",
  "imu_posture_static",
];

export const MODALITY_DEFS: {
  key: string;
  label: string;
  group: "Vision" | "Audio" | "Heart" | "Body" | "Motion" | "Gaze";
  flip?: boolean;
}[] = [
  { key: "vision_yolo_dog_conf", label: "Dog detected", group: "Vision" },
  { key: "motion", label: "Motion", group: "Vision" },
  { key: "brightness", label: "Brightness", group: "Vision" },
  { key: "contrast", label: "Contrast", group: "Vision" },
  { key: "audio_arousal", label: "Arousal", group: "Audio" },
  { key: "audio_valence", label: "Valence", group: "Audio" },
  { key: "audio_bark_prob", label: "Bark probability", group: "Audio" },
  { key: "ecg_hr_norm", label: "Heart rate", group: "Heart" },
  { key: "ecg_stress", label: "Stress", group: "Heart" },
  { key: "imu_activity", label: "Activity", group: "Body" },
  { key: "imu_posture_static", label: "Posture (static)", group: "Body" },
  { key: "pose_play_bow", label: "Play bow", group: "Body" },
  { key: "pose_body_stretch", label: "Body stretch", group: "Body" },
  { key: "arousal_proxy", label: "Arousal proxy", group: "Motion" },
  { key: "velocity_x", label: "Velocity X", group: "Motion" },
  { key: "velocity_y", label: "Velocity Y", group: "Motion" },
  { key: "gaze_door", label: "Gaze → door", group: "Gaze" },
  { key: "gaze_toy", label: "Gaze → toy", group: "Gaze" },
  { key: "gaze_bowl", label: "Gaze → bowl", group: "Gaze" },
  { key: "gaze_center", label: "Gaze → center", group: "Gaze" },
  { key: "track_stability", label: "Track stability", group: "Motion" },
];

// Subset of features shown as rows in the tokenization heatmap (keeps it readable).
export const TOKEN_FEATURES: string[] = [
  "dog_present",
  "vision_yolo_dog_conf",
  "motion",
  "arousal_proxy",
  "velocity_x",
  "velocity_y",
  "gaze_door",
  "gaze_toy",
  "gaze_bowl",
  "pose_play_bow",
  "pose_body_stretch",
  "audio_arousal",
  "audio_valence",
  "audio_bark_prob",
  "ecg_hr_norm",
  "ecg_stress",
  "imu_activity",
  "track_stability",
];

export const MODE_LABELS: Record<CaptureMode, string> = {
  browser: "Browser cam",
  bridge: "Windows bridge",
  server: "Server OpenCV",
};

export const MODE_HINTS: Record<CaptureMode, string> = {
  browser: "Webcam through this browser — no bridge needed.",
  bridge: "MJPEG stream from the Windows host / bridge script.",
  server: "Runtime reads the camera directly with OpenCV.",
};

export const TRAIT_LABELS: Record<string, string> = {
  energy: "Energy",
  excitability: "Excitability",
  friendliness: "Friendliness",
  independence: "Independence",
  vocal_tendency: "Vocal tendency",
  guardiness: "Guardiness",
};

export function fmtConfidence(v: number): string {
  return `${Math.round((v ?? 0) * 100)}%`;
}
