"""Stage: assemble the film with FFmpeg (no AI here, same inputs -> same output).
- Ken Burns move over each keyframe, timed by the narration length
- time labels, English subtitles (<=2 lines, ~40 chars) and the end card drawn as PNG overlays
- score ducked under the narration (sidechaincompress), loudness normalised to -14 LUFS
- exports 9:16 and 16:9. Per-shot clips are cached by hash."""
import argparse, json, re, subprocess, sys, textwrap
from PIL import Image, ImageDraw, ImageFont
from common import ROOT, load_storyboard, sha

FPS = 24
KF, NAR, MUS = (ROOT / "outputs" / d for d in ("keyframes", "narration", "music"))
CLIPS, FINAL, TMP = (ROOT / "outputs" / d for d in ("clips", "final", "tmp"))
for d in (CLIPS, FINAL, TMP):
    d.mkdir(parents=True, exist_ok=True)

ap = argparse.ArgumentParser()
ap.add_argument("--draft", action="store_true", help="half resolution, fast")
ap.add_argument("--only", choices=["vertical", "horizontal"])
ap.add_argument("--force", action="store_true")
args = ap.parse_args()

board = load_storyboard()
shots = board["shots"]
timings = json.loads((NAR / "timings.json").read_text()) if (NAR / "timings.json").exists() else {}

FONTS = ["C:/Windows/Fonts/segoeuib.ttf", "C:/Windows/Fonts/arialbd.ttf", "C:/Windows/Fonts/arial.ttf",
         "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", "/System/Library/Fonts/Helvetica.ttc"]


def font(size):
    for f in FONTS:
        try:
            return ImageFont.truetype(f, size)
        except OSError:
            pass
    return ImageFont.load_default()


def run(cmd):
    r = subprocess.run([str(c) for c in cmd], capture_output=True, text=True)
    if r.returncode:
        print("FFMPEG ERROR:\n", r.stderr[-1500:])
        sys.exit(1)


def even(n):
    return int(n) // 2 * 2


# ---------- planning: how long is each shot? ----------
plan = []
for s in shots:
    nar = timings.get(s["id"])
    if nar is None:
        sys.exit(f"No narration timing for {s['id']}. Run narration.py first.")
    d = max(s["duration_sec"], nar + 0.9)  # never cut the voice off
    if d > s["duration_sec"]:
        print(f"{s['id']}: narration is {nar:.1f}s, shot lengthened {s['duration_sec']}s -> {d:.1f}s")
    plan.append((s, nar, round(d, 2)))
END = board["end_card"]["duration_sec"]
TOTAL = round(sum(p[2] for p in plan) + END, 2)
print(f"Planned film length: {TOTAL}s")
if not 60 <= TOTAL <= 90:
    print("WARNING: length is outside 60-90 seconds")


# ---------- overlays ----------
def boxed_text(lines, W, H, size, y_center):
    img = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    f = font(size)
    lh = int(size * 1.35)
    widths = [d.textlength(l, font=f) for l in lines]
    bw, bh = max(widths) + size, lh * len(lines) + size * 0.4
    x0, y0 = (W - bw) / 2, y_center - bh / 2
    d.rounded_rectangle([x0, y0, x0 + bw, y0 + bh], radius=size * 0.35, fill=(0, 0, 0, 140))
    for i, l in enumerate(lines):
        d.text((W / 2, y0 + size * 0.2 + i * lh + lh / 2), l, font=f, fill="white", anchor="mm",
               stroke_width=2, stroke_fill="black")
    return img


def label_png(text, W, H, path):
    size = int(min(W, H) * 0.045)
    img = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    f = font(size)
    w = d.textlength(text, font=f)
    x, y = W * 0.07, H * (0.075 if H > W else 0.09)
    d.rounded_rectangle([x, y, x + w + size, y + size * 1.7], radius=size * 0.3, fill=(0, 0, 0, 130))
    d.text((x + size / 2, y + size * 0.85), text, font=f, fill=(255, 220, 150, 255), anchor="lm")
    img.save(path)


def sub_chunks(text, max_chars=40):
    out = []
    for sent in re.split(r"(?<=[.!?])\s+", text.strip()):
        lines = textwrap.wrap(sent, max_chars)
        for i in range(0, len(lines), 2):
            out.append(lines[i:i + 2])
    return out


