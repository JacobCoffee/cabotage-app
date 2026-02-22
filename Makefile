BUNENV_DIR := .bunenv
ACTIVATE  := . $(BUNENV_DIR)/bin/activate &&
DOCKER    := docker compose
EXEC      := docker-compose exec cabotage-app
RUN       := $(DOCKER) run --build --rm base

.DEFAULT_GOAL := help

##@ Help
help: ## Show this help
	@awk 'BEGIN {FS = ":.*##"; printf "\nUsage:\n  make \033[36m<target>\033[0m\n"} \
		/^[a-zA-Z_-]+:.*?##/ { printf "  \033[36m%-20s\033[0m %s\n", $$1, $$2 } \
		/^##@/ { printf "\n\033[1m%s\033[0m\n", substr($$0, 5) }' $(MAKEFILE_LIST)

##@ Development
start: ## Start all services
	docker-compose up --build --detach

stop: ## Stop all services
	docker-compose down

destroy: ## Stop and remove volumes
	docker-compose down --volumes

routes: ## Show Flask routes
	$(EXEC) python3 -m flask routes

create-admin: ## Create admin user
	$(EXEC) python3 -m cabotage.scripts.create_admin

##@ Database
migrate: ## Run database migrations
	$(EXEC) python3 -m flask db upgrade

migrations: ## Generate a new migration (usage: make migrations "description")
	$(EXEC) python3 -m flask db revision --autogenerate -m "$(filter-out $@,$(MAKECMDGOALS))"

##@ Setup
setup: setup-frontend ## Set up all dev tooling

setup-frontend: ## Create bunenv and install frontend packages
	bunenv $(BUNENV_DIR)
	$(ACTIVATE) bun install

requirements/%.txt: requirements/%.in
	$(RUN) pip-compile --allow-unsafe --generate-hashes --output-file=$@ $(F) $<

##@ Formatting
fmt: fmt-py fmt-templates fmt-frontend ## Format everything

fmt-py: ## Format Python (black)
	$(RUN) black .

fmt-templates: ## Format Jinja2/HTML templates (djlint, 2-space indent)
	$(RUN) djlint cabotage/client/templates/ --reformat

fmt-frontend: ## Format JS/CSS (oxfmt, 2-space indent)
	$(ACTIVATE) bun run fmt

##@ Linting
lint: ## Lint Python
	$(RUN) bin/lint

lint-templates: ## Lint Jinja2/HTML templates (djlint)
	$(RUN) djlint cabotage/client/templates/ --lint

lint-frontend: ## Lint JS/CSS (oxlint)
	$(ACTIVATE) bun run lint

##@ Quality
type-check: ## Run mypy type checking
	$(RUN) mypy --config-file pyproject.toml .

security-check: ## Run bandit security scan
	$(RUN) bandit -c pyproject.toml -r .

##@ Build
minify: ## Minify CSS/JS via bun (lightningcss + bun build)
	$(ACTIVATE) bun run minify:css && bun run minify:js

minify-py: ## Minify CSS/JS via Python (no bun required)
	$(RUN) python3 -c "\
	import rcssmin, rjsmin, pathlib; \
	css = pathlib.Path('cabotage/client/static/main.css'); \
	js = pathlib.Path('cabotage/client/static/main.js'); \
	css.with_suffix('.min.css').write_text(rcssmin.cssmin(css.read_text())); \
	js.with_suffix('.min.js').write_text(rjsmin.jsmin(js.read_text()))"

##@ CI
ci: ## Run prek hooks with autofix, then verify clean
	prek run --all-files || true
	prek run --all-files

# Aliases
reformat: fmt

.PHONY: help start stop destroy routes create-admin \
	migrate migrations \
	setup setup-frontend \
	fmt fmt-py fmt-templates fmt-frontend \
	lint lint-templates lint-frontend \
	type-check security-check \
	minify minify-py reformat ci
