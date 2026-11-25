"""Stage: keyframes. One image per shot with FLUX.1 schnell on Cloudflare Workers AI.
Cached by hash of (model, prompt, steps, seed). Retried. Every call logged to runs.jsonl."""
import os, sys, base64, time, argparse
import requests
from common import ROOT, load_storyboard, sha, log_run, retry

OUT = ROOT / "outputs" / "keyframes"
OUT.mkdir(parents=True, exist_ok=True)
MODEL = "@cf/black-forest-labs/flux-1-schnell"
STEPS = 6  # schnell max is 8; 4 is default

ap = argparse.ArgumentParser()
ap.add_argument("--shot", help="only this shot id, e.g. s03")
ap.add_argument("--force", action="store_true", help="ignore cache")
ap.add_argument("--seed", type=int, help="override seed (for experiments)")
args = ap.parse_args()

acct = os.environ.get("CLOUDFLARE_ACCOUNT_ID") or sys.exit("Set CLOUDFLARE_ACCOUNT_ID in .env")
token = os.environ.get("CLOUDFLARE_API_TOKEN") or sys.exit("Set CLOUDFLARE_API_TOKEN in .env")
URL = f"https://api.cloudflare.com/client/v4/accounts/{acct}/ai/run/{MODEL}"

board = load_storyboard()
style, char = board["style_block"], board["character"]["description"]


def build_prompt(shot):
    # Same style block + same character text in EVERY prompt -> less drift between shots.
    return f"{shot['keyframe_prompt']}. The woman: {char}. Style: {style}."[:2000]


def generate(prompt, seed, use_seed=True):
    payload = {"prompt": prompt, "steps": STEPS}
    if use_seed:
        payload["seed"] = seed
    r = requests.post(URL, headers={"Authorization": f"Bearer {token}"}, json=payload, timeout=120)
    if not r.ok:
        # Show Cloudflare's own explanation instead of just "400 Bad Request"
        raise RuntimeError(f"HTTP {r.status_code}: {r.text[:400]}")
    body = r.json()
    result = body.get("result", body)
    return base64.b64decode(result["image"])


def generate_with_fallback(prompt, seed):
    try:
        return generate(prompt, seed, use_seed=True)
    except RuntimeError as e:
        if "seed" in str(e).lower():
            print("  seed not accepted by this model; retrying without seed")
            return generate(prompt, seed, use_seed=False)
        raise


for i, shot in enumerate(board["shots"]):
    if args.shot and shot["id"] != args.shot:
        continue
    seed = args.seed if args.seed is not None else shot.get("seed", board["global_seed"] + i)
    prompt = build_prompt(shot)
    img, hfile = OUT / f"{shot['id']}.jpg", OUT / f"{shot['id']}.hash"
    h = sha(MODEL, prompt, STEPS, seed)
    if not args.force and img.exists() and hfile.exists() and hfile.read_text() == h:
        print(f"{shot['id']}: cached, skipped")
        continue
    t = time.time()
    try:
        data = retry(lambda: generate_with_fallback(prompt, seed))
    except Exception as e:
        log_run("keyframes", MODEL, {"seed": seed, "steps": STEPS}, time.time() - t, "error",
                shot=shot["id"], error=str(e)[:300])
        print(f"{shot['id']}: FAILED ({str(e)[:200]})")
        continue
    img.write_bytes(data)
    hfile.write_text(h)
    lat = time.time() - t
    log_run("keyframes", MODEL, {"seed": seed, "steps": STEPS, "prompt_chars": len(prompt)}, lat, "ok", shot=shot["id"])
    print(f"{shot['id']}: generated in {lat:.1f}s (seed {seed})")