# ETHICS.md

## 1. Consent (real person: my mother)
The story is based on my mother's real daily life. No photo, video or recording of her was used. Her face and voice do not appear.

**Project title:** Every Mother
**Description:** A 60-90 second AI-assisted short film celebrating the daily work, faith and love of mothers.

I explained the project to my mother. She understands that AI tools create the illustrations, motion, narration and music.

**Consent statement.** My mother confirmed that:
1. She understands the purpose and message of the film.
2. She gives permission for her story and the representation of her daily activities to be used.
3. She understands that AI tools generate the visuals and other creative elements.
4. She understands the film may be shared with family, friends and online audiences.
5. She had the chance to ask questions and raise concerns.
6. Her participation is voluntary and she can withdraw permission before publication.

| Field | Record |
|---|---|
| Mother's name | Amarech Demmse |
| Consent given | Yes, 26 November 2026, before publication |
| Method | Written approval on this form, discussed in person (original kept privately, available on request) |
| Project creator | Eyobed Sebrala |

## 2. Likeness
Every person in the film is an AI-generated illustrated character. No photograph of a real person was used as an input to any model, and no character is meant to be a real likeness. The prompts say only "Ethiopian woman in her 40s", with no names.

## 3. Voice
Narration uses a stock neural voice (Microsoft Edge TTS, `en-US-AriaNeural`). It is not a clone of my mother or any real person. No voice sample was uploaded anywhere.

## 4. Music
The score is composed by code written for this project (`pipeline/music.py`). No third-party music, model or sample is used, so there is no outside licence.

## 5. Licences checked
| Component | Use | Licence / terms |
|---|---|---|
| FLUX.1 schnell (Cloudflare Workers AI) | Keyframes | Apache 2.0 model; Cloudflare's service terms apply to API use |
| edge-tts (Microsoft Edge online voices) | Narration | Uses Microsoft's online service without an official API agreement. Terms for redistributing the audio are not clearly stated, so I treat this as a risk and say so |
| FFmpeg | Assembly | LGPL/GPL, used as a command-line tool, not redistributed |
| Pillow | Text overlays | HPND (permissive) |
| Gemini API | Tried for TTS, failed for my key; not used in the final film | Google AI Studio terms |
| Wan 2.2 (Apache 2.0) | Planned, then skipped for lack of time | Not used |
| ACE-Step 1.5 (MIT) | Tried, failed on Kaggle; not used in the final film | Not used |

## 6. Labelling
- The film ends with an end card: "For every mother." and "Made with AI".
- I switch on the platform's AI-generated content label when posting.
- Provenance metadata or watermarks added by services are left intact.

## 7. Private data
Free endpoints may use what they receive. The text sent to Cloudflare and Microsoft contained no names, addresses or contacts: only generic descriptions and narration lines. My mother's name appears only in this consent record.