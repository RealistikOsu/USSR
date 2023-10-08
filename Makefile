#!/usr/bin/env make

build:
	docker build -t score-service:latest .

run:
	docker run -p ${APP_PORT}:${APP_PORT} -it score-service:latest

run-bg:
	docker run -p ${APP_PORT}:${APP_PORT} -d score-service:latest
