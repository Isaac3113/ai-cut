"""Export final timeline caption cards as SRT and plain text without rewriting speech.

Input is a JSON array of {id, start_frame, end_frame, text}; ranges are end-exclusive.
No ASR, semantic edits, speed conversion, or rendering are performed by this helper.
"""
from __future__ import annotations

import argparse
from fractions import Fraction
import hashlib
import json
from pathlib import Path


def frame_milliseconds(frame: int, fps: Fraction) -> int:
    """Round absolute frame boundaries to nearest millisecond, ties upward."""
    value = Fraction(frame * 1000, 1) / fps
    return (2 * value.numerator + value.denominator) // (2 * value.denominator)


def timestamp(milliseconds: int) -> str:
    hours, remainder = divmod(milliseconds, 3_600_000)
    minutes, remainder = divmod(remainder, 60_000)
    seconds, milliseconds = divmod(remainder, 1000)
    return f"{hours:02d}:{minutes:02d}:{seconds:02d},{milliseconds:03d}"


def prepare(cards, fps, *, offset_frames=0, duration_frames=None, paragraphs=None):
    """Return SRT, TXT, normalized cards, and rational fps after full validation.

    Optional paragraphs is a chronological partition: [[card_id, ...], ...].
    It changes whitespace only. Without it each card becomes one plain text line.
    Offset is explicit and applied once; input otherwise already uses final frames.
    """
    try:
        rate = Fraction(str(fps))
    except (ValueError, ZeroDivisionError) as exc:
        raise ValueError("fps must be a positive number or rational such as 30000/1001") from exc
    if rate <= 0:
        raise ValueError("fps must be positive")
    if type(offset_frames) is not int or offset_frames < 0:
        raise ValueError("offset_frames must be a nonnegative integer")
    if duration_frames is not None and (type(duration_frames) is not int or duration_frames <= 0):
        raise ValueError("duration_frames must be a positive integer")
    if not isinstance(cards, list) or not cards:
        raise ValueError("cards must be a nonempty JSON array")

    normalized, identifiers, prior_end = [], [], 0
    for index, card in enumerate(cards):
        if not isinstance(card, dict) or not {"id", "start_frame", "end_frame", "text"} <= card.keys():
            raise ValueError(f"card {index}: id/start_frame/end_frame/text are required")
        identifier = card["id"]
        if type(identifier) not in (str, int) or (isinstance(identifier, str) and not identifier.strip()):
            raise ValueError(f"card {index}: invalid id")
        if identifier in identifiers:
            raise ValueError(f"card {index}: duplicate id")
        start, end = card["start_frame"], card["end_frame"]
        if type(start) is not int or type(end) is not int or start < 0 or end <= start:
            raise ValueError(f"card {index}: frames must be integers with 0 <= start < end")
        if index and start < prior_end:
            raise ValueError(f"card {index}: overlapping or out-of-order cards")
        prior_end = end
        text = card["text"]
        if not isinstance(text, str) or not text.strip():
            raise ValueError(f"card {index}: text must contain spoken content")
        text = text.replace("\r\n", "\n").replace("\r", "\n").strip()
        if any(not line.strip() for line in text.split("\n")):
            raise ValueError(f"card {index}: blank lines would split an SRT cue")
        start, end = start + offset_frames, end + offset_frames
        if duration_frames is not None and end > duration_frames:
            raise ValueError(f"card {index}: extends beyond final video duration")
        start_ms, end_ms = frame_milliseconds(start, rate), frame_milliseconds(end, rate)
        if end_ms <= start_ms:
            raise ValueError(f"card {index}: duration collapses at SRT millisecond precision")
        identifiers.append(identifier)
        normalized.append({"id": identifier, "start_frame": start, "end_frame": end,
                           "start_ms": start_ms, "end_ms": end_ms, "text": text})

    groups = [[identifier] for identifier in identifiers]
    if paragraphs is not None:
        if not isinstance(paragraphs, list) or not paragraphs or any(not isinstance(g, list) or not g for g in paragraphs):
            raise ValueError("paragraphs must be nonempty lists of consecutive card ids")
        if [identifier for group in paragraphs for identifier in group] != identifiers:
            raise ValueError("paragraphs must include every id exactly once in original order")
        groups = paragraphs
    texts = {card["id"]: " ".join(card["text"].splitlines()) for card in normalized}
    separator = "\n\n" if paragraphs is not None else "\n"
    plain = separator.join(" ".join(texts[identifier] for identifier in group) for group in groups) + "\n"
    srt = "\n\n".join(
        f"{number}\n{timestamp(card['start_ms'])} --> {timestamp(card['end_ms'])}\n{card['text']}"
        for number, card in enumerate(normalized, 1)
    ) + "\n"
    return srt, plain, normalized, rate


