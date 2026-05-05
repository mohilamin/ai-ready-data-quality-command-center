from src.data_generation.generate_synthetic_data import generate_all
from src.quality.validators import validate_all
from src.scoring.trust_score import calculate_table_scorecards, expected_score_columns


def test_scorecards_include_required_scores() -> None:
    datasets = generate_all()
    issues = validate_all(datasets)
    scorecards = calculate_table_scorecards(datasets, issues)
    assert set(expected_score_columns()).issubset(scorecards.columns)
    assert scorecards["ai_readiness_score"].between(0, 100).all()
