from src.data_generation.generate_synthetic_data import generate_all


def test_generation_is_deterministic_and_complete() -> None:
    first = generate_all()
    second = generate_all()
    assert set(first) == {
        "customers",
        "accounts",
        "transactions",
        "product_reference",
        "employee_access",
        "source_system_loads",
        "data_lineage_events",
    }
    assert first["customers"].equals(second["customers"])
    assert first["customers"]["customer_id"].duplicated().any()
    assert first["transactions"]["product_code"].isin(["BADCODE", "UNKNOWN"]).any()
