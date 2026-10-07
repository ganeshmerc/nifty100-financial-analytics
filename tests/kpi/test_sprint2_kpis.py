"""
Sprint 2 - Additional KPI Formula Tests

Covers:
- OPM
- ROCE
- ROA
- Debt-to-Equity
- Interest Coverage
- Net Debt
- Asset Turnover
- FCF
- CFO Quality
- CapEx Intensity
- FCF Conversion
- CAGR edge cases
"""

from src.analytics.ratios import (
    operating_profit_margin,
    return_on_capital_employed,
    return_on_assets,
    debt_to_equity,
    interest_coverage,
    net_debt,
    asset_turnover,
)

from src.analytics.cashflow_kpis import (
    free_cash_flow,
    cfo_quality_score,
    capex_intensity,
    fcf_conversion_rate,
)

from src.analytics.cagr import calculate_cagr


# ============================================================
# PROFITABILITY
# ============================================================

def test_opm_normal():
    result = operating_profit_margin(200, 1000)
    assert result == 20.0


def test_opm_zero_sales():
    result = operating_profit_margin(200, 0)
    assert result is None


def test_roce_normal():
    result = return_on_capital_employed(
        200,      # EBIT
        500,      # equity capital
        500,      # reserves
        200       # borrowings
    )

    expected = 200 / (500 + 500 + 200) * 100
    assert abs(result - expected) < 0.0001


def test_roa_normal():
    result = return_on_assets(100, 1000)
    assert result == 10.0


def test_roa_zero_assets():
    result = return_on_assets(100, 0)
    assert result is None


# ============================================================
# LEVERAGE & EFFICIENCY
# ============================================================

def test_debt_to_equity_normal():
    result = debt_to_equity(200, 500, 500)
    assert result == 0.2


def test_debt_to_equity_debt_free():
    result = debt_to_equity(0, 500, 500)
    assert result == 0


def test_interest_coverage_normal():
    result = interest_coverage(200, 50, 50)
    assert result == 5.0


def test_interest_coverage_zero_interest():
    result = interest_coverage(200, 50, 0)
    assert result is None


def test_net_debt():
    result = net_debt(500, 200)
    assert result == 300


def test_asset_turnover_normal():
    result = asset_turnover(1000, 500)
    assert result == 2.0


def test_asset_turnover_zero_assets():
    result = asset_turnover(1000, 0)
    assert result is None


# ============================================================
# CASH FLOW
# ============================================================

def test_free_cash_flow():
    result = free_cash_flow(500, -200)
    assert result == 300


def test_cfo_quality_high():
    ratio, label = cfo_quality_score(120, 100)

    assert ratio == 1.2
    assert label == "High Quality"


def test_cfo_quality_moderate():
    ratio, label = cfo_quality_score(70, 100)

    assert ratio == 0.7
    assert label == "Moderate"


def test_cfo_quality_zero_pat():
    ratio, label = cfo_quality_score(100, 0)

    assert ratio is None
    assert label is None


def test_capex_intensity():
    value, label = capex_intensity(-20, 1000)

    assert value == 2.0
    assert label == "Asset Light"


def test_fcf_conversion():
    result = fcf_conversion_rate(200, 400)

    assert result == 50.0


# ============================================================
# CAGR
# ============================================================

def test_cagr_normal():
    value, flag = calculate_cagr(100, 121, 2)

    assert abs(value - 10.0) < 0.0001
    assert flag is None


def test_cagr_zero_base():
    value, flag = calculate_cagr(0, 100, 5)

    assert value is None
    assert flag == "ZERO_BASE"


def test_cagr_turnaround():
    value, flag = calculate_cagr(-100, 100, 5)

    assert value is None
    assert flag == "TURNAROUND"


def test_cagr_decline_to_loss():
    value, flag = calculate_cagr(100, -100, 5)

    assert value is None
    assert flag == "DECLINE_TO_LOSS"


def test_cagr_both_negative():
    value, flag = calculate_cagr(-100, -200, 5)

    assert value is None
    assert flag == "BOTH_NEGATIVE"


def test_cagr_insufficient():
    value, flag = calculate_cagr(100, 120, 0)

    assert value is None
    assert flag == "INSUFFICIENT"