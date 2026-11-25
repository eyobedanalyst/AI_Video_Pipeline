"""Stage 0: check storyboard.json against the schema before anything runs."""
import json, sys
from jsonschema import Draft7Validator
from common import ROOT, load_storyboard

schema = json.loads((ROOT / "schema" / "storyboard.schema.json").read_text(encoding="utf-8"))
board = load_storyboard()
errors = sorted(Draft7Validator(schema).iter_errors(board), key=lambda e: list(e.path))
if errors:
    for e in errors:
        print("INVALID:", "/".join(map(str, e.path)) or "(root)", "->", e.message)
    sys.exit(1)

words = sum(len(s["narration"].split()) for s in board["shots"])
total = sum(s["duration_sec"] for s in board["shots"]) + board["end_card"]["duration_sec"]
print(f"OK: {len(board['shots'])} shots, {words} narration words, planned length {total}s")