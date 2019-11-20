COMMAND = docker-compose run --rm web /bin/bash -c

build:
	docker-compose build

run:
	docker-compose up -d

run_logs:
	docker-compose up

test:
	$(COMMAND) "pytest"