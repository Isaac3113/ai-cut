"""Local person-mask preprocessing, tied to source seconds, not an edit timeline.

SPDX-License-Identifier: MIT
MediaPipe and the separately downloaded Google model retain Apache-2.0 licenses.
"""
from __future__ import annotations

import argparse
import hashlib
import importlib.metadata
import json
import math
from pathlib import Path
import subprocess
import sys
import time

import mediapipe as mp
from mediapipe.tasks import python
from mediapipe.tasks.python import vision
import numpy as np
from PIL import Image, ImageFilter


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            h.update(block)
    return h.hexdigest()


def run_json(command: list[str]) -> dict:
    return json.loads(subprocess.check_output(command, text=True, encoding="utf-8"))


def probe(path: Path, ffprobe: Path) -> dict:
    return run_json([str(ffprobe), "-v", "error", "-show_streams", "-show_format", "-of", "json", str(path)])


def read_exact(stream, length: int) -> bytes:
    data = bytearray()
    while len(data) < length:
        part = stream.read(length - len(data))
        if not part:
            break
        data.extend(part)
    return bytes(data)


def person_probability(segmenter, result) -> np.ndarray:
    masks = result.confidence_masks
    if not masks:
        raise RuntimeError("MediaPipe did not return confidence masks.")
    labels = [str(label).lower() for label in segmenter.labels]
    if len(masks) > 2 and "background" in labels:
        values = 1.0 - masks[labels.index("background")].numpy_view().copy().squeeze()
        if values.ndim != 2 or not np.isfinite(values).all():
            raise RuntimeError("Invalid multiclass background confidence image.")
        return np.clip(values, 0.0, 1.0)
    if len(masks) == 1:
        index = 0  # Google's binary Selfie Segmenter returns foreground confidence.
    elif "person" in labels:
        index = labels.index("person")
    elif "selfie" in labels:
        index = labels.index("selfie")
    else:
        raise RuntimeError(f"Cannot identify the person mask: labels={labels}, masks={len(masks)}")
    values = masks[index].numpy_view().copy().squeeze()
    if values.ndim != 2 or not np.isfinite(values).all():
        raise RuntimeError("Invalid segmentation confidence image.")
    return np.clip(values, 0.0, 1.0)


def prepare_mask(probability: np.ndarray, width: int, height: int, low: float, high: float, blur: float, erode: int = 0, largest_component: bool = False) -> Image.Image:
    values = np.clip((probability - low) / (high - low), 0.0, 1.0)
    mask = Image.fromarray(np.round(values * 255).astype(np.uint8))
    if mask.size != (width, height):
        mask = mask.resize((width, height), Image.Resampling.BILINEAR)
    if largest_component:
        import cv2
        array = np.asarray(mask)
        count, components, stats, _ = cv2.connectedComponentsWithStats((array >= 128).astype(np.uint8), connectivity=8)
        if count > 1:
            largest = 1 + int(np.argmax(stats[1:, cv2.CC_STAT_AREA]))
            support = Image.fromarray(np.where(components == largest, 255, 0).astype(np.uint8)).filter(ImageFilter.MaxFilter(5))
            mask = Image.fromarray(np.minimum(array, np.asarray(support)))
    if erode:
        mask = mask.filter(ImageFilter.MinFilter(erode * 2 + 1))
    return mask.filter(ImageFilter.GaussianBlur(blur)) if blur else mask


def new_output(path: Path) -> Path:
    if path.exists():
        raise FileExistsError(f"Refusing an existing output directory: {path}")
    path.mkdir(parents=True, exist_ok=False)
    return path


def extract_rgb(args, source_seconds: float) -> np.ndarray:
    command = [str(args.ffmpeg), "-hide_banner", "-loglevel", "error", "-ss", f"{source_seconds:.9f}", "-i", str(args.source),
               "-frames:v", "1", "-an", "-vf", f"scale={args.width}:{args.height}:flags=lanczos", "-f", "rawvideo", "-pix_fmt", "rgb24", "pipe:1"]
    raw = subprocess.check_output(command)
    if len(raw) != args.width * args.height * 3:
        raise RuntimeError(f"Expected one decoded RGB frame at source second {source_seconds}.")
    return np.frombuffer(raw, dtype=np.uint8).reshape(args.height, args.width, 3).copy()


def make_segmenter(args, video: bool):
    return vision.ImageSegmenter.create_from_options(vision.ImageSegmenterOptions(
        base_options=python.BaseOptions(model_asset_path=str(args.model)),
        running_mode=vision.RunningMode.VIDEO if video else vision.RunningMode.IMAGE,
        output_confidence_masks=True,
        output_category_mask=False,
    ))


