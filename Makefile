POETRY_HOME := ${HOME}/.local/bin
export PATH := ${POETRY_HOME}:$(PATH)

.PHONY: help
help:
	@echo "TODO write help text"

install:
	@$(MAKE) ensure-poetry

ensure-poetry:
	@if [ "$(shell which poetry)" = "" ]; then \
		$(MAKE) install-poetry; \
	else \
		echo "Found existing Poetry installation at $(shell which poetry)."; \
	fi

install-poetry:
	@echo "Installing Poetry..."
	curl -sSL https://install.python-poetry.org | python3 -
	# TODO verify installation

install-precommits:
	@poetry run pre-commit install
	@pre-commit autoupdate