def export(cards_path: Path, output_stem: Path, fps, *, offset_frames=0,
           duration_frames=None, paragraphs_path: Path | None = None):
    """Validate first, preserve existing outputs, and write byte/hash provenance."""
    cards_path, output_stem = Path(cards_path).resolve(), Path(output_stem).resolve()
    raw = cards_path.read_bytes()
    cards = json.loads(raw.decode("utf-8-sig"))
    paragraphs = None
    if paragraphs_path is not None:
        paragraphs_path = Path(paragraphs_path).resolve()
        paragraphs = json.loads(paragraphs_path.read_text(encoding="utf-8-sig"))
    srt, plain, normalized, rate = prepare(
        cards, fps, offset_frames=offset_frames, duration_frames=duration_frames, paragraphs=paragraphs)
    paths = {kind: Path(str(output_stem) + suffix) for kind, suffix in
             (("srt", ".srt"), ("txt", ".txt"), ("manifest", ".subtitles.json"))}
    if any(path.exists() for path in paths.values()):
        raise FileExistsError("Output exists; choose a new output stem. Historical files are preserved.")
    data = {"srt": srt.encode("utf-8"), "txt": plain.encode("utf-8")}
    manifest = {
        "schema_version": 1, "input_path": str(cards_path),
        "input_sha256": hashlib.sha256(raw).hexdigest(),
        "fps": f"{rate.numerator}/{rate.denominator}",
        "frame_ranges": "start_inclusive_end_exclusive",
        "offset_frames_applied_once": offset_frames,
        "duration_frames": duration_frames, "caption_count": len(normalized),
        "txt_layout": "paragraphs" if paragraphs is not None else "one_card_per_line",
        "cards": normalized,
        "files": {kind: {"path": str(paths[kind]), "sha256": hashlib.sha256(value).hexdigest()}
                  for kind, value in data.items()},
        "verified": ["ordered_nonoverlapping_frame_ranges", "srt_derived_from_absolute_boundaries",
                     "txt_and_srt_share_spoken_text"],
        "not_verified": ["actual_video_caption_match", "listening", "semantic_accuracy",
                         "manual_200ms_sync", "full_video_review"],
    }
    if paragraphs_path is not None:
        manifest["paragraphs"] = {"path": str(paragraphs_path),
                                  "sha256": hashlib.sha256(paragraphs_path.read_bytes()).hexdigest()}
    data["manifest"] = (json.dumps(manifest, ensure_ascii=False, indent=2) + "\n").encode("utf-8")
    output_stem.parent.mkdir(parents=True, exist_ok=True)
    for kind, value in data.items():
        with paths[kind].open("xb") as handle:
            handle.write(value)
    return {kind: str(path) for kind, path in paths.items()}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--cards", required=True, type=Path)
    parser.add_argument("--fps", required=True, help="Final fps, e.g. 30 or 30000/1001")
    parser.add_argument("--output-stem", required=True, type=Path)
    parser.add_argument("--offset-frames", default=0, type=int,
                        help="Explicit offset only when input excludes a newly inserted cover")
    parser.add_argument("--duration-frames", type=int, help="Final complete video length, including cover/ending")
    parser.add_argument("--paragraphs", type=Path, help="Optional JSON array of ordered card-id groups")
    args = parser.parse_args()
    try:
        result = export(args.cards, args.output_stem, args.fps, offset_frames=args.offset_frames,
                        duration_frames=args.duration_frames, paragraphs_path=args.paragraphs)
    except (ValueError, FileExistsError, OSError) as exc:
        parser.exit(2, f"Subtitle export failed: {exc}\n")
    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
