# Makefile for Airflow Embedded Dashboards

# Variables
PROJECT_NAME := airflow-embedash
COMPOSE_FILE := dev/docker-compose.yaml
DOCKER_COMPOSE := docker compose -f $(COMPOSE_FILE)

# Default target
.PHONY: help
help:
	@echo "Airflow Embeded Dashboards Development Environment"
	@echo "=================================================="
	@echo "Available commands:"
	@echo "  help          - Show this help message"
	@echo "  up            - Start the development environment"
	@echo "  down          - Stop and remove containers"
	@echo "  restart       - Restart the development environment"
	@echo "  status        - Show container status"
	@echo "  logs          - Show service logs"
	@echo "  shell         - Get a shell in the webserver container"
	@echo "  install       - Install the plugin in development mode"
	@echo "  clean         - Clean up and remove volumes"
	@echo "  test          - Run tests"
	@echo "  build         - Build the development environment"
	@echo "  wait          - Wait for services to be ready"
	@echo "  open          - Open Airflow UI in browser"
	@echo "  setup         - Run all setup steps"
	@echo "  run           - Run a command in the webserver container"
	@echo "  dags          - List available DAGs"
	@echo "  trigger-dag   - Trigger the test DAG"
	@echo "  list-tasks    - List tasks for a DAG"
	@echo "  dag-info      - Show DAG info"
	@echo "  airflow-help  - Show airflow command help"
	@echo "  plugin-info   - Show plugin info"

# Start all services
.PHONY: up
up:
	$(DOCKER_COMPOSE) up -d

# Stop and remove containers
.PHONY: down
down:
	$(DOCKER_COMPOSE) down

# Restart all services
.PHONY: restart
restart:
	$(DOCKER_COMPOSE) restart

# Show container status
.PHONY: status
status:
	$(DOCKER_COMPOSE) ps

# Show service logs
.PHONY: logs
logs:
	$(DOCKER_COMPOSE) logs -f

# Get a shell in the webserver container
.PHONY: shell
shell:
	$(DOCKER_COMPOSE) exec webserver bash

# Install the plugin in development mode
.PHONY: install
install:
	$(DOCKER_COMPOSE) exec webserver pip install -e /plugins/airflow-embeded-dashboards

# Clean up and remove volumes
.PHONY: clean
clean:
	$(DOCKER_COMPOSE) down -v

# Run tests
.PHONY: test
test:
	$(DOCKER_COMPOSE) exec webserver python -m pytest dev/tests/ -v

# Build the development environment
.PHONY: build
build:
	$(DOCKER_COMPOSE) build

# Wait for services to be ready
.PHONY: wait
wait:
	@echo "Waiting for services to be ready..."
	@while ! curl -f http://localhost:8080/health >/dev/null 2>&1; do \
		echo "Waiting for webserver..."; \
		sleep 2; \
	done
	@echo "Services are ready!"

# Open Airflow UI in browser
.PHONY: open
open:
	@echo "Opening Airflow UI..."
	@open http://localhost:8080

# Target to run all setup steps
.PHONY: setup
setup: up install wait
	@echo "Development environment is ready!"
	@echo "Airflow UI: http://localhost:8080"
	@echo "Flower UI: http://localhost:5555"

# Target to run a specific command in the webserver container
.PHONY: run
run:
	$(DOCKER_COMPOSE) exec webserver

# Target to list available DAGs
.PHONY: dags
dags:
	$(DOCKER_COMPOSE) exec webserver airflow dags list

# Target to trigger a test DAG
.PHONY: trigger-dag
trigger-dag:
	$(DOCKER_COMPOSE) exec webserver airflow dags trigger test_dag

# Target to list tasks for a DAG
.PHONY: list-tasks
list-tasks:
	$(DOCKER_COMPOSE) exec webserver airflow tasks list test_dag

# Target to show DAG info
.PHONY: dag-info
dag-info:
	$(DOCKER_COMPOSE) exec webserver airflow dags show test_dag

# Target to get help on airflow commands
.PHONY: airflow-help
airflow-help:
	$(DOCKER_COMPOSE) exec webserver airflow --help

# Target to show plugin info
.PHONY: plugin-info
plugin-info:
	$(DOCKER_COMPOSE) exec webserver airflow plugins list

# Default target when running make without arguments
.DEFAULT_GOAL := help