.PHONY: install dev preflight accept up verify
PY ?= .venv/bin/python

install:
	$(PY) -m pip install -q -e .

dev:  ## local-engine run (no docker) — dev only, says so loudly
	bash scripts/dev.sh

up:   ## real durable stack (Temporal+PG+Redis+LiteLLM)
	bash deploy/scripts/setup.sh

verify:
	bash deploy/scripts/verify.sh

preflight:  ## E1: live-chain harness against :8000 — "done = preflight passed"
	$(PY) deploy/scripts/preflight.py

accept:  ## Phase 0 kill→resume acceptance (spawns its own gateway+worker)
	DEMO_STEP_SECONDS=$${DEMO_STEP_SECONDS:-15} $(PY) tests/acceptance/phase0_resume.py
