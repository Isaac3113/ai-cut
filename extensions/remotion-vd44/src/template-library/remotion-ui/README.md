# RemotionUI selective adaptation

Source: https://github.com/riaz37/remotion-ui

Pinned commit: `0aecaca2b61a167992e1205d10e4da16d8a71331` (2026-10-23).
Original MIT license: `upstream/LICENSE`. Exact upstream bytes are preserved as
`.tsx.txt` files so unresolved website import aliases do not enter this project's
TypeScript build. The manifest records SHA-256 checksums and modifications.

No new package, installer, network font or model is required by these two local
components. The existing React 19.2.3 and Remotion 4.0.523 runtime is reused;
Remotion's separate engine license still applies. Demonstration vector artwork
and gradient are original, contain no likeness or private footage, and use system
Arial. Do not treat them as a completed video or a test of real person matting.

## Exports and usage

- `OrbitMotion`: children, center, radiusX/Y, periodInFrames, phase, tilt,
  direction, centerX/Y (percent), depth, depthFade, upright, showPath, pathColor,
  style and className. Frame-driven ordering retains upstream's centre z-index
  10, back elements 1 and front elements 20. Supply an authorised transparent
  person layer as center to test actual person occlusion. A rectangular uncut
  video will occlude with its rectangle, not its person's silhouette.
- `TextMaskVideo`: text, src, media (`video`, `image`, `gradient`), gradient,
  width/height, fontSize/family/weight, letterSpacing, lineHeight, reveal,
  drift, zoom, startFrom, mediaFilter, enterInFrames, delayInFrames, exit,
  exitInFrames, exitAtInFrames, style and className. Input video is muted;
  voice/BGM/SFX stay with the authoritative editing timeline. A missing source
  for explicit video/image media is an error, not a pretend video preview.
- `OrbitMotionDemo`: register at 1080x1080, 30fps, 180 frames.
- `TextMaskVideoDemo`: register at 1080x1080, 30fps, 120 frames.

Both demo wrappers also accept JSON-safe CLI props, with optional fields and
defaults that preserve their original demo appearance. Import the wrappers,
`OrbitMotionDemoProps`, `TextMaskVideoDemoProps`, `orbitMotionDemoDefaults` and
`textMaskVideoDemoDefaults` directly from `./Demos`. The defaults objects can be
passed to Composition `defaultProps`; this adaptation does not edit Root.

- Orbit wrapper props: `labels` (non-empty string array), `title`, `note`,
  `periodInFrames`.
- Text-mask wrapper props: `text`, `title`, `note`, `media`, `src`, `gradient`,
  `fontFamily`. Choose `media: "video"` or `"image"` explicitly and provide
  `src` as a public-relative asset or already resolved media URL. Windows
  filesystem paths are rejected; copy/import the authorised asset through the
  selected project workflow. Video/image without a source is an error, and
  unsupported media names are rejected rather than falling back to a gradient.
- The default gradient note changes to a neutral media-source note when media
  is changed, unless a custom note is provided. Changing media is not itself a
  claim that decode/render verification passed.

Example JSON CLI props:

```json
{"labels":["PLAN","FILM","REUSE"],"title":"A reusable orbit","note":"VECTOR DEMO","periodInFrames":120}
```

```json
{"text":"CREATE\nMORE","title":"Video through type","media":"video","src":"authorised-demo.mp4","fontFamily":"Arial, sans-serif","note":"VIDEO SOURCE / MASKED TYPE DEMO"}
```

No Composition is registered by these files. Import the exports into the parent
library's chosen entry point; preserve the existing default project Root.
The demos scale their layout but other aspect ratios still need visual review.

## Differences from upstream

OrbitMotion retains upstream orbit mathematics and geometry. It adds explicit
finite/range checks, imports the FC type directly and explains the alpha-mask
requirement. Its mathematical period is still tied to output frames, not wall
clock time.

TextMaskVideo retains the SVG text clip, nested wipe, media branches, muted
OffthreadVideo and bounded sinusoidal pan/zoom. Website-specific layout and
motion-helper imports are removed. Font scaling is local (`size * width / 1080`).
The small explicit frame contract uses `enterInFrames` rather than upstream's
`durationInFrames`, has no spring/exitTravel/exitDirection options, and requires
non-overlapping entrance/exit windows inside its surrounding Sequence. Upstream
helper timing is not claimed to be identical. A video start frame can be set;
the component does not change playback speed or source/frame mapping.

## Verification status

New source added without executing an upstream installer. Parent task runs the
existing project typecheck and renders both examples. Their renders can verify
frame timing, clipping, overlap and the gradient branch only. Real video decode,
Chinese local fonts, person alpha edges/temporal stability and integration into
the final ChatCut timeline each require their own checks with actual authorised
assets. Do not infer those checks from a synthetic demo.
