.PHONY: default init dev

default: init dev

init:
	pipenv install --dev

dev:
	FLASK_APP=src/app.py FLASK_ENV=development pipenv run flask run