"""Find which TTS model works for YOUR key. Tries each candidate once with a tiny text."""
import os, time, base64
from google import genai
from google.genai import types
from common import log_run

client = genai.Client(api_key=os.environ["GEMINI_API_KEY"])

print("== Models your key can see (names containing 'tts', 'audio' or 'speech') ==")
try:
    all_names = [m.name for m in client.models.list()]
    print(f"(total models visible: {len(all_names)})")
    for n in all_names:
        if any(k in n.lower() for k in ("tts", "audio", "speech")):
            print("  ", n)
except Exception as e:
    print("  could not list models:", str(e)[:150])

CANDIDATES = [
    "gemini-2.5-flash-preview-tts",
    "gemini-2.5-pro-preview-tts",
    "gemini-2.5-flash-tts",
    "gemini-3.1-flash-tts-preview",
    "gemini-3.1-flash-tts",
]
print("\n== Testing each candidate with the older generate_content call ==")
for name in CANDIDATES:
    t = time.time()
    try:
        r = client.models.generate_content(
            model=name,
            contents="Say calmly: Hello, this is a test.",
            config=types.GenerateContentConfig(
                response_modalities=["AUDIO"],
                speech_config=types.SpeechConfig(
                    voice_config=types.VoiceConfig(
                        prebuilt_voice_config=types.PrebuiltVoiceConfig(voice_name="Kore"))),
            ),
        )
        n = len(r.candidates[0].content.parts[0].inline_data.data)
        print(f"  WORKS   {name}  ({n} bytes, {time.time()-t:.1f}s)")
        log_run("find_tts", name, {}, time.time() - t, "ok")
    except Exception as e:
        print(f"  failed  {name}: {str(e)[:110]}")
        log_run("find_tts", name, {}, time.time() - t, "error", error=str(e)[:200])