def sample_frames(args, output: Path) -> dict:
    records = []
    with make_segmenter(args, video=False) as segmenter:
        labels = list(segmenter.labels)
        for seconds in args.samples:
            rgb = extract_rgb(args, seconds)
            result = segmenter.segment(mp.Image(image_format=mp.ImageFormat.SRGB, data=rgb))
            probability = person_probability(segmenter, result)
            mask = prepare_mask(probability, args.width, args.height, args.low, args.high, args.blur, args.erode, args.largest_component)
            stem = f"source-{seconds:g}s"
            original = Image.fromarray(rgb)
            original.save(output / f"{stem}-original.png")
            mask.save(output / f"{stem}-mask.png")
            background = Image.new("RGB", original.size, (58, 52, 105))
            Image.composite(original, background, mask).save(output / f"{stem}-composite.png")
            records.append({"source_seconds": seconds, "requested_timestamp_ms": round(seconds * 1000),
                            "mask_mean": float(np.asarray(mask).mean() / 255), "confidence_masks": len(result.confidence_masks),
                            "original": f"{stem}-original.png", "mask": f"{stem}-mask.png", "composite": f"{stem}-composite.png"})
    return {"mode": "samples", "labels": labels, "samples": records,
            "sample_seek_policy": "FFmpeg accurate source-second seek; first decoded frame at the requested seek position, not a source frame-number assumption."}


def mask_video(args, output: Path) -> dict:
    count = math.ceil(args.duration * args.fps - 1e-9)
    decode = [str(args.ffmpeg), "-hide_banner", "-loglevel", "error", "-ss", f"{args.start:.9f}", "-i", str(args.source), "-an",
              "-vf", f"fps={args.fps}:start_time=0:round=near,scale={args.width}:{args.height}:flags=lanczos", "-frames:v", str(count),
              "-f", "rawvideo", "-pix_fmt", "rgb24", "pipe:1"]
    target = output / "person-mask.mp4"
    encode = [str(args.ffmpeg), "-hide_banner", "-loglevel", "error", "-n", "-f", "rawvideo", "-pix_fmt", "gray", "-s", f"{args.width}x{args.height}",
              "-r", str(args.fps), "-i", "pipe:0", "-an", "-c:v", "libx264", "-preset", "fast", "-qp", "0", "-pix_fmt", "yuv420p",
              "-color_range", "pc", "-movflags", "+faststart", str(target)]
    byte_count = args.width * args.height * 3
    held_tail = 0
    clock = time.perf_counter()
    with (output / "decode.log").open("wb") as decoder_log, (output / "encode.log").open("wb") as encoder_log:
        decoder = subprocess.Popen(decode, stdout=subprocess.PIPE, stderr=decoder_log)
        encoder = subprocess.Popen(encode, stdin=subprocess.PIPE, stderr=encoder_log)
        try:
            with make_segmenter(args, video=True) as segmenter:
                labels = list(segmenter.labels)
                last_rgb = None
                for index in range(count):
                    raw = read_exact(decoder.stdout, byte_count)
                    if len(raw) == 0 and index == count - 1 and last_rgb is not None:
                        # The final requested sample is still inside the source; CFR may round off one tail frame.
                        rgb = last_rgb
                        held_tail += 1
                    elif len(raw) != byte_count:
                        raise RuntimeError(f"Source decode ended early at output sample {index}/{count}.")
                    else:
                        rgb = np.frombuffer(raw, dtype=np.uint8).reshape(args.height, args.width, 3).copy()
                    last_rgb = rgb
                    timestamp_ms = round((args.start + index / args.fps) * 1000)
                    result = segmenter.segment_for_video(mp.Image(image_format=mp.ImageFormat.SRGB, data=rgb), timestamp_ms)
                    mask = prepare_mask(person_probability(segmenter, result), args.width, args.height, args.low, args.high, args.blur, args.erode, args.largest_component)
                    encoder.stdin.write(mask.tobytes())
                    if index % 150 == 0 or index == count - 1:
                        print(json.dumps({"frame": index + 1, "frames": count, "source_seconds": args.start + index / args.fps,
                                          "elapsed_seconds": round(time.perf_counter() - clock, 2)}), flush=True)
            encoder.stdin.close()
            decoder.stdout.close()
            decode_result, encode_result = decoder.wait(), encoder.wait()
            if decode_result or encode_result:
                raise RuntimeError(f"FFmpeg failure: decode={decode_result}, encode={encode_result}")
        finally:
            for process in (decoder, encoder):
                if process.poll() is None:
                    process.terminate()
                    process.wait()
    elapsed = time.perf_counter() - clock
    verification = probe(target, args.ffprobe)
    # A full independent decode catches truncated H264 rather than trusting process exit alone.
    subprocess.run([str(args.ffmpeg), "-hide_banner", "-loglevel", "error", "-i", str(target), "-f", "null", "-"], check=True)
    return {"mode": "video", "labels": labels, "source_start_seconds": args.start, "requested_duration_seconds": args.duration,
            "fps": args.fps, "frame_count": count, "last_sample_source_seconds": args.start + (count - 1) / args.fps,
            "encoded_duration_seconds": count / args.fps, "held_tail_frames": held_tail,
            "timestamp_formula": "round((source_start_seconds + output_sample_index / fps) * 1000)",
            "resampling": "FFmpeg CFR fps filter, nearest timestamp rounding; no semantic cuts, speed changes, crop or audio.",
            "output": target.name, "output_sha256": sha256(target), "elapsed_seconds": elapsed, "processing_fps": count / elapsed,
            "full_decode": "passed", "probe": verification,
            "mask_format": "Opaque grayscale H264 MP4, white=person, black=background; this file has no alpha channel."}


