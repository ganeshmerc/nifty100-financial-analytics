import streamlit as st
from pathlib import Path


# ============================================================
# PAGE CONFIGURATION
# ============================================================

st.set_page_config(
    page_title="Nifty 100 Analytics",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded",
)


# ============================================================
# PROJECT PATH
# ============================================================

PROJECT_ROOT = Path(__file__).resolve().parents[2]


# ============================================================
# CUSTOM CSS
# ============================================================

st.markdown(
    """
    <style>
        /* FORCE SIDEBAR PAGE NAMES TO UPPERCASE */
        section[data-testid="stSidebar"] a {
            text-transform: uppercase !important;
        }

        section[data-testid="stSidebar"] a span {
            text-transform: uppercase !important;
        }

        section[data-testid="stSidebar"] [data-testid="stMarkdownContainer"] {
            text-transform: uppercase;
        }
        .main-header {
            font-size: 2.4rem;
            font-weight: 700;
            margin-bottom: 0.2rem;
        }

        .sub-header {
            font-size: 1.05rem;
            color: #666;
            margin-bottom: 1.5rem;
        }

        .metric-card {
            padding: 1rem;
            border-radius: 10px;
            border: 1px solid #ddd;
            background-color: #fafafa;
        }

        .section-title {
            font-size: 1.4rem;
            font-weight: 600;
            margin-top: 1rem;
            margin-bottom: 0.8rem;
        }

        .footer {
            margin-top: 3rem;
            padding-top: 1rem;
            border-top: 1px solid #ddd;
            text-align: center;
            color: #777;
            font-size: 0.85rem;
        }
    </style>
    """,
    unsafe_allow_html=True,
)


# ============================================================
# SIDEBAR
# ============================================================

with st.sidebar:

    st.title("📊 NIFTY 100")
    st.caption("FINANCIAL ANALYTICS DASHBOARD")

    st.divider()

    st.subheader("NAVIGATION")

    st.markdown(
        """
        Use the pages in the sidebar to explore:

        **🏠 HOME**

        Market-wide KPIs and overview

        **🏢 COMPANY PROFILE**

        Detailed company analysis

        **🔎 SCREENER**

        Filter companies using financial metrics

        **👥 PEER COMPARISON**

        Compare companies within peer groups

        **📈 TRENDS**

        Historical financial trends

        **🏭 SECTORS**

        Sector-level analysis

        **💰 CAPITAL ALLOCATION**

        Capital allocation patterns

        **📄 ANNUAL REPORTS**

        Company reports and documents
        """
    )

    st.divider()

    st.caption("DATA UNIVERSE")
    st.metric("COMPANIES", "92")

    st.caption("DASHBOARD")
    st.caption("NIFTY 100 FINANCIAL ANALYTICS")


# ============================================================
# HOME CONTENT
# ============================================================

st.markdown(
    '<div class="main-header">NIFTY 100 FINANCIAL ANALYTICS</div>',
    unsafe_allow_html=True,
)

st.markdown(
    '<div class="sub-header">'
    "Explore financial performance, valuation, peers, sectors, "
    "trends and capital allocation across the NIFTY 100 universe."
    "</div>",
    unsafe_allow_html=True,
)


# ============================================================
# WELCOME CARDS
# ============================================================

col1, col2, col3 = st.columns(3)

with col1:
    st.markdown(
        """
        ### 🏠 MARKET OVERVIEW

        Track major financial KPIs across the 92-company
        NIFTY 100 analytics universe.
        """
    )

with col2:
    st.markdown(
        """
        ### 🔎 STOCK SCREENER

        Find companies using profitability, growth,
        valuation, leverage and dividend metrics.
        """
    )

with col3:
    st.markdown(
        """
        ### 📈 FINANCIAL ANALYSIS

        Explore historical revenue, profit, ROE, ROCE,
        cash flow and other financial indicators.
        """
    )


st.divider()


# ============================================================
# DASHBOARD MODULES
# ============================================================

st.subheader("DASHBOARD MODULES")

modules = [
    (
        "🏠 HOME",
        "Market overview, KPIs, sector distribution and top composite scores.",
    ),
    (
        "🏢 COMPANY PROFILE",
        "Detailed financial profile for any company in the universe.",
    ),
    (
        "🔎 SCREENER",
        "Apply multiple financial filters and export the results.",
    ),
    (
        "👥 PEER COMPARISON",
        "Compare companies against their defined peer groups.",
    ),
    (
        "📈 TRENDS",
        "Analyze long-term financial trends and year-over-year changes.",
    ),
    (
        "🏭 SECTORS",
        "Explore sector performance and company-level relationships.",
    ),
    (
        "💰 CAPITAL ALLOCATION",
        "Analyze how companies allocate capital across different patterns.",
    ),
    (
        "📄 ANNUAL REPORTS",
        "Access available company annual reports and documents.",
    ),
]


for i in range(0, len(modules), 2):

    left, right = st.columns(2)

    with left:
        title, description = modules[i]
        st.markdown(f"### {title}")
        st.write(description)

    if i + 1 < len(modules):

        with right:
            title, description = modules[i + 1]
            st.markdown(f"### {title}")
            st.write(description)


# ============================================================
# DATASET SUMMARY
# ============================================================

st.divider()

st.subheader("DATASET SUMMARY")

c1, c2, c3, c4 = st.columns(4)

with c1:
    st.metric("COMPANIES", "92")

with c2:
    st.metric("PEER GROUPS", "11")

with c3:
    st.metric("FINANCIAL HISTORY", "10+ YEARS")

with c4:
    st.metric("ANALYTICS MODULES", "8")


# ============================================================
# FOOTER
# ============================================================

st.markdown(
    """
    <div class="footer">
        NIFTY 100 FINANCIAL ANALYTICS DASHBOARD<br>
        Built with Python, SQLite, Pandas, Plotly and Streamlit
    </div>
    """,
    unsafe_allow_html=True,
)