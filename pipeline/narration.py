"""Stage: narration. One WAV per shot. Cached by hash, retried, logged."""
import os, sys, json, time, wave, base64, argparse
from google import genai
from google.genai import types
from common import ROOT, load_storyboard, sha, log_run, retry

OUT = ROOT / "outputs" / "narration"
OUT.mkdir(parents=True, exist_ok=True)
RATE = 24000  # Gemini TTS returns 24 kHz, 16-bit, mono PCM

ap = argparse.ArgumentParser()
ap.add_argument("--shot", help="only this shot id, e.g. s03")
ap.add_argument("--force", action="store_true", help="ignore cache")
args = ap.parse_args()

board = load_storyboard()
provider = os.environ.get("TTS_PROVIDER") or board["narration"].get("provider", "gemini")
if provider == "edge":
    model = "edge-tts"
    voice = board["narration"].get("edge_voice", "en-US-AriaNeural")
    rate = board["narration"].get("edge_rate", "+0%")
else:
    model = os.environ.get("TTS_MODEL") or sys.exit("Set TTS_MODEL in .env")
    voice = board["narration"]["voice"]
style = board["narration"]["style_instruction"]
client = genai.Client(api_key=os.environ["GEMINI_API_KEY"]) if provider != "edge" else None
timings_path = OUT / "timings.json"
timings = json.loads(timings_path.read_text()) if timings_path.exists() else {}


def _prompt(text):
    # Docs pattern: "Say <style>: <text>"
    return f"{style.rstrip('. ')}: {text}"


def synth_interactions(text):
    """New API (used by gemini-3.1-flash-tts-preview)."""
    it = client.interactions.create(
        model=model,
        input=_prompt(text),
        response_format={"type": "audio"},
        generation_config={"speech_config": [{"voice": voice}]},
    )
    data = it.output_audio.data
    return base64.b64decode(data) if isinstance(data, str) else data


def synth_generate_content(text):
    """Older API (used by gemini-2.5-flash-preview-tts)."""
    resp = client.models.generate_content(
        model=model,
        contents=_prompt(text),
        config=types.GenerateContentConfig(
            response_modalities=["AUDIO"],
            speech_config=types.SpeechConfig(
                voice_config=types.VoiceConfig(
                    prebuilt_voice_config=types.PrebuiltVoiceConfig(voice_name=voice)
                )
            ),
        ),
    )
    return resp.candidates[0].content.parts[0].inline_data.data


def synth_edge(text):
    """Free Microsoft neural voices via edge-tts. Returns 24 kHz 16-bit mono PCM."""
    import asyncio, subprocess, tempfile
    import edge_tts

    async def go(path):
        await edge_tts.Communicate(text, voice, rate=rate).save(path)

    with tempfile.TemporaryDirectory() as d:
        mp3 = os.path.join(d, "t.mp3")
        asyncio.run(go(mp3))
        return subprocess.run(["ffmpeg", "-v", "error", "-i", mp3, "-f", "s16le", "-ar", "24000", "-ac", "1", "-"],
                              capture_output=True, check=True).stdout


def synth(text):
    if provider == "edge":
        return synth_edge(text)
    # Pick the API by model name; fall back to the other one if it errors.
    first, second = (synth_interactions, synth_generate_content) if "3." in model else (synth_generate_content, synth_interactions)
    try:
        return first(text)
    except Exception as e:
        print(f"  {first.__name__} failed: {str(e)[:120]} -> trying {second.__name__}")
        return second(text)


for shot in board["shots"]:
    if args.shot and shot["id"] != args.shot:
        continue
    wav, hfile = OUT / f"{shot['id']}.wav", OUT / f"{shot['id']}.hash"
    h = sha(model, voice, style, shot["narration"])
    if not args.force and wav.exists() and hfile.exists() and hfile.read_text() == h:
        print(f"{shot['id']}: cached, skipped")
        continue
    t = time.time()
    try:
        pcm = retry(lambda: synth(shot["narration"]))
    except Exception as e:
        log_run("narration", model, {"voice": voice}, time.time() - t, "error", shot=shot["id"], error=str(e))
        print(f"{shot['id']}: FAILED ({e})")
        continue
    lat = time.time() - t
    with wave.open(str(wav), "wb") as w:
        w.setnchannels(1); w.setsampwidth(2); w.setframerate(RATE); w.writeframes(pcm)
    hfile.write_text(h)
    dur = len(pcm) / (RATE * 2)
    timings[shot["id"]] = round(dur, 2)
    log_run("narration", model, {"voice": voice, "chars": len(shot["narration"]), "audio_s": round(dur, 2)},
            lat, "ok", shot=shot["id"])
    print(f"{shot['id']}: generated {dur:.1f}s of speech in {lat:.1f}s")

timings_path.write_text(json.dumps(timings, indent=2))
print("Narration seconds per shot saved to outputs/narration/timings.json")