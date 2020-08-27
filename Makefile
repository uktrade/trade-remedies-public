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


docker-code-style:
		docker-compose -f docker-compose-test.yml -p trade-remedies-public-code rm --force
		docker-compose -f docker-compose-test.yml -p trade-remedies-public-code run test-trade-remedies-code
		docker-compose -f docker-compose-test.yml -p trade-remedies-public-code stop
		docker-compose -f docker-compose-test.yml -p trade-remedies-public-code rm --force

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
