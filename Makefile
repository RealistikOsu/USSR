#!/usr/bin/env make

build:
	docker build -t score-service:latest .

run:
	docker run --network=host --env-file=.env -it score-service:latest

run-bg:
	docker run --network=host --env-file=.env -d score-service:latest
