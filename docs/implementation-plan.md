# Implementation Plan

## Objective

Build a lightweight, production-style local data quality command center that demonstrates how messy synthetic enterprise data becomes trusted, governed, AI-ready data products.

## Phase 1: Bootstrap

- Create the expected repository structure from `AGENTS.md`.
- Add Python 3.11 project metadata, dependency pins, lint settings, Docker files, CI, and make commands.
- Add configuration files for paths, freshness thresholds, scoring weights, and table-level data quality rules.
- Draft meaningful architecture, business, metrics, data dictionary, demo, STAR, and LinkedIn documentation.

## Phase 2: Synthetic Data

- Generate deterministic synthetic CSV files in `data/raw` using a configured random seed.
- Include realistic columns for customers, accounts, transactions, product reference, employee access, source system loads, and lineage events.
- Inject controlled quality issues so validation and scoring have visible evidence to detect.

## Phase 3: Ingestion, Quality, and Quarantine

- Load raw CSVs into pandas DataFrames with clear logging and file validation.
- Detect required-field failures, duplicate business keys, invalid relationships, stale loads, invalid product codes, anomalies, PII risk indicators, unauthorized access, schema drift, and closed-account transactions.
- Write an issue-level exceptions table and table-specific quarantine files.

## Phase 4: Transformation and Scoring

- Remove invalid rows from clean outputs while preserving source data and quarantine evidence.
- Build curated DuckDB models for customer/account, transaction risk, source freshness, and issue summary use cases.
- Calculate table-level Data Trust and AI-readiness scorecards from quality evidence.

## Phase 5: Service and Dashboard

- Add a FastAPI app that serves health, table lists, scorecards, issues, quarantine summaries, and AI-readiness summaries.
- Add a Streamlit dashboard with business-readable scorecards, issue tables, quarantine views, freshness summaries, and lineage views.

## Phase 6: Verification

- Add pytest coverage for generation, ingestion, validation, scoring, pipeline execution, and the API health endpoint.
- Run data generation, the full pipeline, pytest, and ruff.
- Update the README with setup, run, API, dashboard, testing, business value, and known limitations.
