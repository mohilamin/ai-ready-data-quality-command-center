from __future__ import annotations

import json
from pathlib import Path

import pandas as pd
from fastapi import FastAPI, HTTPException

from src.common.config import get_path

app = FastAPI(title="AI-Ready Data Quality Command Center")


def _csv(path: Path) -> pd.DataFrame:
    if not path.exists():
        return pd.DataFrame()
    return pd.read_csv(path)


def _records(path: Path) -> list[dict[str, object]]:
    return _csv(path).fillna("").to_dict("records")


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok", "service": "ai-ready-data-quality-command-center"}


@app.get("/tables")
def tables() -> dict[str, list[str]]:
    raw_path = get_path("raw")
    return {"tables": sorted(path.stem for path in raw_path.glob("*.csv"))}


@app.get("/tables/{table_name}/score")
def table_score(table_name: str) -> dict[str, object]:
    scorecards = _csv(get_path("scorecards") / "table_scorecards.csv")
    if scorecards.empty:
        raise HTTPException(status_code=404, detail="Scorecards have not been generated.")
    matches = scorecards.loc[scorecards["table_name"] == table_name]
    if matches.empty:
        raise HTTPException(status_code=404, detail=f"No scorecard found for table {table_name}.")
    return matches.iloc[0].fillna("").to_dict()


@app.get("/issues")
def issues() -> list[dict[str, object]]:
    return _records(get_path("quarantine") / "quality_issues.csv")


@app.get("/quarantine")
def quarantine() -> dict[str, list[dict[str, object]]]:
    quarantine_path = get_path("quarantine")
    return {
        path.stem.replace("_quarantine", ""): _records(path)
        for path in sorted(quarantine_path.glob("*_quarantine.csv"))
    }


@app.get("/ai-readiness-summary")
def ai_readiness_summary() -> dict[str, object]:
    path = get_path("scorecards") / "ai_readiness_summary.json"
    if not path.exists():
        raise HTTPException(status_code=404, detail="AI-readiness summary has not been generated.")
    with path.open("r", encoding="utf-8") as file:
        return json.load(file)
