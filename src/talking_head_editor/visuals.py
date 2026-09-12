from __future__ import annotations

import os
import re
import shutil
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

from .util import require, runtime_config, ROOT, file_hash


def font_path():
    choices = [os.environ.get("THE_FONT"), runtime_config().get("font"),
               "C:/Windows/Fonts/msyh.ttc", "/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc"]
    selected = next((Path(p) for p in choices if p and Path(p).is_file()), None)
    require(selected, "font_missing", "Configure THE_FONT with a locally licensed CJK font")
    return selected


def font(size):
    return ImageFont.truetype(str(font_path()), max(12, int(size)))


def render_font_dir():
    # Load the selected local font only; scanning the entire Windows font folder
    # hits legacy .fon files and can destabilize libass/FreeType builds.
    source=font_path()
    folder=ROOT/".runtime"/"fonts"/file_hash(source)
    folder.mkdir(parents=True,exist_ok=True)
    target=folder/source.name
    if not target.exists(): shutil.copyfile(source,target)
    require(file_hash(target)==file_hash(source),"font_changed","Cached local font mismatch")
    return folder


def join_tokens(tokens):
    output = ""
    for token in tokens:
        if output and re.search(r"[A-Za-z0-9]$", output) and re.match(r"[A-Za-z0-9]", token):
            output += " "
        output += token
    return output


def wrap(text, face, max_width):
    tokens = re.findall(r"[A-Za-z0-9]+(?:[._%+-][A-Za-z0-9]+)*|[^\s]", text)
    lines, current = [], ""
    for token in tokens:
        candidate = join_tokens([current, token]) if current else token
        if face.getlength(candidate) > max_width and current:
            lines.append(current)
            current = token
        else:
            current = candidate
        if face.getlength(current) > max_width:
            # A very long URL/English token must not leave the canvas.
            chars = current
            current = ""
            for char in chars:
                if face.getlength(current + char) > max_width and current:
                    lines.append(current)
                    current = char
                else:
                    current += char
    if current:
        lines.append(current)
    return lines


def caption_cues(words, width, height, style, scale=1):
    face = font(style["font_size"]*scale)
    max_width = width * (.82 if height > width else .84)
    cues, active = [], []
    def flush():
        if active:
            text = join_tokens([w["text"] for w in active])
            lines = wrap(text, face, max_width)
            require(len(lines) <= 2, "caption_overflow", "Caption cannot fit two lines; split the source tokens")
            cues.append({"start": active[0]["start"], "end": active[-1]["end"],
                         "text": text, "lines": lines, "word_ids": [w["id"] for w in active],
                         "max_line_width": max(face.getlength(x) for x in lines)})
            active.clear()
    for word in words:
        proposed = join_tokens([w["text"] for w in active] + [word["text"]])
        if active and (word["end"]-active[0]["start"] > 3.2
                       or word["start"]-active[-1]["end"] > .45
                       or word.get("clip_id") != active[0].get("clip_id")
                       or len(wrap(proposed, face, max_width)) > 2):
            flush()
        active.append(word)
        if word.get("caption_break_after") or re.search(r"[。！？!?；;]$", word["text"]):
            flush()
    flush()
    return cues


def ass_time(t):
    centis = max(0, round(t*100))
    h, rem = divmod(centis, 360000)
    m, rem = divmod(rem, 6000)
    s, c = divmod(rem, 100)
    return f"{h}:{m:02d}:{s:02d}.{c:02d}"


def srt_time(t):
    ms = max(0, round(t*1000))
    h, rem = divmod(ms, 3600000)
    m, rem = divmod(rem, 60000)
    s, ms = divmod(rem, 1000)
    return f"{h:02d}:{m:02d}:{s:02d},{ms:03d}"


def ass_color(color):
    return "&H00" + color[5:7] + color[3:5] + color[1:3]


def ass_escape(text):
    return text.replace("\\", "＼").replace("{", "｛").replace("}", "｝").replace("\n", " ")


