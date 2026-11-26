# Every Mother: an AI-made heritage short, built by a pipeline

A 60-90 second film about my mother's ordinary day, told in first person, with English narration and subtitles,
an original score ducked under the voice, an AI end card, and exports in 9:16 and 16:9.
All characters are AI-generated illustrations. See `ETHICS.md`.

**The film is the output. The pipeline is the product.** One file, `storyboard.json`, is the contract between all stages.

## Run it (one command)
```bash
git clone <this repo> && cd AI_Video_Pipeline
pip install -r requirements.txt          # Python 3.10+ and FFmpeg on PATH
cp .env.example .env                      # then fill in the two Cloudflare values
python run.py                             # validate -> keyframes -> narration -> music -> assemble
```
Works on Windows, macOS and Linux. `make film` does the same where `make` is installed.
Options: `python run.py --draft` (fast, half resolution) and `python run.py --skip-keyframes` (reuse pictures).

Result: `outputs/final/every_mother_vertical.mp4` and `outputs/final/every_mother_horizontal.mp4`.

### Keys needed
| Key | For | Where |
|---|---|---|
| `CLOUDFLARE_ACCOUNT_ID`, `CLOUDFLARE_API_TOKEN` | Keyframes (FLUX.1 schnell, Workers AI) | Cloudflare dashboard, free |
| none | Narration (edge-tts), music (local synth), assembly (FFmpeg) | - |
| `GEMINI_API_KEY`, `TTS_MODEL` | Optional: Gemini TTS provider. It failed for my key, see `FAILURES.md` | Google AI Studio |

Secrets live only in `.env`, which is in `.gitignore`.

## Change one shot and regenerate only that shot
Edit a narration line or keyframe prompt in `storyboard.json`, then run `make film` again.
Every stage hashes its inputs; unchanged shots print `cached, skipped`. The new model calls appear as new lines in `runs.jsonl`.
Force one shot: `python pipeline/keyframes.py --shot s05 --force --seed 777`.

## What is in the repo
| Path | Purpose |
|---|---|
| `storyboard.json` | The contract: shots, durations, prompts, narration, camera, music cues, export |
| `schema/storyboard.schema.json` | JSON Schema, validated before every run |
| `pipeline/` | `validate`, `keyframes`, `narration`, `music`, `assemble`, `radio_cut`, plus `common.py` (hashing, retry, logging) |
| `runs.jsonl` | One line per model call: stage, model, params, seed, latency, cost, status |
| `outputs/` | Keyframes, narration, music, clips, final films |
| `DESIGN.md` `ARCHITECTURE.md` `EXPERIMENTS.md` `FAILURES.md` `COSTS.md` `ETHICS.md` | Process evidence |

## Honest limits
- **No AI video.** Wan 2.2 on Kaggle was not attempted to completion (time and setup blockers). Motion is a Ken Burns pan/zoom over AI keyframes made by FFmpeg. `assemble.py` already prefers `outputs/shots/<id>.mp4` if a video clip exists.
- **Score is composed by code** (`pipeline/music.py`), not ACE-Step. ACE-Step on Kaggle failed (see `FAILURES.md`).
- **Seeds are not applied by the Cloudflare endpoint** (see `EXPERIMENTS.md` E3): reruns with `--force` give a new image. Reproducibility comes from the saved keyframes and the hash cache.
- **Character consistency** comes from repeating one character description and style block in every prompt. FLUX.1 schnell takes no reference image.
- **Narration voice** is edge-tts (Microsoft online voices), not Gemini TTS.

## Cost
Measured cost of the full run: $0. List-price equivalent about $0.013. Details in `COSTS.md`.