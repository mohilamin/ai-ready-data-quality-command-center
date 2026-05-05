from src.data_generation.generate_synthetic_data import generate_all
from src.quality.validators import validate_all


def test_duplicate_missing_and_foreign_key_issues_are_detected() -> None:
    datasets = generate_all()
    issues = validate_all(datasets)
    issue_types = set(issues["issue_type"])
    assert "duplicate_customers" in issue_types
    assert "missing_customer_emails" in issue_types
    assert "invalid_account_foreign_keys" in issue_types
    assert "unauthorized_employee_access" in issue_types
