PY=python

validate:
	$(PY) pipeline/validate.py

narration: validate
	$(PY) pipeline/narration.py

keyframes: validate
	$(PY) pipeline/keyframes.py

radio: narration
	$(PY) pipeline/radio_cut.py

draft: keyframes narration
	$(PY) pipeline/assemble.py --draft

# One command for the whole film: make film
film: validate keyframes narration
	$(PY) pipeline/assemble.py