# Architecture

The command center is a lightweight local data platform with clear layers:

1. Synthetic source generation creates raw enterprise-like CSV files.
2. Ingestion validates expected files and loads them into pandas.
3. Quality checks produce issue-level exceptions and quarantine outputs.
4. Transformations create clean CSVs and curated DuckDB tables.
5. Scoring turns validation evidence into Data Trust and AI-readiness scorecards.
6. FastAPI and Streamlit expose the results for data consumers and executives.

The first version favors explainable Python modules over heavy framework abstractions so every rule, score, and output can be inspected locally.
