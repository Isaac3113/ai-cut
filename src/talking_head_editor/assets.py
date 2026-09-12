from __future__ import annotations

import json
import os
import urllib.parse
import urllib.request
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

from .util import (ROOT, require, copy_media, job_lock, load_job, save_revision, probe,
                   streams, inside, run, executable, atomic_json, digest, ident, number)

IMAGE_EXT = {".png", ".jpg", ".jpeg", ".webp"}
MEDIA_EXT = IMAGE_EXT | {".mp4", ".mov", ".mkv", ".m4v", ".wav", ".mp3", ".m4a", ".flac"}


def describe_media(path):
    path = Path(path)
    if path.suffix.lower() in IMAGE_EXT:
        with Image.open(path) as im:
            im.verify()
        with Image.open(path) as im:
            return {"kind": "image", "width": im.width, "height": im.height}
    info = probe(path)
    video = streams(info, "video")
    return {"kind": "video" if video else "audio", "duration": float(info["format"]["duration"]),
            **({"width": video[0]["width"], "height": video[0]["height"]} if video else {})}


def register(job, path, metadata=None):
    metadata = metadata or {"license": {"kind": "provided"}, "source_url": "", "author": "user-provided"}
    require(metadata.get("license", {}).get("kind") in ("provided", "free", "paid"), "license", "Record asset license kind")
    info = describe_media(path)
    with job_lock(job):
        job, p = load_job(job)
        record = copy_media(path, job, "assets")
        aid = "a" + record["sha256"][:16]
        if aid in p["assets"]:
            return {"asset_id": aid, "revision": p["revision"], "existing": True}
        allowed = {k:v for k,v in metadata.items() if k in ("license","source_url","author","preview_url","price","purpose")}
        record.update(info, **allowed, review={"description": "", "evidence": ""})
        p["assets"][aid] = record
        save_revision(job, p, expected=p["revision"], event="asset_registered")
    sheet = contact_sheet(job, inside(job, record["path"]), aid) if info["kind"] != "audio" else None
    return {"asset_id": aid, "revision": p["revision"], "contact_sheet": sheet,
            "next": "Inspect the actual media, then annotate its contents and relevance"}


def index_folder(job, directory):
    directory = Path(directory).resolve()
    require(directory.is_dir(), "asset_directory", "Asset folder missing")
    files = sorted(p for p in directory.rglob("*") if p.is_file() and not p.is_symlink() and p.suffix.lower() in MEDIA_EXT)
    return {"assets": [register(job, p) for p in files]}


def annotate(job, aid, description, evidence):
    require(description.strip() and evidence.strip(), "review_evidence", "Describe actual viewed/heard media and inspected timestamps/frames")
    with job_lock(job):
        job, p = load_job(job)
        require(aid in p["assets"], "asset_id", "Asset missing")
        p["assets"][aid]["review"] = {"description": description, "evidence": evidence}
        save_revision(job, p, expected=p["revision"], event="asset_reviewed")
        return {"revision": p["revision"], "asset_id": aid}


def approve_paid(job, aid, evidence):
    require(evidence.strip(), "user_evidence", "Record actual user's approval after showing preview, price and purpose")
    with job_lock(job):
        job, p = load_job(job)
        a = p["assets"].get(aid)
        require(a and a["license"]["kind"] == "paid", "paid_asset", "Choose a paid asset")
        require(a.get("preview_url") and a.get("purpose") and a.get("price", {}).get("currency"),
                "paid_preview", "Paid asset needs preview URL, currency, price and intended use")
        number(a["price"]["amount"], "price")
        a["approval"] = {"user_evidence": evidence, "sha256": a["sha256"]}
        save_revision(job, p, expected=p["revision"], event="paid_asset_approved")
        return {"revision": p["revision"], "asset_id": aid, "purchase_performed": False}