def main() -> None:
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source", type=Path, required=True)
    parser.add_argument("--model", type=Path, required=True)
    parser.add_argument("--ffmpeg", type=Path, required=True)
    parser.add_argument("--ffprobe", type=Path, required=True)
    parser.add_argument("--out-dir", type=Path, required=True)
    parser.add_argument("--mode", choices=("samples", "video"), required=True)
    parser.add_argument("--width", type=int, default=540)
    parser.add_argument("--height", type=int, default=960)
    parser.add_argument("--fps", type=int, default=30)
    parser.add_argument("--start", type=float, default=0)
    parser.add_argument("--duration", type=float, default=47.77)
    parser.add_argument("--samples", type=lambda value: [float(part) for part in value.split(",")], default=[3, 15, 30, 43])
    parser.add_argument("--low", type=float, default=0.2)
    parser.add_argument("--high", type=float, default=0.8)
    parser.add_argument("--blur", type=float, default=0.65)
    parser.add_argument("--erode", type=int, default=0, help="Conservative output-pixel erosion; must be inspected for lost hair/fingers.")
    parser.add_argument("--largest-component", action="store_true", help="Drop isolated components; intended only for a single prominent speaker.")
    args = parser.parse_args()
    for name in ("source", "model", "ffmpeg", "ffprobe"):
        path = getattr(args, name).resolve(strict=True)
        if not path.is_file():
            raise ValueError(f"{name} must be a file.")
        setattr(args, name, path)
    if min(args.width, args.height, args.fps) <= 0 or args.width % 2 or args.height % 2 or args.fps > 120:
        raise ValueError("Use positive even dimensions and 1-120 fps.")
    if not (0 <= args.low < args.high <= 1) or args.blur < 0 or args.start < 0 or args.duration <= 0 or not (0 <= args.erode <= 10):
        raise ValueError("Invalid probability, blur or source-time range.")
    source_probe = probe(args.source, args.ffprobe)
    video = next(stream for stream in source_probe["streams"] if stream["codec_type"] == "video")
    if abs(video["width"] / video["height"] - args.width / args.height) > 0.002:
        raise ValueError("Refusing aspect-ratio changes in mask preprocessing.")
    duration = float(source_probe["format"]["duration"])
    if args.mode == "video" and args.start + args.duration > duration + 0.001:
        raise ValueError("Requested source range extends beyond the source video.")
    if args.mode == "samples" and any(not (0 <= seconds < duration) for seconds in args.samples):
        raise ValueError("A sample timestamp is outside the source duration.")
    output = new_output(args.out_dir.resolve())
    record = {"schema_version": 1, "source": str(args.source), "source_sha256": sha256(args.source),
              "model": str(args.model), "model_sha256": sha256(args.model), "script_sha256": sha256(Path(__file__)),
              "mediapipe_version": importlib.metadata.version("mediapipe"), "source_probe": source_probe,
              "width": args.width, "height": args.height, "probability_remap": {"low": args.low, "high": args.high, "gaussian_blur_output_pixels": args.blur, "erosion_output_pixels": args.erode, "keep_largest_component": args.largest_component},
              "privacy": "All inference and media decoding are local. This script has no upload or model-download path.",
              "limitations": ["Semantic person segmentation, not pixel-perfect hair matting.", "No proof of temporal edge stability or full human review from a successful render.", "No source audio or editing timeline is changed."]}
    try:
        record.update(sample_frames(args, output) if args.mode == "samples" else mask_video(args, output))
        record["status"] = "complete"
    except Exception as error:
        record.update(status="failed", error=str(error))
        raise
    finally:
        (output / "mask-manifest.json").write_text(json.dumps(record, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"status": record["status"], "manifest": str(output / "mask-manifest.json")}, ensure_ascii=False), flush=True)


if __name__ == "__main__":
    main()
