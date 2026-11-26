# FAILURES.md

Each entry: what broke, what I tried, what fixed it or what I did instead.

## F1. Gemini TTS: 400 INVALID_ARGUMENT, then no TTS model visible (25 Nov)
- **Broke:** `narration.py` with `gemini-3.1-flash-tts-preview` returned `Unknown name "speechConfig" at 'generation_config'`. A later try with the newer "interactions" call returned `404 model not found`.
- **Tried:** wrote `find_tts.py` to test 5 model names (`gemini-2.5-flash-preview-tts`, `gemini-2.5-pro-preview-tts`, `gemini-2.5-flash-tts`, `gemini-3.1-flash-tts-preview`, `gemini-3.1-flash-tts`) three times; upgraded `google-genai`; read the live docs; added an interactions-API call with fallback. 17 failed calls are in `runs.jsonl`.
- **Found:** my key could list 28 models and none was a speech model, so TTS is not available to this key.
- **Fix:** made the narration provider a field in `storyboard.json` and added `edge-tts` (free, no key). Narration worked on the first run (8.35 s for s01).
- **Lesson:** the brief said tools would be out of date; checking the account's real model list is faster than guessing names.

## F2. Cloudflare keyframes: HTTP 400 with no explanation (25 Nov)
- **Broke:** first call for s01 failed with `400 Bad Request` after 16.5 s; my script hid the response body.
- **Tried:** printed Cloudflare's error text; added a fallback that retries without `seed`.
- **Result:** the next call succeeded (4.8 s). Later runs printed "seed not accepted by this model; retrying without seed", so the 400 was most likely the `seed` field. Consequence: seeds are not applied, see `EXPERIMENTS.md` E3. Lesson: always log the response body, and log whether a parameter was really applied.

## F3. Silent script (25 Nov)
- **Broke:** `python pipeline/keyframes.py --shot s01` printed nothing.
- **Cause:** the file in `pipeline/` was an empty placeholder from my repo skeleton, not the new code.
- **Fix:** replaced the file; checked with `wc -l`. Lesson: a script that prints nothing is usually an empty file.

## F4. Kaggle: no internet (25-26 Nov)
- **Broke:** `git clone` failed with `Could not resolve host: github.com`.
- **Fix:** enabled Internet in the notebook session options (needs a phone-verified account).

## F5. Kaggle: ACE-Step needs Python <3.13 (25-26 Nov)
- **Broke:** `pip install -e .` failed: `Package 'ace-step' requires a different Python: 3.13 not in '<3.13,>=3.11'`.
- **Tried:** switching to `uv sync` and running generation as scripts.
- **Outcome:** still blocked and costing hours. A hosted ACE-Step web demo produced a track but offered no download.
- **Fix:** wrote `pipeline/music.py`, a local numpy synthesiser (soft piano arpeggio over a pad, 68 BPM, D major) that is original, free and reproducible. Two seeds logged. It sounds simpler than ACE-Step. I say so openly in the README.

## F6. Wan 2.2 image-to-video skipped (26 Nov)
- **Decision:** with the deadline hours away and two Kaggle blockers already, I skipped AI video. Motion is a Ken Burns pan/zoom made by FFmpeg, the fallback the brief names. `assemble.py` will use `outputs/shots/<id>.mp4` automatically if a clip is provided later.
- **Cost of the decision:** the film has less motion. **Benefit:** the required stages were finished and documented.

## F7. Film too long (26 Nov)
- **Broke:** the draft film planned 92.06 s, above the 90 s limit (`assemble.py` printed a warning).
- **Cause:** the voice sets the shot length (`narration + 0.9 s`), and the earlier narration for s01, s05, s06 was longer.
- **Fix:** shortened those three lines after user test 2 (see `DESIGN.md`); the planned length is now 84.79 s.

## F8. Subtitles too wide in vertical (26 Nov)
- **Broke:** 40-character lines touched the edges of the 9:16 frame in a test render.
- **Fix:** 28 characters per line for vertical, 40 for horizontal.

## F9. git push failed with HTTP 408 (26 Nov)
- **Broke:** pushing a 19.8 MB commit (two 90-second WAV scores) disconnected: `RPC failed; HTTP 408`.
- **Cause:** large binary files on a slow connection.
- **Fix:** stopped committing generated media that the pipeline can recreate (`outputs/music/*.wav`, `outputs/final/`, `outputs/clips/`, `outputs/tmp/`), added them to `.gitignore`, and hosted the final MP4s outside the repo.