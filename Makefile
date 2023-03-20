POETRY_HOME := ${HOME}/.local/bin
export PATH := ${POETRY_HOME}:$(PATH)

.PHONY: help install ensure-poetry install-poetry install-precommits

help:
	@echo "TODO write help text"

install:
	@$(MAKE) ensure-poetry
	@$(MAKE) install-precommits

ensure-poetry:
	@if [ "$(shell which poetry)" = "" ]; then \
		$(MAKE) install-poetry; \
	else \
		echo "Found existing Poetry installation at $(shell which poetry)."; \
	fi
	@poetry install

install-poetry:
	@echo "Installing Poetry..."
	curl -sSL https://install.python-poetry.org | python3 -
	# TODO verify installation

install-precommits:
	@poetry run pre-commit autoupdate
	@poetry run pre-commit install --overwrite --install-hooks

test:
	@poetry run pytest --cov --cov-fail-under 100 --cov-report term-missing
