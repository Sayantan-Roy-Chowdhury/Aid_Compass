.PHONY: setup test validate web run gap-report

setup:
	python -m venv .venv
	.venv/bin/pip install -e ".[dev]"

test:
	pytest

validate:
	python scripts/validate_project.py

web:
	adk web .

run:
	adk run aidcompass

gap-report:
	python scripts/build_gap_report.py
