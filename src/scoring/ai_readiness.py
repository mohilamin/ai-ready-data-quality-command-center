from __future__ import annotations

import pandas as pd

from src.scoring.trust_score import summarize_scorecards


def calculate_ai_readiness_summary(
    scorecards: pd.DataFrame, issues: pd.DataFrame
) -> dict[str, object]:
    """Calculate the AI-readiness executive summary."""
    return summarize_scorecards(scorecards, issues)
