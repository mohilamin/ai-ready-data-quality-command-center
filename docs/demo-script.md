# Demo Script

1. Run `make generate-data` to create deterministic raw source data.
2. Run `make run-pipeline` to validate, quarantine, clean, model, and score the data.
3. Open the scorecard CSV and show the lowest-scoring tables.
4. Open the quality issues table and explain the detected root causes.
5. Launch `make api` and show `/health`, `/tables`, and `/ai-readiness-summary`.
6. Launch `make dashboard` and walk through the executive overview, issues, quarantine, freshness, and lineage sections.
