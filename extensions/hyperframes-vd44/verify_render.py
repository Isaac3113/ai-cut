"""Inspect already-decoded render frames; never manufactures a substitute render."""
from pathlib import Path
import hashlib
import json
from PIL import Image, ImageDraw, ImageStat

ROOT = Path(__file__).resolve().parent
frames = sorted((ROOT / 'evidence' / 'decoded-frames').glob('frame-*.jpg'))
probe = json.loads((ROOT / 'evidence' / 'ffprobe.json').read_text(encoding='utf-8-sig'))
video = ROOT / 'renders' / 'customer-status-vd44.mp4'
assert len(frames) == 201, f'Expected all 201 decoded frames, found {len(frames)}'
assert len(probe['streams']) == 1 and probe['streams'][0]['codec_type'] == 'video'
assert probe['streams'][0]['width'] == 1920 and probe['streams'][0]['height'] == 1080
assert probe['streams'][0]['r_frame_rate'] == '30/1'
assert int(probe['streams'][0]['nb_read_frames']) == 201
assert abs(float(probe['format']['duration']) - 6.7) < 0.0001

flat = []
deviations = []
for i, path in enumerate(frames):
    with Image.open(path) as im:
        deviation = max(ImageStat.Stat(im.convert('RGB')).stddev)
        deviations.append(deviation)
        if deviation < 0.5:
            flat.append(i)
assert not flat, f'Flat/blank frame candidates: {flat}'

picked = [0, 15, 36, 51, 58, 75, 97, 103, 114, 149, 157, 168, 198, 200]
tile_w, tile_h = 480, 298
sheet = Image.new('RGB', (tile_w * 4, tile_h * 4), '#101112')
draw = ImageDraw.Draw(sheet)
for slot, frame in enumerate(picked):
    x, y = (slot % 4) * tile_w, (slot // 4) * tile_h
    with Image.open(frames[frame]) as im:
        sheet.paste(im, (x, y + 26))
    draw.text((x + 8, y + 7), f'Encoded frame {frame:03d} / {frame / 30:.3f}s', fill='white')
sheet.save(ROOT / 'evidence' / 'encoded-contact-sheet.jpg', quality=94)

report = {
    'artifact': str(video),
    'sha256': hashlib.sha256(video.read_bytes()).hexdigest(),
    'bytes': video.stat().st_size,
    'width': 1920, 'height': 1080, 'fps': 30, 'frames': len(frames), 'duration_seconds': 6.7,
    'audio_streams': 0,
    'flat_frame_candidates': flat,
    'minimum_frame_rgb_stddev': min(deviations),
    'encoded_frames_in_contact_sheet': picked,
    'limitations': ['Pixel statistics are not full human viewing.', 'No listening applies: intentionally no audio.', 'ChatCut integration and complete talking-head export remain outside this insert verification.'],
}
(ROOT / 'evidence' / 'render-verification.json').write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding='utf-8')
print(json.dumps(report, ensure_ascii=False))
