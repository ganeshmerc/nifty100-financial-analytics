# 📊 Nifty 100 Financial Analytics

A financial analytics project covering **92 Nifty 100 companies**, focused on ETL pipelines, data quality validation, financial ratios, KPI analysis, CAGR, cash-flow analysis, capital allocation, stock screening, peer comparison, and an interactive Streamlit dashboard.

---

## 🚀 Project Overview

This project builds an end-to-end financial analytics pipeline that transforms raw Excel data into a structured SQLite database and analytical outputs.

### Key Features

* 📥 Excel data ingestion
* 🔄 Data normalization
* ✅ Data quality validation
* 🗄️ SQLite database
* 📊 50+ financial KPIs and ratios
* 📈 CAGR analysis
* 💰 Cash-flow analysis
* 🏦 Capital allocation classification
* 🏦 Financial-sector carve-out
* 🔎 Stock screening
* 🤝 Peer comparison
* 📊 Interactive Streamlit dashboard
* 🧪 Automated testing and validation

---

# 🏗️ Project Pipeline

```text
Raw Excel Data
      │
      ▼
┌───────────────┐
│ Excel Ingestion│
└───────┬───────┘
        │
        ▼
┌────────────────┐
│ Data Normalizer │
└───────┬────────┘
        │
        ▼
┌──────────────────┐
│ Data Validation  │
│ 16 DQ Rules      │
└────────┬─────────┘
         │
         ▼
┌────────────────┐
│ SQLite Database │
└───────┬────────┘
        │
        ▼
┌─────────────────────────┐
│ Financial Analytics     │
│ 50+ KPIs & Ratios       │
└───────────┬─────────────┘
            │
            ▼
┌─────────────────────────┐
│ Screener / Peer Analysis│
└───────────┬─────────────┘
            │
            ▼
┌─────────────────────────┐
│ Streamlit Dashboard     │
└─────────────────────────┘
```

---

# 📌 Sprint 1 — Data Foundation

## ETL Pipeline

The first sprint establishes the project's data foundation.

* Excel data ingestion
* Data normalization
* Data validation
* SQLite database loading
* Foreign-key validation
* Database integrity checks

### Data Quality

Implemented **16 Data Quality rules** to identify:

* Missing values
* Invalid financial data
* Data mismatches
* Missing companies
* Table-level inconsistencies
* Foreign-key issues

### Database

* SQLite database
* Structured financial tables
* SQL schema
* Database validation scripts

---

# 📈 Sprint 2 — Financial Ratio Engine

The project includes **50+ financial KPIs and ratios**.

## Profitability

* ROE
* ROA
* Profit margins
* Other profitability indicators

## Leverage

* Debt-related ratios
* Capital structure analysis
* Leverage indicators

## Efficiency

* Asset efficiency
* Working-capital-related metrics
* Operational efficiency indicators

## Growth

* CAGR engine
* Historical growth analysis

## Cash Flow

* Cash-flow KPIs
* Operating cash-flow analysis
* Cash-flow validation

## Capital Allocation

* Capital allocation classification
* Financial-sector carve-out
* Company-level classification

---

# 🔎 Stock Screener

The project includes a configurable stock screening engine for analyzing companies using financial metrics and ratios.

Configuration:

```text
config/screener_config.yaml
```

---

# 📊 Interactive Streamlit Dashboard

The project includes an interactive **Streamlit dashboard** for exploring company-level financial information.

### Dashboard Sections

* 🏠 Home
* 👤 Company Profile
* 🔎 Stock Screener
* 🤝 Peer Comparison
* 📈 Financial Trends
* 🏭 Sector Analysis
* 💰 Capital Allocation
* 📄 Reports

Run the dashboard with:

```bash
streamlit run src/dashboard/app.py
```

---

# 🧪 Testing & Validation

Automated tests are included for ETL and KPI functionality.

Testing covers:

* Data normalization
* Data validation
* Financial ratio calculations
* KPI calculations
* Edge cases
* Database integrity
* Financial-sector carve-out validation

Run the test suite:

```bash
pytest
```

---

# 🛠️ Tech Stack

| Technology    | Usage                       |
| ------------- | --------------------------- |
| 🐍 Python     | Data processing & analytics |
| 🐼 Pandas     | Data manipulation           |
| 🔢 NumPy      | Numerical analysis          |
| 🗄️ SQLite    | Financial database          |
| 📊 Streamlit  | Interactive dashboard       |
| 🧪 Pytest     | Automated testing           |
| 📋 PyYAML     | Screener configuration      |
| 📑 Excel/XLSX | Source data                 |
| 🗃️ SQL       | Database design & queries   |

---

# 📁 Project Structure

```text
nifty100-financial-analytics/
│
├── config/
│   └── screener_config.yaml
│
├── db/
│   └── schema.sql
│
├── src/
│   ├── analytics/
│   ├── dashboard/
│   ├── etl/
│   ├── nlp/
│   ├── reports/
│   └── screener/
│
├── tests/
│   ├── etl/
│   └── kpi/
│
├── requirements.txt
├── Makefile
├── schema.sql
└── README.md
```

---

# ▶️ Installation & Usage

## 1. Clone the repository

```bash
git clone https://github.com/ganeshmerc/nifty100-financial-analytics.git
cd nifty100-financial-analytics
```

## 2. Create a virtual environment

```bash
python -m venv .venv
```

## 3. Activate the environment

### Windows

```bash
.venv\Scripts\activate
```

## 4. Install dependencies

```bash
pip install -r requirements.txt
```

## 5. Run tests

```bash
pytest
```

## 6. Launch the dashboard

```bash
streamlit run src/dashboard/app.py
```

---

# 🎯 Project Goals

The main goal is to build a structured financial analytics system capable of:

1. Ingesting financial data
2. Normalizing and validating the data
3. Storing data in SQLite
4. Calculating financial KPIs and ratios
5. Analyzing company performance
6. Comparing companies and peers
7. Screening companies using financial metrics
8. Presenting insights through an interactive dashboard

---

# 📌 Project Highlights

| Area               | Implementation                                          |
| ------------------ | ------------------------------------------------------- |
| Companies          | **92 Nifty 100 companies**                              |
| Data Quality       | **16 validation rules**                                 |
| Financial Analysis | **50+ KPIs & ratios**                                   |
| Database           | **SQLite**                                              |
| ETL                | **Python-based pipeline**                               |
| Dashboard          | **Streamlit**                                           |
| Testing            | **Pytest**                                              |
| Screening          | **Configurable stock screener**                         |
| Analysis           | **CAGR, cash flow, capital allocation & peer analysis** |

---

## 👨‍💻 Author

**Ganesh**

GitHub: [@ganeshmerc](https://github.com/ganeshmerc)
