"""One command for the whole film, on any OS (Windows, macOS, Linux). No `make` needed.

    python run.py            full quality, both aspect ratios
    python run.py --draft    half resolution, fast check
    python run.py --skip-keyframes   reuse existing pictures (e.g. to save the free daily quota)

Stages: validate -> keyframes -> narration -> music -> assemble.
Each stage caches by hash, so unchanged shots are skipped."""
import subprocess, sys, time
from pathlib import Path

ROOT = Path(__file__).resolve().parent
args = sys.argv[1:]
draft = "--draft" in args
stages = [("validate", []), ("keyframes", []), ("narration", []), ("music", []),
          ("assemble", ["--draft"] if draft else [])]
if "--skip-keyframes" in args:
    stages = [s for s in stages if s[0] != "keyframes"]

t_all = time.time()
for name, extra in stages:
    print(f"\n=== {name} ===", flush=True)
    t = time.time()
    r = subprocess.run([sys.executable, str(ROOT / "pipeline" / f"{name}.py"), *extra], cwd=ROOT)
    if r.returncode:
        sys.exit(f"\nStage '{name}' failed (exit {r.returncode}). Fix it and run again; finished stages are cached.")
    print(f"--- {name} done in {time.time() - t:.1f}s")
print(f"\nAll stages done in {time.time() - t_all:.0f}s. Films are in outputs/final/")