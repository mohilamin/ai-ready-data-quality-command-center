.PHONY: install generate-data run-pipeline test lint format dashboard api docker-up docker-down

install:
	pip install -r requirements.txt

generate-data:
	python -m src.data_generation.generate_synthetic_data

run-pipeline:
	python -m src.pipeline.run_all

test:
	pytest

lint:
	ruff check .

format:
	ruff format .

dashboard:
	streamlit run src/dashboard/app.py

api:
	uvicorn src.api.main:app --reload

docker-up:
	docker compose up --build

docker-down:
	docker compose down