def write_captions(folder, cues, width, height, style, scale=1, theme_ranges=None):
    face = font(style["font_size"]*scale)
    family = face.getname()[0].replace(",", " ")
    fontsize = round(style["font_size"]*scale)
    margin = round((180 if height > width else 65)*scale)
    bold = -1 if style.get("caption_bold", True) else 0
    outline = max(0,style.get("caption_outline",3)*scale)
    shadow = max(0,style.get("caption_shadow",1)*scale)
    header = f"""[Script Info]
ScriptType: v4.00+
PlayResX: {width}
PlayResY: {height}
WrapStyle: 2
ScaledBorderAndShadow: yes

[V4+ Styles]
Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding
Style: Default,{family},{fontsize},{ass_color(style['caption_color'])},{ass_color(style['accent'])},&H00101519,&H80000000,{bold},0,0,0,100,100,0,0,1,{outline},{shadow},2,{round(width*.08)},{round(width*.08)},{margin},1

[Events]
Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text
"""
    rows, srt = [], []
    keywords = style.get("keywords", [])
    for i, cue in enumerate(cues):
        text = r"\N".join(ass_escape(x) for x in cue["lines"])
        for keyword in keywords:
            escaped = ass_escape(keyword)
            if escaped:
                text = text.replace(escaped, "{\\c"+ass_color(style['accent'])+"&}"+escaped+"{\\r}")
        # Split only ASS appearance at a full-frame visual boundary. Spoken text,
        # SRT timing and word identities remain on the unchanged master timeline.
        ranges=theme_ranges or []
        boundaries=sorted({cue['start'],cue['end']} | {x for span in ranges for x in (span['start'],span['end']) if cue['start']<x<cue['end']})
        for start,end in zip(boundaries,boundaries[1:]):
            theme=next((x['theme'] for x in ranges if x['start']<=(start+end)/2<x['end']),None)
            tags=r'{\1c&H003D2F17&\bord0\shad0}' if theme=='dark' else r'{\fad(60,60)}'
            rows.append(f"Dialogue: 0,{ass_time(start)},{ass_time(end)},Default,,0,0,0,,{tags}{text}")
        srt.append(f"{i+1}\n{srt_time(cue['start'])} --> {srt_time(cue['end'])}\n" + "\n".join(cue["lines"]))
    Path(folder, "captions.ass").write_text(header + "\n".join(rows), encoding="utf-8-sig")
    Path(folder, "captions.srt").write_text("\n\n".join(srt)+"\n", encoding="utf-8")


