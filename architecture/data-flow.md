# Data Flow

```text
Synthetic source systems
  -> data/raw/*.csv
  -> ingestion loaders
  -> quality validators
  -> data/quarantine/quality_issues.csv
  -> data/clean/*.csv
  -> data/processed/command_center.duckdb
  -> data/scorecards/table_scorecards.csv
  -> FastAPI service and Streamlit dashboard
```

Bad records are not silently dropped. They are written to quarantine so business users can understand what failed and why.
