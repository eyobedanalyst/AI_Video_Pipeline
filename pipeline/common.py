"""Shared helpers: load storyboard, hash for caching, log every model call, retry."""
import json, hashlib, time, datetime
from pathlib import Path
from dotenv import load_dotenv

ROOT = Path(__file__).resolve().parent.parent
load_dotenv(ROOT / ".env")
RUNS = ROOT / "runs.jsonl"


def load_storyboard():
    return json.loads((ROOT / "storyboard.json").read_text(encoding="utf-8"))


def sha(*parts):
    """Fingerprint of the inputs. Same inputs -> same hash -> reuse the cached output."""
    h = hashlib.sha256()
    for p in parts:
        h.update(str(p).encode("utf-8"))
        h.update(b"|")
    return h.hexdigest()[:16]


def log_run(stage, model, params, latency_s, status, cost_usd=0.0, shot=None, error=None):
    """Append ONE line to runs.jsonl for every model call."""
    rec = {
        "ts": datetime.datetime.now(datetime.timezone.utc).isoformat(),
        "stage": stage, "shot": shot, "model": model, "params": params,
        "latency_s": round(latency_s, 3), "cost_usd": cost_usd,
        "status": status, "error": error,
    }
    with open(RUNS, "a", encoding="utf-8") as f:
        f.write(json.dumps(rec, ensure_ascii=False) + "\n")


def retry(fn, tries=3, base_delay=3.0):
    """Call fn(); if it fails, wait and try again (3, 6, 12 seconds...)."""
    for attempt in range(1, tries + 1):
        try:
            return fn()
        except Exception as e:
            if attempt == tries:
                raise
            wait = base_delay * 2 ** (attempt - 1)
            print(f"  attempt {attempt} failed ({e}); retrying in {wait:.0f}s")
            time.sleep(wait)