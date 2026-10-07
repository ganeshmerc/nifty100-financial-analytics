"""
Sprint 2 - Composite Quality Score

Combines profitability, leverage, cash-flow quality,
and growth metrics into a 0-100 quality score.
"""


def score_profitability(npm, roe, roce):
    """
    Profitability score: maximum 30 points.
    """

    score = 0

    if npm is not None:
        if npm >= 20:
            score += 10
        elif npm >= 10:
            score += 7
        elif npm >= 5:
            score += 4

    if roe is not None:
        if roe >= 20:
            score += 10
        elif roe >= 12:
            score += 7
        elif roe >= 5:
            score += 4

    if roce is not None:
        if roce >= 20:
            score += 10
        elif roce >= 12:
            score += 7
        elif roce >= 5:
            score += 4

    return score


def score_leverage(debt_to_equity, interest_coverage):
    """
    Leverage score: maximum 25 points.
    """

    score = 0

    if debt_to_equity is not None:
        if debt_to_equity <= 0.5:
            score += 12
        elif debt_to_equity <= 1:
            score += 9
        elif debt_to_equity <= 2:
            score += 5

    if interest_coverage is not None:
        if interest_coverage >= 5:
            score += 13
        elif interest_coverage >= 3:
            score += 10
        elif interest_coverage >= 1.5:
            score += 6

    return score


def score_cashflow(cfo_quality, fcf_conversion):
    """
    Cash-flow score: maximum 25 points.
    """

    score = 0

    if cfo_quality is not None:
        if cfo_quality > 1:
            score += 12
        elif cfo_quality >= 0.5:
            score += 8

    if fcf_conversion is not None:
        if fcf_conversion >= 80:
            score += 13
        elif fcf_conversion >= 50:
            score += 9
        elif fcf_conversion >= 20:
            score += 5

    return score


def score_growth(revenue_cagr, pat_cagr):
    """
    Growth score: maximum 20 points.
    """

    score = 0

    if revenue_cagr is not None:
        if revenue_cagr >= 15:
            score += 10
        elif revenue_cagr >= 8:
            score += 7
        elif revenue_cagr >= 0:
            score += 4

    if pat_cagr is not None:
        if pat_cagr >= 15:
            score += 10
        elif pat_cagr >= 8:
            score += 7
        elif pat_cagr >= 0:
            score += 4

    return score


def composite_quality_score(
    npm,
    roe,
    roce,
    debt_to_equity,
    interest_coverage,
    cfo_quality,
    fcf_conversion,
    revenue_cagr,
    pat_cagr,
):
    """
    Returns a composite quality score from 0 to 100.
    """

    score = (
        score_profitability(npm, roe, roce)
        + score_leverage(debt_to_equity, interest_coverage)
        + score_cashflow(cfo_quality, fcf_conversion)
        + score_growth(revenue_cagr, pat_cagr)
    )

    return min(score, 100)


def quality_label(score):
    """
    Convert score into a simple investment-quality label.
    """

    if score is None:
        return "INSUFFICIENT_DATA"

    if score >= 80:
        return "Excellent"

    if score >= 65:
        return "Good"

    if score >= 50:
        return "Average"

    if score >= 35:
        return "Weak"

    return "Poor"