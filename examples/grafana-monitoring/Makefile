# Makefile for Airflow Embedded Dashboards
# Set the Airflow version (2 or 3)

# Variables
VERSION := 3
PROJECT_NAME := airflow-embedash
COMPOSE_FILE := dev/airflow/v$(VERSION)/docker-compose.yaml
DOCKER_COMPOSE := docker compose -f $(COMPOSE_FILE)

# Airflow 2 serves the UI from the webserver; Airflow 3 from the api-server.
ifeq ($(VERSION),2)
AIRFLOW_SERVICE := airflow-webserver
HEALTH_URL := http://localhost:8080/health
else
AIRFLOW_SERVICE := airflow-api-server
HEALTH_URL := http://localhost:8080/api/v2/monitor/health
endif

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
	@echo "  open          - Print local UI URLs"
	@echo "  setup         - Run all setup steps"
	@echo "  run           - Run a command in the webserver container"
	@echo "  dags          - List available DAGs"
	@echo "  unpause-dag   - Unpause the demo DAG so it feeds Grafana"
	@echo "  trigger-dag   - Trigger the test DAG"
	@echo "  list-tasks    - List tasks for a DAG"
	@echo "  dag-info      - Show DAG info"
	@echo "  airflow-help  - Show airflow command help"
	@echo "  plugin-info   - Show plugin info"
	@echo "  prepare       - Create the local demo encryption key if needed"

# Airflow encrypts Variables. All demo containers need the same Fernet key to
# read the dashboard configuration seeded by airflow-init. The key is generated
# locally, stored in ignored .env, and must never be used in a deployment.
.PHONY: prepare
prepare:
	@test -f .env || (umask 077 && printf 'AIRFLOW__CORE__FERNET_KEY=%s\\n' "$$(openssl rand -base64 32 | tr '+/' '-_')" > .env)

# Start all services
.PHONY: up
up: prepare
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
	$(DOCKER_COMPOSE) exec $(AIRFLOW_SERVICE) bash

# Install the plugin in development mode
.PHONY: install
install:
	@echo "The plugin is baked into the local development image. Run 'make build up'."

# Clean up and remove volumes
.PHONY: clean
clean:
	$(DOCKER_COMPOSE) down -v

# Run tests
.PHONY: test
test:
	$(DOCKER_COMPOSE) exec $(AIRFLOW_SERVICE) python -m pytest -v

# Build the development environment
.PHONY: build
build: prepare
	$(DOCKER_COMPOSE) build

# Wait for services to be ready
.PHONY: wait
wait:
	@echo "Waiting for services to be ready..."
	@while ! curl -f $(HEALTH_URL) >/dev/null 2>&1; do \
		echo "Waiting for webserver..."; \
		sleep 2; \
	done
	@echo "Services are ready!"

# Open Airflow UI in browser
.PHONY: open
open:
	@echo "Opening Airflow UI..."
	@echo "Airflow: http://localhost:8080"
	@echo "Grafana: http://localhost:3000/d/airflow-embedash-demo/airflow-pipeline-health?orgId=1"

# Target to run all setup steps
.PHONY: setup
setup: up install wait
	@echo "Development environment is ready!"
	@echo "Airflow UI: http://localhost:8080"
	@echo "Grafana: http://localhost:3000"

# Target to run a specific command in the webserver container
.PHONY: run
run:
	$(DOCKER_COMPOSE) exec $(AIRFLOW_SERVICE)

# Target to list available DAGs
.PHONY: dags
dags:
	$(DOCKER_COMPOSE) exec $(AIRFLOW_SERVICE) airflow dags list

# Target to trigger a test DAG
.PHONY: trigger-dag
trigger-dag:
	$(DOCKER_COMPOSE) exec $(AIRFLOW_SERVICE) airflow dags trigger embedash_demo

# Target to unpause the demo DAG so it starts feeding the Grafana dashboard
.PHONY: unpause-dag
unpause-dag:
	$(DOCKER_COMPOSE) exec $(AIRFLOW_SERVICE) airflow dags unpause embedash_demo

# Target to list tasks for a DAG
.PHONY: list-tasks
list-tasks:
	$(DOCKER_COMPOSE) exec $(AIRFLOW_SERVICE) airflow tasks list embedash_demo

# Target to show DAG info
.PHONY: dag-info
dag-info:
	$(DOCKER_COMPOSE) exec $(AIRFLOW_SERVICE) airflow dags show embedash_demo

# Target to get help on airflow commands
.PHONY: airflow-help
airflow-help:
	$(DOCKER_COMPOSE) exec $(AIRFLOW_SERVICE) airflow --help

# Target to show plugin info
.PHONY: plugin-info
plugin-info:
	$(DOCKER_COMPOSE) exec $(AIRFLOW_SERVICE) airflow plugins

# Default target when running make without arguments
.DEFAULT_GOAL := help
