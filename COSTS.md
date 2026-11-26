# COSTS.md

All numbers come from `runs.jsonl` (53 logged lines, 25-26 Nov 2026) and the providers' published prices checked on 26 Nov 2026.

## Measured latency per stage
| Stage | Backend | Successful calls | Mean latency | Range | Failed calls |
|---|---|---|---|---|---|
| Narration (per shot) | edge-tts, `en-US-AriaNeural` | 16 (10 first run, 6 regenerated after edits) | 3.5 s | 1.7 - 17.8 s | 0 |
| Narration (attempted) | Gemini TTS, 5 model names | 0 | n/a | 0.1 - 19.5 s | 17 |
| Keyframes (per image) | FLUX.1 schnell, 6 steps, Cloudflare | 15 (10 first run, 5 reseeds/regenerations) | 9.2 s | 4.8 - 17.6 s | 1 (HTTP 400, fixed) |
| Music (per 90 s track) | local numpy synthesiser, CPU | 2 (seeds 7 and 21) | 9.5 s | 8.8 - 10.2 s | 0 |
| Assembly (both formats, full rebuild, 1080p) | FFmpeg + Pillow, my Windows laptop (CPU) | 1 run measured with `time` | 107.5 s (1 min 47 s) | | 0 |

Narration produced 69 s of speech for the current storyboard (sum of `audio_s` for the latest version of each shot).

## GPU minutes
| Stage | GPU minutes |
|---|---|
| Keyframes | 0 on my side (served by Cloudflare) |
| Narration | 0 |
| Music | 0 (CPU) |
| Wan 2.2 / ACE-Step on Kaggle | 0 completed. Notebook sessions only reached install errors, see `FAILURES.md` |

## Money
Measured spend: **$0.00**. All providers were used on free tiers.

## List-price equivalent
| Item | Basis | Estimate |
|---|---|---|
| FLUX.1 schnell on Workers AI | $0.0000528 per 512x512 tile + $0.0001056 per step. 1024x1024 output (4 tiles, measured) at 6 steps = $0.000845 per image (76.8 neurons) | 15 images = **$0.013** |
| Gemini TTS | not used (failed for my key) | $0 |
| edge-tts | Microsoft online voice, no published per-call price | not priced |
| Music, FFmpeg | local CPU | $0 |
| **Total list-price equivalent** | | **about $0.013** |

Check done: the returned keyframes are 1024 x 1024 pixels (measured with Pillow), so the 4-tile assumption holds.

## Free-tier limits I found
- Cloudflare Workers AI: 10,000 neurons per day free, resetting at 00:00 UTC. At 76.8 neurons per image that is about 130 images per day, which agrees with the brief's 50-170 range.
- Gemini TTS: no model visible to my key; the list returned 28 models, none for speech.
- Kaggle: phone verification and the Internet toggle were required before the notebook could reach GitHub.

## Frontier comparison
No access to Omni Flash, Nano Banana or Lyria 3.5 through an organisation key, so no frontier comparison was run.

## What limited me
Not money. The binding limits were: account/model availability (Gemini TTS), setup time on Kaggle (internet, Python 3.13), and the clock.