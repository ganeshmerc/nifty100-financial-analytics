PRAGMA foreign_keys = ON;

-- Sprint 1 database schema

CREATE TABLE IF NOT EXISTS companies (
    company_id TEXT PRIMARY KEY,
    company_name TEXT NOT NULL,
    ticker TEXT UNIQUE,
    broad_sector TEXT
);

CREATE TABLE IF NOT EXISTS profitandloss (
    company_id TEXT NOT NULL,
    year INTEGER NOT NULL,
    sales REAL,
    operating_profit REAL,
    operating_profit_margin REAL,
    other_income REAL,
    interest REAL,
    net_profit REAL,
    eps REAL,
    dividend_payout REAL,
    PRIMARY KEY (company_id, year),
    FOREIGN KEY (company_id) REFERENCES companies(company_id)
);

CREATE TABLE IF NOT EXISTS balancesheet (
    company_id TEXT NOT NULL,
    year INTEGER NOT NULL,
    equity_capital REAL,
    reserves REAL,
    borrowings REAL,
    investments REAL,
    total_assets REAL,
    book_value_per_share REAL,
    PRIMARY KEY (company_id, year),
    FOREIGN KEY (company_id) REFERENCES companies(company_id)
);

CREATE TABLE IF NOT EXISTS cashflow (
    company_id TEXT NOT NULL,
    year INTEGER NOT NULL,
    operating_activity REAL,
    investing_activity REAL,
    financing_activity REAL,
    PRIMARY KEY (company_id, year),
    FOREIGN KEY (company_id) REFERENCES companies(company_id)
);

CREATE TABLE IF NOT EXISTS analysis (
    company_id TEXT NOT NULL,
    year INTEGER,
    roce_percentage REAL,
    roe_percentage REAL,
    opm_percentage REAL,
    FOREIGN KEY (company_id) REFERENCES companies(company_id)
);

CREATE TABLE IF NOT EXISTS documents (
    company_id TEXT,
    document_type TEXT,
    document_url TEXT,
    FOREIGN KEY (company_id) REFERENCES companies(company_id)
);

CREATE TABLE IF NOT EXISTS prosandcons (
    company_id TEXT,
    item_type TEXT,
    description TEXT,
    FOREIGN KEY (company_id) REFERENCES companies(company_id)
);

CREATE TABLE IF NOT EXISTS sectors (
    company_id TEXT,
    broad_sector TEXT,
    sector TEXT,
    FOREIGN KEY (company_id) REFERENCES companies(company_id)
);

CREATE TABLE IF NOT EXISTS stock_prices (
    company_id TEXT,
    date TEXT,
    close_price REAL,
    FOREIGN KEY (company_id) REFERENCES companies(company_id)
);

CREATE TABLE IF NOT EXISTS financial_ratios (
    company_id TEXT NOT NULL,
    year INTEGER NOT NULL,

    net_profit_margin_pct REAL,
    operating_profit_margin_pct REAL,
    return_on_equity_pct REAL,
    return_on_capital_employed_pct REAL,
    return_on_assets_pct REAL,

    debt_to_equity REAL,
    interest_coverage REAL,
    asset_turnover REAL,
    net_debt_cr REAL,

    free_cash_flow_cr REAL,
    capex_cr REAL,
    cfo_quality_score REAL,
    capex_intensity_pct REAL,
    fcf_conversion_rate_pct REAL,

    earnings_per_share REAL,
    book_value_per_share REAL,
    dividend_payout_ratio_pct REAL,
    total_debt_cr REAL,
    cash_from_operations_cr REAL,

    revenue_cagr_3yr REAL,
    revenue_cagr_5yr REAL,
    revenue_cagr_10yr REAL,

    pat_cagr_3yr REAL,
    pat_cagr_5yr REAL,
    pat_cagr_10yr REAL,

    eps_cagr_3yr REAL,
    eps_cagr_5yr REAL,
    eps_cagr_10yr REAL,

    composite_quality_score REAL,

    high_leverage_flag INTEGER DEFAULT 0,
    icr_warning_flag INTEGER DEFAULT 0,
    icr_label TEXT,

    PRIMARY KEY (company_id, year),
    FOREIGN KEY (company_id) REFERENCES companies(company_id)
);

CREATE TABLE IF NOT EXISTS peer_groups (
    company_id TEXT,
    peer_company_id TEXT,
    FOREIGN KEY (company_id) REFERENCES companies(company_id),
    FOREIGN KEY (peer_company_id) REFERENCES companies(company_id)
);
