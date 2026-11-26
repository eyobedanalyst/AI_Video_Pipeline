# EXPERIMENTS.md

Format: hypothesis, change, result. One change at a time. Results marked **FILL** need my own observation.

## E1. Is a free API voice available for Amharic/English narration?
- **Hypothesis:** Gemini TTS will give natural narration on the free tier.
- **Change:** tried 5 Gemini TTS model names and two API call styles, then swapped provider to edge-tts.
- **Result:** Gemini 0 of 17 calls succeeded (400 and 404); edge-tts 16 of 16 succeeded, mean 3.5 s per shot. I kept edge-tts. Evidence: `runs.jsonl`, `FAILURES.md` F1.

## E2. Shortening narration after the user tests
- **Hypothesis:** shorter lines for s01, s05, s06 fix "slow opening", "church part too long", "unclear transition".
- **Change:** three rewrites of each line. Spoken length from `runs.jsonl`: s01 8.35 s, then 4.97 s, then 4.30 s; s05 10.68 s, 8.74 s, 5.02 s; s06 6.17 s, 7.85 s, 5.74 s (s06 got longer first because I added the bridge to the church scene, then shorter).
- **Result:** timing measured. Audience reaction to the third version: **FILL** after a third listener (see `DESIGN.md`).

## E3. Does a fixed seed reproduce the same keyframe?
- **Hypothesis:** same prompt, steps and seed give the same image from FLUX.1 schnell on Cloudflare.
- **Change:** regenerated s03 twice with `--force`, same prompt, seed 44, and compared file hashes (md5). Earlier, s03 had also been generated four times with seed 44 (see `runs.jsonl`).
- **Result:** the hashes differ (`112e48b3...` vs `a17f8db9...`), and the console printed "seed not accepted by this model; retrying without seed". The REST endpoint rejected my `seed` field, so every image is a fresh random draw. A seed in `storyboard.json` is recorded but does **not** make the picture reproducible. This explains why consistency was weak and why I reseeded by regenerating until a shot looked right. `keyframes.py` now tries the seed as a number, then as text, then without it, and logs `seed_applied` in `runs.jsonl` so the log tells the truth.
- **Consequence:** reproducibility of keyframes comes from the saved JPEG files and the hash cache, not from the seed. The README says this.

## E4. Latency of keyframes
- **Hypothesis:** 6 steps give roughly 5-10 s per image.
- **Change:** 15 successful calls at 6 steps.
- **Result:** mean 9.2 s, min 4.8 s, max 17.6 s. Variation is mostly queueing, not the prompt (s06: 17.5 s first, 8.7 s on retry with the same prompt).

## E5. Score: three seeds of a local synthesiser
- **Hypothesis:** a quiet arpeggio over a pad leaves room for the voice.
- **Change:** seeds 7 and 21 (and 33 if run), same settings.
- **Result:** generation took 10.2 s (seed 7) and 8.8 s (seed 21) on CPU. I chose seed 7 (`score.wav`) because it stayed quiet under the narration and matched the mood. Viewers in user test 2 said the music strengthened the message.

## E6. Subtitle line length in vertical frames
- **Hypothesis:** 40 characters per line fit the 9:16 safe area.
- **Change:** rendered a test frame at 40, then 28 characters per line.
- **Result:** 40 reached the screen edges; 28 stayed inside with a margin. Kept 28 for vertical.

## E7 - E10 (run these, each takes about 10 minutes)
Add results as you run them.
- **E7. Narration rate.** `edge_rate` -8% vs +0%: which do 3 listeners prefer?
- **E8. Style block.** Same shot and seed with and without `style_block`: does the look stay consistent?
- **E9. Steps.** FLUX steps 4 vs 6 vs 8 for one shot: latency and visible quality.
- **E10. Ducking.** `sidechaincompress` threshold 0.02 vs 0.05: is the voice clearer?