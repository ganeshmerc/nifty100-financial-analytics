"""
Sprint 2 - Capital Allocation Classifier

Classifies company-year cash-flow behavior based on:
CFO = Cash Flow from Operations
CFI = Cash Flow from Investing
CFF = Cash Flow from Financing

Patterns:
(+,-,-) = Reinvestor
(+,-,-) with high CFO/PAT = Shareholder Returns
(+,+,-) = Liquidating Assets
(-,+,+) = Distress Signal
(-,-,+) = Growth Funded by Debt
(+,+,+) = Cash Accumulator
(-,-,-) = Pre-Revenue
(+,-,+) = Mixed
"""


def sign(value):
    """
    Return the sign of a cash-flow value.

    Positive → +
    Negative → -
    Zero     → 0
    """
    if value is None:
        return None

    if value > 0:
        return "+"

    if value < 0:
        return "-"

    return "0"


def classify_capital_allocation(
    cfo,
    cfi,
    cff,
    cfo_pat_ratio=None,
):
    """
    Classify capital allocation pattern.

    High CFO/PAT threshold:
        > 1.0 = High Quality / Shareholder Returns

    Returns:
        pattern_label
    """

    cfo_sign = sign(cfo)
    cfi_sign = sign(cfi)
    cff_sign = sign(cff)

    # Missing data
    if None in (cfo_sign, cfi_sign, cff_sign):
        return "Unknown"

    pattern = (cfo_sign, cfi_sign, cff_sign)

    # --------------------------------------------------
    # (+,-,-)
    # --------------------------------------------------
    # Normal case:
    # Cash generated from operations is being reinvested
    # and financing cash flow is negative.
    #
    # If CFO/PAT > 1.0, classify as shareholder returns.
    # --------------------------------------------------

    if pattern == ("+", "-", "-"):

        if cfo_pat_ratio is not None and cfo_pat_ratio > 1.0:
            return "Shareholder Returns"

        return "Reinvestor"

    # --------------------------------------------------
    # (+,+,-)
    # --------------------------------------------------

    if pattern == ("+", "+", "-"):
        return "Liquidating Assets"

    # --------------------------------------------------
    # (-,+,+)
    # --------------------------------------------------

    if pattern == ("-", "+", "+"):
        return "Distress Signal"

    # --------------------------------------------------
    # (-,-,+)
    # --------------------------------------------------

    if pattern == ("-", "-", "+"):
        return "Growth Funded by Debt"

    # --------------------------------------------------
    # (+,+,+)
    # --------------------------------------------------

    if pattern == ("+", "+", "+"):
        return "Cash Accumulator"

    # --------------------------------------------------
    # (-,-,-)
    # --------------------------------------------------

    if pattern == ("-", "-", "-"):
        return "Pre-Revenue"

    # --------------------------------------------------
    # (+,-,+)
    # --------------------------------------------------

    if pattern == ("+", "-", "+"):
        return "Mixed"

    # --------------------------------------------------
    # Any remaining / zero-sign combination
    # --------------------------------------------------

    return "Mixed"


def get_capital_allocation(
    cfo,
    cfi,
    cff,
    pat=None,
):
    """
    Return complete capital allocation information.

    Returns dictionary containing:
        cfo_sign
        cfi_sign
        cff_sign
        cfo_pat_ratio
        pattern_label
    """

    cfo_pat_ratio = None

    if pat is not None and pat != 0:
        cfo_pat_ratio = cfo / pat

    label = classify_capital_allocation(
        cfo,
        cfi,
        cff,
        cfo_pat_ratio,
    )

    return {
        "cfo_sign": sign(cfo),
        "cfi_sign": sign(cfi),
        "cff_sign": sign(cff),
        "cfo_pat_ratio": cfo_pat_ratio,
        "pattern_label": label,
    }