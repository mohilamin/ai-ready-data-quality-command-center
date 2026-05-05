# AGENTS.md

You are building a production-style Data Engineering + AI/MLOps portfolio project.

Project name:
AI-Ready Data Quality Command Center

Primary goal:
Build a realistic enterprise data engineering system that converts messy raw source data into trusted, governed, AI-ready data products.

## Business Context

Large enterprises want to deploy AI, GenAI agents, analytics, automation, risk models, fraud models, and operational dashboards. These initiatives fail when data is stale, duplicated, inconsistent, incomplete, poorly governed, or not traceable.

This project must show how a data engineer would solve that problem in a Fortune 50-style environment.

## Core Outcome

The system should answer:

"Can this dataset be trusted for analytics, machine learning, GenAI, or enterprise decisioning?"

## Build Principles

- Write clean, modular, production-style Python.
- Use type hints.
- Use docstrings for public functions.
- Use structured logging.
- Add error handling.
- Avoid overengineering.
- Prefer simple, explainable architecture.
- Every data pipeline must be testable.
- Every data quality rule must be documented.
- Every model, score, or AI output must include evaluation or explanation.
- Use synthetic data only.
- Do not use real customer, health, financial, or personal data.
- Keep the README updated after each major feature.
- Keep all code runnable locally.
- Avoid hidden dependencies.
- Add tests with pytest.
- Add GitHub Actions CI.
- Add Docker support.

## Required Architecture

The repo should contain these layers:

1. Synthetic data generation
2. Raw data ingestion
3. Schema validation
4. Data quality checks
5. Quarantine handling
6. Clean trusted data outputs
7. Data Trust Score calculation
8. AI-readiness scoring
9. API service
10. Streamlit dashboard
11. Tests
12. Documentation
13. CI/CD

## Expected Folder Structure

```text
ai-ready-data-quality-command-center/
  README.md
  AGENTS.md
  architecture/
    architecture.md
    data-flow.md
    star-story.md
  config/
    settings.yaml
    data_quality_rules.yaml
  data/
    raw/
    processed/
    clean/
    quarantine/
    scorecards/
  docs/
    business-problem.md
    data-dictionary.md
    implementation-plan.md
    metrics.md
    demo-script.md
    linkedin-post.md
  notebooks/
    01_data_exploration.ipynb
  src/
    __init__.py
    common/
      __init__.py
      config.py
      logging.py
      paths.py
    data_generation/
      __init__.py
      generate_synthetic_data.py
    ingestion/
      __init__.py
      loaders.py
    quality/
      __init__.py
      validators.py
      rules.py
      quarantine.py
    transformation/
      __init__.py
      clean.py
      models.py
    scoring/
      __init__.py
      trust_score.py
      ai_readiness.py
    api/
      __init__.py
      main.py
    dashboard/
      __init__.py
      app.py
    pipeline/
      __init__.py
      run_all.py
  tests/
    unit/
    integration/
    data_quality/
  .github/
    workflows/
      ci.yml
  .env.example
  .gitignore
  Dockerfile
  docker-compose.yml
  Makefile
  pyproject.toml
  requirements.txt
```

## Synthetic Datasets

Create synthetic datasets for:

customers
accounts
transactions
product_reference
employee_access
source_system_loads
data_lineage_events

Each dataset must include realistic columns and controlled bad data.

## Required Data Quality Issues

Inject controlled issues such as:

duplicate records
missing required fields
invalid foreign keys
stale source loads
invalid product codes
outlier transaction amounts
inconsistent date formats
invalid email formats
exposed PII fields
schema drift
negative balances where not allowed
transactions linked to closed accounts
unauthorized employee access events

## Data Trust Score

For each table, calculate:

completeness_score
uniqueness_score
freshness_score
schema_stability_score
referential_integrity_score
anomaly_score
pii_risk_score
ai_readiness_score

Scores should be from 0 to 100.

Document formulas in docs/metrics.md.

## API Requirements

Create a FastAPI app with these endpoints:

GET /health
GET /tables
GET /tables/{table_name}/score
GET /issues
GET /quarantine
GET /ai-readiness-summary

## Dashboard Requirements

Create a Streamlit dashboard with these pages or sections:

Executive Overview
Table-Level Data Trust Scores
Data Quality Issues
Quarantine Records
AI-Readiness Assessment
Source Load Freshness
Lineage Summary

The dashboard should be simple, clean, and business-readable.

## Required Commands

Use these commands where possible:

pip install -r requirements.txt
python -m src.data_generation.generate_synthetic_data
python -m src.pipeline.run_all
pytest
ruff check .
ruff format .
streamlit run src/dashboard/app.py
uvicorn src.api.main:app --reload

## Makefile Commands

Create a Makefile with:

make install
make generate-data
make run-pipeline
make test
make lint
make format
make dashboard
make api
make docker-up
make docker-down

## Testing Requirements

Add tests for:

synthetic data generation
schema validation
data quality rules
quarantine logic
scoring formulas
pipeline execution
API endpoints

## Definition of Done

A task is complete only when:

Code runs locally.
Tests pass.
README is updated.
Data dictionary is updated.
Metrics are documented.
Logs are useful.
Errors are handled.
The dashboard can run.
API endpoints return valid JSON.
GitHub Actions workflow exists.
Docker files exist.
STAR story is documented.
LinkedIn post draft is included.