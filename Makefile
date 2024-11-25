SHELL := /bin/bash
APPLICATION_NAME="Trade Remedies Public"

# Colour coding for output
COLOUR_NONE=\033[0m
COLOUR_GREEN=\033[32;01m
COLOUR_YELLOW=\033[33;01m

ifeq ($(APPLICATION_VERSION),)
APPLICATION_VERSION := "no version"
endif

.PHONY: help test
help:
	@echo -e "$(COLOUR_GREEN)|--- $(APPLICATION_NAME) [$(APPLICATION_VERSION)] ---|$(COLOUR_NONE)"
	@echo -e "$(COLOUR_YELLOW)make all-requirements$(COLOUR_NONE) : Generate all requirements (preferred usage - builds on container)"
	@echo -e "$(COLOUR_YELLOW)make dev-requirements$(COLOUR_NONE) : Generate dev requirements (requires local pip-compile)"
	@echo -e "$(COLOUR_YELLOW)make prod-requirements$(COLOUR_NONE) : Generate prod requirements (requires local pip-compile)"

all-requirements:
	poetry lock
	poetry export --without-hashes -f requirements.txt -o requirements.txt
	poetry export --with dev --without-hashes -f requirements.txt -o requirements-dev.txt
	pip install -r requirements-dev.txt
