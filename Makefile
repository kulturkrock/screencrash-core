.PHONY: default init dev

default: init dev

init:
	pipenv install --dev

dev:
	pipenv run watchmedo auto-restart \
		--patterns="*.py" \
		--recursive \
		python -- src/main.py