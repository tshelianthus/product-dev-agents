.PHONY: check

check:
	python3 scripts/check_contracts.py
	python3 scripts/check_run_output.py examples/run-output.valid.json
