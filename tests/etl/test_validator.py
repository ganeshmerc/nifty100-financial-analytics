import pandas as pd

from src.etl.validator import DataQualityValidator


def test_dq01_duplicate_primary_key():
    df = pd.DataFrame({
        "company_id": [1, 1, 2],
        "year": [2024, 2024, 2024],
    })

    validator = DataQualityValidator()

    validator.check_pk_uniqueness(
        df,
        ["company_id", "year"],
    )

    assert len(validator.failures) == 2
    assert all(
        failure.rule_id == "DQ-01"
        for failure in validator.failures
    )


def test_dq02_duplicate_company_year():
    df = pd.DataFrame({
        "company_id": [1, 1, 2],
        "year": [2024, 2024, 2024],
    })

    validator = DataQualityValidator()

    validator.check_company_year_uniqueness(df)

    assert len(validator.failures) == 2
    assert all(
        failure.rule_id == "DQ-02"
        for failure in validator.failures
    )


def test_dq03_invalid_foreign_key():
    child = pd.DataFrame({
        "company_id": [1, 2, 99],
        "year": [2024, 2024, 2024],
    })

    parent = pd.DataFrame({
        "company_id": [1, 2],
    })

    validator = DataQualityValidator()

    validator.check_foreign_keys(
        child,
        parent,
    )

    assert len(validator.failures) == 1
    assert validator.failures[0].rule_id == "DQ-03"
    assert validator.failures[0].severity == "CRITICAL"


def test_dq03_valid_foreign_keys():
    child = pd.DataFrame({
        "company_id": [1, 2],
        "year": [2024, 2024],
    })

    parent = pd.DataFrame({
        "company_id": [1, 2],
    })

    validator = DataQualityValidator()

    validator.check_foreign_keys(
        child,
        parent,
    )

    assert len(validator.failures) == 0


def test_dq04_balance_sheet_valid():
    df = pd.DataFrame({
        "company_id": [1],
        "year": [2024],
        "total_assets": [1000],
        "total_liabilities": [1000],
    })

    validator = DataQualityValidator()

    validator.check_balance_sheet_balance(df)

    assert len(validator.failures) == 0


def test_dq04_balance_sheet_invalid():
    df = pd.DataFrame({
        "company_id": [1],
        "year": [2024],
        "total_assets": [1000],
        "total_liabilities": [900],
    })

    validator = DataQualityValidator()

    validator.check_balance_sheet_balance(df)

    assert len(validator.failures) == 1
    assert validator.failures[0].rule_id == "DQ-04"
    assert validator.failures[0].severity == "CRITICAL"


def test_dq05_opm_valid():
    df = pd.DataFrame({
        "company_id": [1],
        "year": [2024],
        "sales": [1000],
        "operating_profit": [200],
        "opm_percentage": [20],
    })

    validator = DataQualityValidator()

    validator.check_opm_crosscheck(df)

    assert len(validator.failures) == 0


def test_dq05_opm_mismatch():
    df = pd.DataFrame({
        "company_id": [1],
        "year": [2024],
        "sales": [1000],
        "operating_profit": [200],
        "opm_percentage": [10],
    })

    validator = DataQualityValidator()

    validator.check_opm_crosscheck(df)

    assert len(validator.failures) == 1
    assert validator.failures[0].rule_id == "DQ-05"
    assert validator.failures[0].severity == "WARNING"


def test_dq06_positive_sales():
    df = pd.DataFrame({
        "company_id": [1],
        "year": [2024],
        "sales": [1000],
    })

    validator = DataQualityValidator()

    validator.check_positive_sales(df)

    assert len(validator.failures) == 0


def test_dq06_zero_sales():
    df = pd.DataFrame({
        "company_id": [1],
        "year": [2024],
        "sales": [0],
    })

    validator = DataQualityValidator()

    validator.check_positive_sales(df)

    assert len(validator.failures) == 1
    assert validator.failures[0].rule_id == "DQ-06"


def test_dq06_negative_sales():
    df = pd.DataFrame({
        "company_id": [1],
        "year": [2024],
        "sales": [-100],
    })

    validator = DataQualityValidator()

    validator.check_positive_sales(df)

    assert len(validator.failures) == 1


def test_failure_export(tmp_path, monkeypatch):
    import src.etl.validator as validator_module

    monkeypatch.setattr(
        validator_module,
        "OUTPUT_DIR",
        tmp_path,
    )

    validator = DataQualityValidator()

    validator.add_failure(
        rule_id="DQ-01",
        severity="CRITICAL",
        message="Test failure",
        company_id=1,
        year=2024,
    )

    output = validator.export_failures()

    assert output.exists()

    result = pd.read_csv(output)

    assert len(result) == 1
    assert result.iloc[0]["rule_id"] == "DQ-01"