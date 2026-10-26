# Local person-mask preprocessing

This isolated extension uses Google MediaPipe Tasks ImageSegmenter 1.1.1 and the
official Selfie Segmenter float16 v1 / Selfie Multiclass 256 float32 v1. Python packages live in
`.runtime/segmentation-venv`, and model/card/license downloads in
`.runtime/models/mediapipe-selfie-segmenter-float16-v1`. The main `.venv` is untouched.
The multiclass model is separately stored in
`.runtime/models/mediapipe-selfie-multiclass-256-float32-v1`.
Neither models, private media, masks nor outputs belong in Git.

The model card explicitly identifies Apache License 2.0. The model is intended
for prominent humans and real-time segmentation; fine hair/fingers, motion blur,
dark regions and occluders can fail. This is not a promise of pixel-perfect alpha.

- Package: https://pypi.org/project/mediapipe/1.1.1/
- API: https://developers.google.com/edge/mediapipe/solutions/vision/image_segmenter/python
- Model: https://storage.googleapis.com/mediapipe-models/image_segmenter/selfie_segmenter/float16/1/selfie_segmenter.tflite
- Model card: https://storage.googleapis.com/mediapipe-assets/Model%20Card%20MediaPipe%20Selfie%20Segmentation.pdf
- Runtime license: https://github.com/google-ai-edge/mediapipe/blob/master/LICENSE
- Multiclass model: https://storage.googleapis.com/mediapipe-models/image_segmenter/selfie_multiclass_256x256/float32/1/selfie_multiclass_256x256.tflite
- Multiclass card: https://storage.googleapis.com/mediapipe-assets/Model%20Card%20Multiclass%20Segmentation.pdf

Both model cards explicitly state Apache-2.0. The multiclass foreground is
`1 - background confidence`, retaining hair, body/face skin, clothes and
accessories. It is not just the face or hair channel. Versions, download hashes,
license evidence and the complete installed package set are recorded in
`source-manifest.json` and `requirements.lock.txt`. Package wheels were obtained
from official PyPI with binary-only installation into the isolated environment;
no upstream setup scripts or new cloud inference service were introduced.

## Workflow

Use the isolated Python with `segment_video.py --mode samples` first. Inspect the
original/mask/coloured-background composite for each source timestamp. Only after
acceptable samples, run `--mode video` to generate a silent opaque grayscale MP4:
white is person confidence, black is background. This is a luminance mask, not an
alpha-bearing video and not a finished edit. The processor has no upload path.

Required flags are `--source`, `--model`, `--ffmpeg`, `--ffprobe`, `--out-dir`,
`--mode`. Defaults: 540x960, 30fps, source start 0, duration 47.77 seconds,
samples 3/15/30/43 seconds, probability remap 0.2 to 0.8, Gaussian blur 0.65 output
pixels. New aspect ratios must match the source; preprocessing refuses stretching.
The output directory must not already exist, including partial earlier runs.
Optional `--largest-component` keeps the main connected foreground for a single
speaker; `--erode N` removes N output-edge pixels before blur. These are explicit,
source-dependent choices and can remove hair/fingers. They do not repair model
mistakes. The selected multiclass run uses neither option.

All inference timestamps derive from source seconds. Video decoding converts VFR
to 30fps with FFmpeg nearest timestamp rounding. Sample i is tied to
`source_start + i / fps`, and its MediaPipe timestamp is that value in milliseconds.
There are no semantic cuts or speed changes. If CFR rounding omits only the final
requested sample, the last decoded frame may be held once and is recorded.
The final mask frame occupies one full encoded frame, so the MP4 may be slightly
longer than the requested source span; the manifest records both durations.

The authoritative ChatCut timeline must map source seconds to final clip frames.
Trim/resample this mask with exactly the same mapping as its source image. Never
apply a second independent 1.2x transform or use source-frame arithmetic for VFR.
Compositing can upscale the luminance mask with bilinear interpolation; it cannot
recover fine features already lost at the model's 256x256 input resolution.

Each run writes source/model/script SHA-256, settings, true source probe, exact
timestamp formula, output probe and performance in `mask-manifest.json`. Full-video
mode also independently decodes the encoded MP4. Successful decoding does not
prove quality, temporal stability or a human full-watch approval.

## Initial real-footage comparison

Four source-time samples (3, 15, 30 and 43 seconds) were actually viewed against
a purple background. The tiny binary model retained visible bright curtain
patches near the neck/shoulders, including after stricter thresholds and erosion.
The multiclass model reduced the larger curtain patches and preserved the main
head/torso silhouette better, so it was selected for the full-source mask.
Fast blurred arms at the 3-second sample and a lower wrist at 15 seconds still
have missing portions. A short graphic paper-cut outline can tolerate coarse
edges; a clean long background replacement or pixel-perfect hair is unverified.
Do not treat this assessment as approval of every frame or the final edit.
