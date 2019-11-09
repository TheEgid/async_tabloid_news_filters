
COMMAND = docker-compose run --rm web /bin/bash -c

build:
	docker-compose build

run:
	docker-compose up -d

run_with_logs:
	docker-compose up

test:
	$(COMMAND) "pytest"

test_server:
	$(COMMAND) "pytest -m server"

test_adapters:
	$(COMMAND) "pytest -m adapters_inosmi_ru"

test_tools:
	$(COMMAND) "pytest -m text_tools"