def contact_sheet(job, path, name="source", times=None):
    ident(name)
    folder = Path(job) / "review" / name
    folder.mkdir(parents=True, exist_ok=True)
    media = describe_media(path)
    frames = []
    if media["kind"] == "image":
        frames = [(0, Image.open(path).convert("RGB"))]
    elif media["kind"] == "video":
        duration = media["duration"]
        times = times or [min(max(0, duration-.1), duration*i/7) for i in range(8)]
        for i, at in enumerate(times):
            dst = folder / f"frame{i:03d}.jpg"
            run([executable("ffmpeg"), "-y", "-v", "error", "-ss", str(max(0, at)), "-i", path,
                 "-frames:v", "1", "-vf", "scale=480:-2", "-pix_fmt", "yuvj420p", dst], timeout=120)
            if dst.is_file():
                frames.append((at, Image.open(dst).convert("RGB")))
    require(frames, "no_frames", "Cannot inspect frames for this media")
    columns = 2
    sheet = Image.new("RGB", (960, ((len(frames)+1)//2)*308), "#151923")
    draw = ImageDraw.Draw(sheet)
    for i, (at, im) in enumerate(frames):
        im.thumbnail((472, 270))
        x, y = (i % columns)*480, (i//columns)*308
        sheet.paste(im, (x+(480-im.width)//2, y))
        draw.text((x+10, y+275), f"{at:.3f}s", fill="white")
    output = folder / "contact-sheet.jpg"
    sheet.save(output, quality=90)
    return str(output)


def pexels_search(job, query, media_type="video", limit=6):
    key = os.environ.get("PEXELS_API_KEY")
    require(key, "pexels_key_missing", "Pexels API key not configured. Use browser search/download and asset register; never scrape credentials")
    require(media_type in ("video", "image"), "search_type", "Choose video or image")
    base = "https://api.pexels.com/videos/search" if media_type == "video" else "https://api.pexels.com/v1/search"
    req = urllib.request.Request(base + "?" + urllib.parse.urlencode({"query": query, "per_page": min(limit, 15)}),
                                 headers={"Authorization": key, "User-Agent": "TalkingHeadEditor/0.1"})
    with urllib.request.urlopen(req, timeout=30) as r:
        data = json.load(r)
    candidates = []
    for item in data.get("videos" if media_type == "video" else "photos", []):
        if media_type == "video":
            files = [f for f in item["video_files"] if f.get("file_type") == "video/mp4" and f.get("width")]
            require(files, "pexels_file", "No usable MP4 candidate")
            selected = min(files, key=lambda f: abs(max(f["width"], f["height"])-1920))
            download = selected["link"]
            author = item.get("user", {}).get("name", "")
            preview = item.get("image")
        else:
            download, author, preview = item["src"]["large2x"], item.get("photographer", ""), item["src"]["medium"]
        candidates.append({"id": str(item["id"]), "kind": media_type, "source_url": item["url"],
                           "download_url": download, "preview_url": preview, "author": author,
                           "license": {"kind": "free", "url": "https://www.pexels.com/license/"}})
    path = Path(job) / "research" / (digest({"query":query,"type":media_type})[:16]+".json")
    atomic_json(path, {"query": query, "candidates": candidates})
    return {"file": str(path), "candidates": candidates, "note": "Inspect assets; generic stock is not evidence of user/customer identity"}


def download_pexels(job, candidate):
    url = candidate["download_url"]
    allowed = {"images.pexels.com", "videos.pexels.com"}
    def valid(u):
        parsed = urllib.parse.urlsplit(u)
        return parsed.scheme == "https" and parsed.hostname in allowed and not parsed.username and parsed.port in (None,443)
    require(valid(url), "download_host", "Automatic downloader only accepts official Pexels media hosts")
    class Redirect(urllib.request.HTTPRedirectHandler):
        def redirect_request(self, req, fp, code, msg, headers, newurl):
            require(valid(newurl), "download_redirect", "Unexpected media redirect host")
            return super().redirect_request(req, fp, code, msg, headers, newurl)
    suffix = ".mp4" if candidate["kind"] == "video" else ".jpg"
    tmp = Path(job) / "downloads" / (digest(url) + suffix)
    tmp.parent.mkdir(parents=True, exist_ok=True)
    opener = urllib.request.build_opener(Redirect())
    with opener.open(url, timeout=60) as response, tmp.with_suffix(suffix+".partial").open("wb") as f:
        total = 0
        while chunk := response.read(1024*1024):
            total += len(chunk)
            require(total <= 512*1024*1024, "download_size", "Media download exceeds 512 MB; choose a smaller source")
            f.write(chunk)
    os.replace(tmp.with_suffix(suffix+".partial"), tmp)
    return register(job, tmp, candidate)
