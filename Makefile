SRC_DIRECTORY:=src
POETRY_VERSION:=1.8.3

include local.env
export

install:
	@if ! command -v poetry &> /dev/null; \
	then \
		echo "Installing poetry"; \
		pip3 install poetry==$(POETRY_VERSION); \
	fi
	@if ! command -v pre-commit &> /dev/null; \
	then \
		echo "Installing pre-commit"; \
		pip3 install pre-commit; \
	fi
	@poetry install --no-root
	@pre-commit install

run: redis
	@python src/app.py

gunicorn: redis
	@poetry run gunicorn src.app:create_app --bind 127.0.0.1:8080 --worker-class aiohttp.GunicornWebWorker --pythonpath src

test:
	poetry run pytest

format:
	@poetry run ruff format .

lint:
	@poetry run ruff check .
	@poetry run mypy .

redis:
	@docker compose up redis -d

pre-commit:
	@git add .pre-commit-config.yaml
	@pre-commit run --all-files

docker.build:
	@docker compose build

docker.up: docker.build
	@docker compose up web -d

docker.down:
	@docker compose down
