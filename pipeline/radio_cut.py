"""Radio cut: all narration lines in order, with short pauses, on a black screen."""
import subprocess
from common import ROOT, load_storyboard

board = load_storyboard()
OUT = ROOT / "outputs" / "final"
OUT.mkdir(parents=True, exist_ok=True)
wavs = [ROOT / "outputs" / "narration" / f"{s['id']}.wav" for s in board["shots"]]
missing = [w.name for w in wavs if not w.exists()]
if missing:
    raise SystemExit(f"Missing narration files: {missing}. Run narration first.")

cmd = ["ffmpeg", "-y"]
for w in wavs:
    cmd += ["-i", str(w)]
n = len(wavs)
padded = ";".join(f"[{i}:a]apad=pad_dur=0.7[a{i}]" for i in range(n))
concat = "".join(f"[a{i}]" for i in range(n)) + f"concat=n={n}:v=0:a=1[out]"
audio = OUT / "radio_cut.wav"
subprocess.run(cmd + ["-filter_complex", padded + ";" + concat, "-map", "[out]", str(audio)], check=True)
subprocess.run(["ffmpeg", "-y", "-f", "lavfi", "-i", "color=c=black:s=720x1280:r=24", "-i", str(audio),
                "-shortest", "-c:v", "libx264", "-pix_fmt", "yuv420p", "-c:a", "aac",
                str(OUT / "radio_cut.mp4")], check=True)
print("Radio cut ready: outputs/final/radio_cut.mp4")