def graphic_image(graphic, output, width, height, style):
    typ = graphic["type"]
    if typ != "bar":
        require(typ in ("flow", "states", "title", "keywords"), "graphic_type", "Unknown graphic type")
        require(width >= 160 and height >= 96, "graphic_size", "Graphic is too small for readable text")
        image = Image.new("RGBA", (width, height), style["background"])
        draw = ImageDraw.Draw(image)
        unit = min(width, height) / 1080
        banner = width / height >= 3.5 or height <= 190
        small = min(width, height) < 420
        portrait = height > width
        margin = max(12, round((.13 * height) if banner else 64 * unit))
        caption_margin = (180 if portrait else 65) * unit
        reserve = 0 if banner or small else int(max(210 * unit, caption_margin + style["font_size"] * unit * 3.2 + 24 * unit) + .999)
        bottom = height - reserve
        require(bottom > margin * 3, "graphic_overflow", "Insufficient space above the subtitle safe area")
        navy, muted, cyan = "#152A40", "#233D53", "#43D5E8"
        yellow = style["accent"]
        draw.rounded_rectangle((margin, margin, width-margin, bottom-margin),
                               radius=max(8, round(24*unit)), fill=navy)
        draw.rounded_rectangle((margin*2, margin, margin*2+max(30, round(104*unit)),
                                margin+max(3, round(7*unit))), radius=2, fill=yellow)

        def fit_text(text, max_width, max_height, maximum, minimum, max_lines, code):
            require(isinstance(text, str) and text.strip(), code, "Use nonempty graphic text")
            for size in range(max(12, int(maximum)), max(11, int(minimum))-1, -1):
                face = font(size)
                lines = wrap(text.strip(), face, max_width)
                line_height = int(size*1.5+.999)
                if len(lines) <= max_lines and len(lines)*line_height <= max_height:
                    return face, lines, line_height
            require(False, code, "Shorten the graphic text to keep it readable and inside the panel")

        def text_lines(lines, face, line_height, box, fill, centered=False):
            left, top, right, lower = box
            top += max(0, (lower-top-len(lines)*line_height)/2)
            for line in lines:
                x = (left+right-face.getlength(line))/2 if centered else left
                draw.text((x, top), line, font=face, fill=fill, anchor="lt")
                top += line_height

        title = graphic.get("title") or graphic.get("text", "")
        subtitle = graphic.get("subtitle", "")
        require(isinstance(subtitle, str), "graphic_subtitle", "subtitle must be text")
        inner_left, inner_right = margin*2, width-margin*2
        available_width = inner_right-inner_left
        if typ in ("title", "keywords"):
            title_max = height*.34 if banner else 120*unit
            title_min = max(16, height*.15) if banner else max(16, 38*unit)
            text_height = bottom-margin*(3 if banner else 4)
            title_face, title_lines, title_step = fit_text(
                title, available_width, text_height*(.63 if subtitle else 1),
                title_max, title_min, 1 if banner else 3, "graphic_overflow")
            sub = None
            if subtitle:
                sub = fit_text(subtitle, available_width, text_height*.32,
                               height*.18 if banner else 42*unit, 14 if small else 26*unit,
                               1 if banner else 2, "graphic_subtitle")
            spacing = max(8, round(26*unit)) if sub else 0
            total = len(title_lines)*title_step + spacing + (len(sub[1])*sub[2] if sub else 0)
            top = (bottom-total)/2
            require(top >= margin*(1.4 if banner else 1.5) and top+total <= bottom-margin,
                    "graphic_overflow", "Graphic text exceeds safe panel")
            text_lines(title_lines, title_face, title_step,
                       (inner_left, top, inner_right, top+len(title_lines)*title_step),
                       yellow if typ == "keywords" else "#F4FAFF")
            if sub:
                top += len(title_lines)*title_step + spacing
                text_lines(sub[1], sub[0], sub[2], (inner_left, top, inner_right, top+len(sub[1])*sub[2]), "#BBD0DD")
            image.save(output)
            return

        nodes = graphic.get("nodes", [])
        require(isinstance(nodes, list) and 1 <= len(nodes) <= 5
                and all(isinstance(node, str) and node.strip() for node in nodes),
                "flow_nodes", "Use 1..5 nonempty node labels")
        count = graphic.get("visible_count", len(nodes))
        active = graphic.get("active_index")
        require(type(count) is int and 1 <= count <= len(nodes), "graphic_state", "visible_count must be 1..number of nodes")
        require(active is None or (type(active) is int and 0 <= active < count),
                "graphic_state", "active_index must identify one visible node")
        title_face, title_lines, title_step = fit_text(
            title, available_width, (bottom-margin*3)*.30,
            height*.20 if banner else 72*unit, 16 if small else 32*unit,
            1 if banner else 2, "graphic_overflow")
        y = margin*1.8
        text_lines(title_lines, title_face, title_step,
                   (inner_left, y, inner_right, y+len(title_lines)*title_step), "#F4FAFF")
        y += len(title_lines)*title_step
        if subtitle:
            face, lines, step = fit_text(subtitle, available_width, (bottom-margin*3)*.14,
                                         34*unit, 12 if small else 24*unit, 1, "graphic_subtitle")
            text_lines(lines, face, step, (inner_left, y, inner_right, y+step), "#BBD0DD")
            y += step
        area_top = y + max(6, round(22*unit))
        area_bottom = bottom-margin*1.7
        require(area_bottom-area_top > 35, "flow_overflow", "Title leaves too little room for nodes")
        gap = max(14, round(52*unit))
        boxes = []
        if portrait:
            node_height = min(208*unit, (area_bottom-area_top-gap*(len(nodes)-1))/len(nodes))
            require(node_height >= 40, "flow_overflow", "Too many nodes for this graphic size")
            top = area_top+(area_bottom-area_top-node_height*len(nodes)-gap*(len(nodes)-1))/2
            for index in range(len(nodes)):
                boxes.append((inner_left, top+index*(node_height+gap), inner_right,
                              top+index*(node_height+gap)+node_height))
        else:
            node_width = (available_width-gap*(len(nodes)-1))/len(nodes)
            node_height = min(280*unit if not banner else height*.40, area_bottom-area_top)
            require(node_width >= 60 and node_height >= 36, "flow_overflow", "Too many nodes for this graphic size")
            top = area_top+(area_bottom-area_top-node_height)/2
            for index in range(len(nodes)):
                left = inner_left+index*(node_width+gap)
                boxes.append((left, top, left+node_width, top+node_height))

        # Only a real flow has arrows. Parallel states keep identical positions
        # through the reveal, but never acquire a visual order relationship.
        if typ == "flow":
            for index in range(count-1):
                left, right = boxes[index], boxes[index+1]
                stroke = max(2, round(5*unit))
                head = max(5, round(13*unit))
                if portrait:
                    center = (left[0]+left[2])/2
                    a, b = left[3]+4, right[1]-4
                    draw.line((center, a, center, b-head), fill=cyan, width=stroke)
                    draw.polygon(((center, b), (center-head*.65, b-head), (center+head*.65, b-head)), fill=cyan)
                else:
                    center = (left[1]+left[3])/2
                    a, b = left[2]+4, right[0]-4
                    draw.line((a, center, b-head, center), fill=cyan, width=stroke)
                    draw.polygon(((b, center), (b-head, center-head*.65), (b-head, center+head*.65)), fill=cyan)

        for index, box in enumerate(boxes):
            shown, current = index < count, index == active
            fill = cyan if current else (muted if shown else "#172A3D")
            outline = cyan if current else ("#43667E" if shown else "#263D51")
            draw.rounded_rectangle(box, radius=max(8, round(20*unit)), fill=fill, outline=outline,
                                   width=max(1, round((4 if current else 2)*unit)))
            if not shown:
                continue
            left, top, right, lower = box
            pad = max(8, round(24*unit))
            if portrait:
                badge_size = max(22, round(54*unit))
                badge_box = (left+pad, (top+lower-badge_size)/2, left+pad+badge_size, (top+lower+badge_size)/2)
                text_box = (badge_box[2]+pad, top+pad, right-pad, lower-pad)
            else:
                badge_size = max(16, round(48*unit))
                badge_box = ((left+right-badge_size)/2, top+pad*.5, (left+right+badge_size)/2, top+pad*.5+badge_size)
                text_box = (left+pad, badge_box[3]+max(4, pad*.3), right-pad, lower-pad*.5)
            # Flow numbers identify steps; a state receives a dot, not a stage number.
            draw.ellipse(badge_box, fill=yellow if current else "#3B5A70")
            if typ == "flow":
                badge_face = font(max(12, badge_size*.58))
                label = str(index+1)
                draw.text(((badge_box[0]+badge_box[2]-badge_face.getlength(label))/2,
                           (badge_box[1]+badge_box[3]-badge_size*.7)/2), label,
                          font=badge_face, fill="#102336" if current else "#C5DFEC", anchor="lt")
            face, lines, step = fit_text(nodes[index], text_box[2]-text_box[0], text_box[3]-text_box[1],
                                         max(14, 46*unit), max(12, 26*unit), 2, "flow_overflow")
            text_lines(lines, face, step, text_box, "#102336" if current else "#D7E9F3", centered=not portrait)
        image.save(output)
        return

    # Preserve the existing numeric chart renderer and its data validation.
    image = Image.new("RGBA", (width, height), style["background"])
    draw = ImageDraw.Draw(image)
    unit = min(width, height)/1080
    margin = int(72*unit)
    accent = style["accent"]
    draw.rounded_rectangle((margin, margin, width-margin, height-margin), radius=int(36*unit), fill="#202633")
    draw.rounded_rectangle((margin, margin, margin+int(100*unit), margin+int(8*unit)), radius=3, fill=accent)
    title = graphic.get("title") or graphic.get("text", "")
    size = 70*unit
    while size > 28*unit and len(wrap(title, font(size), width-4*margin)) > 3:
        size -= 2
    title_face = font(size)
    lines = wrap(title, title_face, width-4*margin)
    require(len(lines) <= 3, "graphic_overflow", "Title too long; simplify graphic")
    y = margin*2
    for line in lines:
        draw.text((margin*2, y), line, font=title_face, fill="white")
        y += size*1.45
    typ = graphic["type"]
    if typ == "bar":
        items = graphic["items"]
        require(len(items) <= 6, "chart_items", "Use at most six bars per card")
        maxvalue = max((x["value"] for x in items), default=0) or 1
        remaining = height-y-margin*2
        require(remaining>=len(items)*40*unit,"chart_overflow","Chart title leaves insufficient room for bars")
        row = remaining/max(1,len(items))
        label_face = font(min(42*unit, row*.35))
        for item in items:
            label=f"{item['label']}  {item['value']:g}{graphic.get('unit','')}"
            require(label_face.getlength(label)<=width-4*margin,"chart_overflow","Chart label exceeds the card; shorten it or use a separate card")
            draw.text((margin*2,y), label, font=label_face, fill="white")
            length = max(1, (width-4*margin)*item["value"]/maxvalue)
            draw.rounded_rectangle((margin*2,y+row*.47,margin*2+length,y+row*.73), radius=max(1,int(9*unit)), fill=accent)
            y += row
    elif typ == "flow":
        nodes = graphic.get("nodes", [])
        require(1 <= len(nodes) <= 5, "flow_nodes", "Use 1..5 flow nodes")
        step = (height-y-margin*2)/len(nodes)
        for i, node in enumerate(nodes):
            draw.rounded_rectangle((margin*2,y,width-margin*2,y+step*.75), radius=12, fill="#30394A")
            label = f"{i+1:02d}  {node}"
            face = font(min(46*unit, step*.35))
            require(face.getlength(label) <= width-5*margin, "flow_overflow", "Flow label too long")
            draw.text((margin*2.3,y+step*.12), label, font=face, fill=accent)
            y += step
    image.save(output)
