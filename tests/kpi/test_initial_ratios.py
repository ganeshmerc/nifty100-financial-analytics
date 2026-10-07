from src.analytics.ratios import (
    net_profit_margin,
    operating_profit_margin,
    return_on_equity,
    debt_to_equity,
    interest_coverage
)


def test_net_profit_margin():
    assert net_profit_margin(100, 1000) == 10


def test_net_profit_margin_zero_sales():
    assert net_profit_margin(100, 0) is None


def test_roe():
    assert return_on_equity(100, 500, 500) == 10


def test_roe_negative_equity():
    assert return_on_equity(100, -600, 500) is None


def test_debt_free():
    assert debt_to_equity(0, 500, 500) == 0


def test_interest_zero():
    assert interest_coverage(100, 10, 0) is None
