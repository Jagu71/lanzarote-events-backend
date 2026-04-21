PYTHON ?= python3

.PHONY: install init-db api scrape scheduler test docker-up docker-down docker-logs

install:
	$(PYTHON) -m pip install -r requirements.txt

init-db:
	$(PYTHON) -m scripts.init_db

api:
	$(PYTHON) -m uvicorn app.main:app --reload

scrape:
	$(PYTHON) -m scripts.run_scrapers

scheduler:
	$(PYTHON) -m scripts.run_scheduler

test:
	$(PYTHON) -m pytest

docker-up:
	docker compose up -d --build

docker-down:
	docker compose down

docker-logs:
	docker compose logs -f
