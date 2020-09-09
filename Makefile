SHELL := /bin/bash
APPLICATION_NAME="Trade Remedies Public"
APPLICATION_VERSION=1.0
VENV_PATH=~/Envs/traderem-api/bin

# Colour coding for output
COLOUR_NONE=\033[0m
COLOUR_GREEN=\033[32;01m
COLOUR_YELLOW=\033[33;01m


.PHONY: help test
help:
		@echo -e "$(COLOUR_GREEN)|--- $(APPLICATION_NAME) [$(APPLICATION_VERSION)] ---|$(COLOUR_NONE)"
		@echo -e "$(COLOUR_YELLOW)make docker-test$(COLOUR_NONE) : Run the test suite in a dockerized environment"
		@echo -e "$(COLOUR_YELLOW)make docker-cli$(COLOUR_NONE) : Start a terminal session in a dockerized environment for development"
		@echo -e "$(COLOUR_YELLOW)make docker-cli-connect$(COLOUR_NONE) : Start a new terminal session in a running cli container "
		@echo -e "$(COLOUR_YELLOW)make build-docker-cli$(COLOUR_NONE) : Rebuild the dockerized environment for development"

		@echo -e "$(COLOUR_YELLOW)make prettier$(COLOUR_NONE) : Check sass files using prettier"
		@echo -e "$(COLOUR_YELLOW)make flake8$(COLOUR_NONE) : Check python files using flake8"
		@echo -e "$(COLOUR_YELLOW)make black$(COLOUR_NONE) : Check python files using black"

prettier:
		docker run -it --rm -v node_modules:/app/node_modules -v "$(CURDIR):/app" node sh -c 'cd /app && npm i && npx prettier --check "trade_remedies_public/templates/**/*.{scss,js}"'

docker-test:
		docker-compose -f docker-compose-test.yml -p trade-remedies-public-test rm --force
		docker-compose -f docker-compose-test.yml -p trade-remedies-public-test run test-trade-remedies-public
		docker-compose -f docker-compose-test.yml -p trade-remedies-public-test stop
		docker-compose -f docker-compose-test.yml -p trade-remedies-public-test rm --force

docker-cli:
		docker-compose -f docker-compose.yml run --service-ports --rm --name trade-remedies-public-cli cli
		docker-compose -f docker-compose.yml stop

docker-cli-connect:
		docker exec -i -t trade-remedies-public-cli /bin/bash

build-docker-cli:
		docker-compose -f docker-compose.yml build cli

black:
		docker run -it --rm -v pub-requirements:/usr/local -v "$(CURDIR):/app" python sh -c "cd /app && pip install -r requirements-dev.txt && black trade_remedies_public --check"

flake8:
		docker run -it --rm -v pub-requirements:/usr/local -v "$(CURDIR):/app" python sh -c "cd /app && pip install -r requirements-dev.txt && flake8 --count"
