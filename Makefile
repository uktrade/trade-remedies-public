APPLICATION_NAME="Trade Remedies Public"

# Colour coding for output
COLOUR_NONE=\033[0m
COLOUR_GREEN=\033[32;01m
COLOUR_YELLOW=\033[33;01m


.PHONY: help test
help:
		@echo -e "$(COLOUR_GREEN)|--- $(APPLICATION_NAME) [$(APPLICATION_VERSION)] ---|$(COLOUR_NONE)"
		@echo -e "$(COLOUR_YELLOW)make all-requirements$(COLOUR_NONE) : Generate all requirements (requires local pip-compile)"
		@echo -e "$(COLOUR_YELLOW)make dev-requirements$(COLOUR_NONE) : Generate dev requirements (requires local pip-compile)"
		@echo -e "$(COLOUR_YELLOW)make prod-requirements$(COLOUR_NONE) : Generate prod requirements (requires local pip-compile)"

all-requirements:
	pip-compile --output-file requirements/base.txt requirements.in/base.in
	pip-compile --output-file requirements/dev.txt requirements.in/dev.in
	pip-compile --output-file requirements/prod.txt requirements.in/prod.in

dev-requirements:
	pip-compile --output-file requirements/base.txt requirements.in/base.in
	pip-compile --output-file requirements/dev.txt requirements.in/dev.in

prod-requirements:
	pip-compile --output-file requirements/base.txt requirements.in/base.in
	pip-compile --output-file requirements/prod.txt requirements.in/prod.in