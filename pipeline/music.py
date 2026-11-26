"""Music stage: composes an original, quiet piano-and-pad score locally.
No GPU, no internet, no API key. Same seed -> same file (reproducible).
Usage: python pipeline/music.py [--seconds 90] [--seed 7] [--out outputs/music/score.wav]
"""
import argparse, json, os, time, wave
import numpy as np

SR = 44100
BPM = 68
# Chords in D major: D, Bm, G, A  (I - vi - IV - V). MIDI notes.
CHORDS = [[50, 54, 57, 62], [47, 54, 59, 62], [43, 50, 55, 59], [45, 52, 57, 61]]

def hz(m): return 440.0 * 2 ** ((m - 69) / 12)

def piano_note(freq, dur, rng):
    t = np.arange(int(SR * dur)) / SR
    s = np.zeros_like(t)
    for k, a in enumerate([1.0, 0.5, 0.25, 0.12, 0.06], start=1):
        s += a * np.sin(2 * np.pi * freq * k * t + rng.uniform(0, 6.28))
    env = np.minimum(t / 0.01, 1.0) * np.exp(-t * 1.6)
    return s * env

def pad_note(freq, dur):
    t = np.arange(int(SR * dur)) / SR
    s = sum(np.sin(2 * np.pi * freq * (1 + d) * t) for d in (-0.002, 0, 0.002))
    s += 0.4 * np.sin(2 * np.pi * freq * 2 * t)
    a = np.minimum(t / 1.2, 1.0)
    r = np.minimum((dur - t) / 1.5, 1.0)
    return s * a * r

def reverb(x, rng):
    n = int(SR * 2.2)
    ir = rng.standard_normal(n) * np.exp(-np.arange(n) / (SR * 0.6))
    L = len(x) + n
    X = np.fft.rfft(x, L) * np.fft.rfft(ir, L)
    y = np.fft.irfft(X, L)[: len(x)]
    return 0.7 * x + 0.5 * y / (np.max(np.abs(y)) + 1e-9) * np.max(np.abs(x))

def compose(seconds, seed):
    rng = np.random.default_rng(seed)
    beat = 60.0 / BPM
    bar = 4 * beat
    n = int(SR * (seconds + 4))
    pad = np.zeros(n); pno = np.zeros(n)
    bars = int(seconds / bar) + 1
    for b in range(bars):
        chord = CHORDS[b % 4]
        i0 = int(b * bar * SR)
        for m in chord:
            p = pad_note(hz(m), bar + 1.0) * 0.10
            pad[i0:i0 + len(p)] += p[: n - i0]
        # soft arpeggio, eighth notes, gentle and sparse (no strong lead melody)
        pattern = [0, 2, 1, 3, 2, 1, 3, 2]
        for k, idx in enumerate(pattern):
            if rng.random() < 0.2:
                continue
            m = chord[idx] + (12 if idx >= 2 else 0)
            i = i0 + int(k * beat / 2 * SR)
            note = piano_note(hz(m), 2.5, rng) * rng.uniform(0.10, 0.16)
            pno[i:i + len(note)] += note[: n - i]
    mix = reverb(pad + pno, rng)[: int(SR * seconds)]
    t = np.arange(len(mix)) / SR
    mix *= np.minimum(t / 3.0, 1.0) * np.minimum((seconds - t) / 4.0, 1.0)
    mix = mix / np.max(np.abs(mix)) * 0.5
    return mix

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--seconds", type=float, default=90)
    ap.add_argument("--seed", type=int, default=7)
    ap.add_argument("--out", default="outputs/music/score.wav")
    a = ap.parse_args()
    os.makedirs(os.path.dirname(a.out), exist_ok=True)
    t0 = time.time()
    x = compose(a.seconds, a.seed)
    pcm = (x * 32767).astype(np.int16)
    with wave.open(a.out, "wb") as w:
        w.setnchannels(1); w.setsampwidth(2); w.setframerate(SR)
        w.writeframes(pcm.tobytes())
    lat = round(time.time() - t0, 2)
    with open("runs.jsonl", "a") as f:
        f.write(json.dumps({"stage": "music", "model": "local-synth(numpy)",
            "params": {"seconds": a.seconds, "bpm": BPM, "key": "D major", "seed": a.seed},
            "seed": a.seed, "latency_s": lat, "cost_usd": 0.0, "output": a.out}) + "\n")
    print(f"saved {a.out} ({a.seconds}s, seed {a.seed}) in {lat}s")

if __name__ == "__main__":
    main()