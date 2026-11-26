# ARCHITECTURE.md

## Shape
```
storyboard.json --(validate)--> keyframes --> narration --> music --> assemble --> two MP4s
   the contract      schema        FLUX        edge-tts     synth      FFmpeg
```
Each stage is one script in `pipeline/`. A stage reads only `storyboard.json` and the outputs of earlier stages, and writes only into `outputs/`. Stages do not import each other; they share `pipeline/common.py`.

## The contract: storyboard.json
Defines audience, intent, style block, character description, narration settings, music settings, 10 shots, end card and export targets.
Every shot carries `id`, `duration_sec`, `reason` (why the shot exists), `keyframe_prompt`, `motion_prompt`, `camera`, `narration`, optional `time_label`, `sfx`, `seed`.
`schema/storyboard.schema.json` checks types, required fields, 8-12 shots, allowed camera values. `validate.py` runs first in every `make` target and stops the run on error.
Prompts and seeds live in the contract, not in code, so any run can be reproduced and explained.

## Stages
| Stage | Reads | Writes | Backend |
|---|---|---|---|
| validate | storyboard, schema | prints word count and planned length | jsonschema |
| keyframes | style block, character, `keyframe_prompt`, seed | `outputs/keyframes/<id>.jpg` | FLUX.1 schnell on Cloudflare Workers AI |
| narration | `narration`, voice settings | `outputs/narration/<id>.wav`, `timings.json` | edge-tts (Gemini TTS optional) |
| music | `music` block | `outputs/music/score.wav` | local numpy synthesiser |
| assemble | all of the above | `outputs/clips/*`, `outputs/final/*.mp4` | FFmpeg + Pillow overlays |

## Caching
`keyframes` and `narration` compute `sha256(model | prompt | parameters | seed)` and store it in `<id>.hash` next to the output.
If the file exists and the hash matches, the shot is skipped (`cached, skipped`). Changing one narration line regenerates one WAV.
`assemble` caches each per-shot clip by a hash of the keyframe bytes, narration text, camera, label, duration, narration length and frame size, so a change rebuilds one clip, then re-concatenates.
`--force` ignores the cache for experiments.

## Failure handling
- **Retry with backoff** (`common.retry`): 3 tries, 3 s then 6 s, for every network call.
- **Log every call, success or failure,** to `runs.jsonl` with model, parameters, seed, latency, cost, status and error text. Failures were as useful as successes when writing `FAILURES.md`.
- **Fallbacks by design:** narration has two providers selected in the storyboard; assemble uses a Ken Burns move when no video clip exists; a failed shot does not stop the others.
- **Secrets** are read from `.env` and never written to logs.
- **Timing follows the voice:** shot length is `max(planned, narration + 0.9 s)`, so the voice is never cut off.

## Assembly details
- Subtitles, time labels and the end card are drawn as PNG overlays (Pillow), because AI image models garble text and FFmpeg font handling differs per OS.
- Vertical subtitle lines are 28 characters, horizontal 40, kept in the phone safe area.
- Audio: per-shot narration padded to shot length, concatenated, score looped and trimmed, ducked with `sidechaincompress` (threshold 0.02, ratio 6, attack 300 ms, release 1500 ms), mixed, `loudnorm` to -14 LUFS, true peak -1 dB.
- Keyframes are square (the Cloudflare endpoint exposes no width/height), so the subject is centred and each image is centre-cropped to 9:16 and 16:9.

## Design decisions worth explaining
1. **JSON contract first,** so a change to one field only re-runs the stage that reads it.
2. **Provider swap without code changes** (Gemini TTS to edge-tts) because the provider is a field in the storyboard.
3. **Deterministic assembly:** FFmpeg is not AI; same inputs give the same film.
4. **Optional stages degrade gracefully:** video and score are optional inputs to assembly.