"""Call Gemini once, log the latency, and list TTS-capable models for your key."""
import os, time
from google import genai
from common import log_run

client = genai.Client(api_key=os.environ["GEMINI_API_KEY"])
t = time.time()
names = [m.name for m in client.models.list()]
log_run("smoke_test", "models.list", {}, time.time() - t, "ok")
print("Models that look like TTS:")
for n in names:
    if "tts" in n.lower():
        print("  ", n)
print("Put one of them (without the 'models/' prefix) in .env as TTS_MODEL=")