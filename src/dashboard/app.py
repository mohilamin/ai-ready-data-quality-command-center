from __future__ import annotations

import json
from pathlib import Path

import pandas as pd
import streamlit as st

from src.common.config import get_path


def read_csv(path: Path) -> pd.DataFrame:
    if not path.exists():
        return pd.DataFrame()
    return pd.read_csv(path)


def main() -> None:
    st.set_page_config(page_title="AI-Ready Data Quality Command Center", layout="wide")
    st.title("AI-Ready Data Quality Command Center")

    scorecards = read_csv(get_path("scorecards") / "table_scorecards.csv")
    issues = read_csv(get_path("quarantine") / "quality_issues.csv")
    loads = read_csv(get_path("clean") / "source_system_loads.csv")
    lineage = read_csv(get_path("clean") / "data_lineage_events.csv")
    summary_path = get_path("scorecards") / "ai_readiness_summary.json"
    summary = {}
    if summary_path.exists():
        with summary_path.open("r", encoding="utf-8") as file:
            summary = json.load(file)

    st.header("Executive Overview")
    col1, col2, col3 = st.columns(3)
    col1.metric("AI Readiness", summary.get("overall_ai_readiness_score", "Run pipeline"))
    col2.metric("Critical Issues", summary.get("critical_issue_count", "Run pipeline"))
    col3.metric("Tables Scored", len(scorecards) if not scorecards.empty else 0)

    st.header("Table-Level Data Trust Scores")
    if scorecards.empty:
        st.info("Run `python -m src.pipeline.run_all` to generate scorecards.")
    else:
        st.bar_chart(scorecards.set_index("table_name")["ai_readiness_score"])
        st.dataframe(scorecards, use_container_width=True)

    st.header("Data Quality Issues")
    if issues.empty:
        st.success("No quality issues found or pipeline has not run yet.")
    else:
        st.bar_chart(issues.groupby("issue_type").size())
        st.dataframe(issues, use_container_width=True)

    st.header("Quarantine Records")
    quarantine_path = get_path("quarantine")
    quarantine_files = sorted(quarantine_path.glob("*_quarantine.csv"))
    if not quarantine_files:
        st.info("No quarantine files found.")
    for path in quarantine_files:
        st.subheader(path.stem.replace("_quarantine", ""))
        st.dataframe(read_csv(path), use_container_width=True)

    st.header("AI-Readiness Assessment")
    st.json(summary or {"message": "Run the pipeline to create the AI-readiness summary."})

    st.header("Source Load Freshness")
    st.dataframe(loads, use_container_width=True)

    st.header("Lineage Summary")
    st.dataframe(lineage, use_container_width=True)


if __name__ == "__main__":
    main()