def end_png(lines, W, H, path):
    img = Image.new("RGB", (W, H), "black")
    d = ImageDraw.Draw(img)
    big, small = int(min(W, H) * 0.075), int(min(W, H) * 0.04)
    d.text((W / 2, H * 0.46), lines[0], font=font(big), fill="white", anchor="mm")
    for i, l in enumerate(lines[1:]):
        d.text((W / 2, H * 0.56 + i * small * 1.6), l, font=font(small), fill=(190, 190, 190), anchor="mm")
    img.save(path)


# ---------- one clip per shot ----------
def camera_expr(cam, n):
    ctr_x, ctr_y = "iw/2-(iw/zoom/2)", "ih/2-(ih/zoom/2)"
    if cam == "push_in":
        return f"1+0.12*on/{n}", ctr_x, ctr_y
    if cam == "zoom_out":
        return f"1.12-0.12*on/{n}", ctr_x, ctr_y
    if cam == "pan_right":
        return "1.12", f"(iw-iw/zoom)*on/{n}", ctr_y
    if cam == "pan_left":
        return "1.12", f"(iw-iw/zoom)*(1-on/{n})", ctr_y
    return f"1+0.03*on/{n}", ctr_x, ctr_y  # static: almost still


def make_clip(s, nar, dur, W, H, tag):
    out, hfile = CLIPS / f"{tag}_{s['id']}.mp4", CLIPS / f"{tag}_{s['id']}.hash"
    src = KF / f"{s['id']}.jpg"
    if not src.exists():
        sys.exit(f"Missing keyframe {src.name}. Run keyframes.py first.")
    h = sha(src.read_bytes().hex()[:2000], len(src.read_bytes()), s["camera"], s["narration"], s.get("time_label"),
            dur, nar, W, H)
    if not args.force and out.exists() and hfile.exists() and hfile.read_text() == h:
        return out, True
    # center-crop the (square) picture to the target shape, oversample 1.5x for a smooth zoom
    im = Image.open(src).convert("RGB")
    iw, ih = im.size
    target = W / H
    if iw / ih > target:
        nw = int(ih * target)
        im = im.crop(((iw - nw) // 2, 0, (iw - nw) // 2 + nw, ih))
    else:
        nh = int(iw / target)
        im = im.crop((0, (ih - nh) // 2, iw, (ih - nh) // 2 + nh))
    prep = TMP / f"{tag}_{s['id']}.jpg"
    im.resize((even(W * 1.5), even(H * 1.5)), Image.LANCZOS).save(prep, quality=95)

    inputs = ["-i", prep]
    n = round(dur * FPS)
    z, x, y = camera_expr(s["camera"], n)
    chain = f"[0:v]zoompan=z='{z}':x='{x}':y='{y}':d={n}:s={W}x{H}:fps={FPS},format=yuv420p[v0]"
    k, last = 1, "v0"
    if s.get("time_label"):
        lp = TMP / f"{tag}_{s['id']}_label.png"
        label_png(s["time_label"], W, H, lp)
        inputs += ["-i", lp]
        chain += f";[{last}][{k}:v]overlay=0:0:enable='between(t,0.3,3.3)'[v{k}]"
        last, k = f"v{k}", k + 1
    chunks = sub_chunks(s["narration"], 28 if H > W else 40)
    weights = [sum(len(l) for l in c) for c in chunks]
    t0, span = 0.3, nar
    for ci, c in enumerate(chunks):
        a = t0
        b = t0 + span * weights[ci] / sum(weights)
        t0 = b
        sp = TMP / f"{tag}_{s['id']}_sub{ci}.png"
        y_c = H * (0.80 if H > W else 0.88)
        boxed_text(c, W, H, int(min(W, H) * (0.046 if H > W else 0.048)), y_c).save(sp)
        inputs += ["-i", sp]
        chain += f";[{last}][{k}:v]overlay=0:0:enable='between(t,{a:.2f},{b:.2f})'[v{k}]"
        last, k = f"v{k}", k + 1
    run(["ffmpeg", "-y", *inputs, "-filter_complex", chain, "-map", f"[{last}]", "-t", dur, "-r", FPS,
         "-c:v", "libx264", "-preset", "veryfast", "-crf", "20", "-pix_fmt", "yuv420p", out])
    hfile.write_text(h)
    return out, False


# ---------- audio mix (same for both aspect ratios) ----------
def build_audio():
    inputs, parts = [], []
    for i, (s, nar, dur) in enumerate(plan):
        inputs += ["-i", NAR / f"{s['id']}.wav"]
        parts.append(f"[{i}:a]aresample=48000,adelay=300:all=1,apad=whole_dur={dur}[a{i}]")
    n = len(plan)
    parts.append(f"anullsrc=r=48000:cl=mono,atrim=0:{END}[sil]")
    parts.append("".join(f"[a{i}]" for i in range(n)) + f"[sil]concat=n={n + 1}:v=0:a=1[nar]")
    music = next((p for ext in ("wav", "mp3", "flac", "m4a") for p in MUS.glob(f"score*.{ext}")), None)
    if music:
        inputs += ["-stream_loop", "-1", "-i", music]
        m = n
        parts.append("[nar]asplit=2[n1][n2]")
        parts.append(f"[{m}:a]aresample=48000,aformat=channel_layouts=stereo,atrim=0:{TOTAL},asetpts=PTS-STARTPTS,"
                     f"volume=0.7,afade=t=in:d=2,afade=t=out:st={TOTAL - 3}:d=3[mus]")
        parts.append("[n1]aformat=channel_layouts=stereo[k]")
        parts.append("[mus][k]sidechaincompress=threshold=0.02:ratio=6:attack=300:release=1500[duck]")
        parts.append("[n2]aformat=channel_layouts=stereo[nv]")
        parts.append("[nv][duck]amix=inputs=2:duration=first:dropout_transition=0,volume=2,"
                     "loudnorm=I=-14:TP=-1:LRA=11[out]")
        print(f"Score: {music.name} (ducked under narration)")
    else:
        parts.append("[nar]aformat=channel_layouts=stereo,loudnorm=I=-14:TP=-1:LRA=11[out]")
        print("No score found in outputs/music/ (score.wav or score.mp3): narration only")
    mix = FINAL / "mix.m4a"
    run(["ffmpeg", "-y", *inputs, "-filter_complex", ";".join(parts), "-map", "[out]", "-t", TOTAL,
         "-ar", 48000, "-c:a", "aac", "-b:a", "192k", mix])
    return mix


# ---------- main ----------
targets = [t for t in board["export"]["targets"]
           if not args.only or (args.only == "vertical") == (t["aspect"] == "9:16")]
mix = build_audio()
for t in targets:
    W, H = map(int, t["size"].split("x"))
    if args.draft:
        W, H = even(W / 2), even(H / 2)
    tag = f"{'v' if H > W else 'h'}{'d' if args.draft else ''}"
    print(f"\n== {t['aspect']} ({W}x{H}) ==")
    clip_files = []
    for s, nar, dur in plan:
        f, cached = make_clip(s, nar, dur, W, H, tag)
        print(f"  {s['id']}: {'cached' if cached else 'built'} ({dur}s)")
        clip_files.append(f)
    ep = TMP / f"{tag}_end.png"
    end_png(board["end_card"]["lines"], W, H, ep)
    endclip = CLIPS / f"{tag}_end.mp4"
    run(["ffmpeg", "-y", "-loop", 1, "-t", END, "-i", ep, "-vf", f"fade=t=in:st=0:d=1,fps={FPS},format=yuv420p",
         "-c:v", "libx264", "-preset", "veryfast", "-crf", "20", endclip])
    lst = CLIPS / f"{tag}_list.txt"
    lst.write_text("".join(f"file '{p.name}'\n" for p in clip_files + [endclip]))
    silent = CLIPS / f"{tag}_silent.mp4"
    run(["ffmpeg", "-y", "-f", "concat", "-safe", 0, "-i", lst, "-c", "copy", silent])
    dest = ROOT / t["file"]
    dest.parent.mkdir(parents=True, exist_ok=True)
    if args.draft:
        dest = dest.with_name(dest.stem + "_draft.mp4")
    run(["ffmpeg", "-y", "-i", silent, "-i", mix, "-c:v", "copy", "-c:a", "copy", "-t", TOTAL,
         "-movflags", "+faststart", dest])
    print(f"  -> {dest.relative_to(ROOT)}")
print("\nDone.")