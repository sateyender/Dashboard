import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

# =========================
# PAGE CONFIG
# =========================
st.set_page_config(
    page_title="Startup Pulse Dashboard",
    layout="wide",
    initial_sidebar_state="expanded"
)

# =========================
# CUSTOM CSS
# =========================
st.markdown("""
    <style>
    .stApp {
        background-color: #ffffff;
        color: #1e293b;
    }

    section[data-testid="stSidebar"] {
        background-color: #0f172a !important;
        color: #f8fafc !important;
    }

    section[data-testid="stSidebar"] * {
        color: #ffffff !important;
    }

    .metric-card {
        background-color: #f1f5f9;
        padding: 20px;
        border-radius: 12px;
        border-left: 5px solid #0f172a;
        text-align: center;
        box-shadow: 0 2px 8px rgba(0,0,0,0.06);
        margin-bottom: 10px;
    }

    .metric-value {
        font-size: 24px;
        font-weight: bold;
        color: #0f172a;
    }

    .metric-label {
        font-size: 13px;
        color: #64748b;
        text-transform: uppercase;
        margin-bottom: 6px;
    }

    .stTabs [data-baseweb="tab-list"] {
        gap: 10px;
    }

    .stTabs [data-baseweb="tab"] {
        min-height: 50px;
        background-color: #f1f5f9 !important;
        border-radius: 8px 8px 0 0;
        color: #334155 !important;
        font-weight: 600 !important;
        padding: 10px 18px;
    }

    .stTabs [data-baseweb="tab"] * {
        color: #334155 !important;
    }

    .stTabs [aria-selected="true"] {
        background-color: #0f172a !important;
        color: #ffffff !important;
    }

    .stTabs [aria-selected="true"] * {
        color: #ffffff !important;
    }
    </style>
""", unsafe_allow_html=True)

# =========================
# HELPERS
# =========================
CHART_COLOR = "#0f172a"
THEME_COLORS = ["#0f172a", "#334155", "#64748b", "#94a3b8", "#0d9488"]

def normalize_cols(df):
    df.columns = [
        str(c).lower().strip().replace(" ", "_").replace("-", "_")
        for c in df.columns
    ]
    return df

def safe_numeric(df, cols):
    for col in cols:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors="coerce")
    return df

def get_col(df, candidates):
    for c in candidates:
        if c in df.columns:
            return c
    return None

def metric_card(label, value):
    st.markdown(
        f"""
        <div class="metric-card">
            <div class="metric-label">{label}</div>
            <div class="metric-value">{value}</div>
        </div>
        """,
        unsafe_allow_html=True
    )

def apply_filters(df, industry_col=None, country_col=None, selected_industries=None, selected_countries=None):
    dff = df.copy()

    if selected_industries and industry_col:
        dff = dff[dff[industry_col].astype(str).isin(selected_industries)]

    if selected_countries and country_col:
        dff = dff[dff[country_col].astype(str).isin(selected_countries)]

    # Filter lagne ke baad empty ho gaya to crash na ho
    if dff.empty:
        return df.copy()

    return dff

# =========================
# DATA LOADING
# =========================
@st.cache_data
def load_data():
    try:
        india_df = pd.read_csv("india_startup_powerbi.csv")
        world_df = pd.read_csv("world_startup_powerbi.csv")
    except Exception as e:
        st.error(f"Error loading datasets: {e}")
        st.stop()

    india_df = normalize_cols(india_df)
    world_df = normalize_cols(world_df)

    numeric_cols = [
        "total_funding_musd",
        "annual_revenue_musd",
        "burn_rate_musd",
        "revenue_growth_percent",
        "employee_count",
        "valuation_musd",
        "is_ipo",
        "annual_profit_musd",
        "is_profitable"
    ]

    india_df = safe_numeric(india_df, numeric_cols)
    world_df = safe_numeric(world_df, numeric_cols)

    return india_df, world_df

india_raw, world_raw = load_data()

# =========================
# COLUMN REFERENCES
# =========================
INDUSTRY_COL_I = get_col(india_raw, ["industry"])
COUNTRY_COL_I = get_col(india_raw, ["country"])
STAGE_COL_I = get_col(india_raw, ["funding_stage"])

INDUSTRY_COL_W = get_col(world_raw, ["industry"])
COUNTRY_COL_W = get_col(world_raw, ["country"])
STAGE_COL_W = get_col(world_raw, ["funding_stage"])

FUNDING_COL = "total_funding_musd"
VALUATION_COL = "valuation_musd"
REVENUE_COL = "annual_revenue_musd"
BURN_COL = "burn_rate_musd"
GROWTH_COL = "revenue_growth_percent"
EMP_COL = "employee_count"
IPO_COL = "is_ipo"
PROFIT_COL = "is_profitable"
PROFIT_AMT_COL = "annual_profit_musd"

# =========================
# WORLD EXCLUDING INDIA
# =========================
if COUNTRY_COL_W:
    world_exclusive = world_raw[
        world_raw[COUNTRY_COL_W].astype(str).str.strip().str.lower() != "india"
    ].copy()
else:
    world_exclusive = world_raw.copy()

# =========================
# SIDEBAR FILTERS
# =========================
st.sidebar.title("Startup Pulse Dashboard")
st.sidebar.markdown("Filter startup ecosystem insights dynamically.")

all_industries = []

if INDUSTRY_COL_I:
    all_industries.extend(india_raw[INDUSTRY_COL_I].dropna().astype(str).unique().tolist())
if INDUSTRY_COL_W:
    all_industries.extend(world_exclusive[INDUSTRY_COL_W].dropna().astype(str).unique().tolist())

all_industries = sorted(list(set(all_industries)))

selected_industries = st.sidebar.multiselect(
    "Select Industry / Sector",
    options=all_industries,
    default=[]
)

all_countries = []
if COUNTRY_COL_W:
    all_countries = sorted(world_exclusive[COUNTRY_COL_W].dropna().astype(str).unique().tolist())

selected_countries = st.sidebar.multiselect(
    "Select Countries (World Only)",
    options=all_countries,
    default=[]
)



# =========================
# TABS
# =========================
tab1, tab2, tab3 = st.tabs([
    "🇮🇳 India Dashboard",
    "World Dashboard",
    " India vs World Comparison"
])

# ============================================================
# TAB 1: INDIA DASHBOARD
# ============================================================
with tab1:
    st.subheader("India Startup Ecosystem")

    df_i = apply_filters(
        india_raw,
        industry_col=INDUSTRY_COL_I,
        selected_industries=selected_industries
    )

    # KPIs
    k1, k2, k3, k4 = st.columns(4)

    with k1:
        metric_card("Total Startups", f"{len(df_i):,}")

    with k2:
        total_funding_india = df_i[FUNDING_COL].sum() if FUNDING_COL in df_i.columns else 0
        metric_card("Total Funding", f"$ {total_funding_india:,.1f}M")

    with k3:
        avg_valuation_india = df_i[VALUATION_COL].mean() if VALUATION_COL in df_i.columns else 0
        metric_card("Avg Valuation", f"$ {avg_valuation_india:,.1f}M")

    with k4:
        profitable_india = (df_i[PROFIT_COL] == 1).sum() if PROFIT_COL in df_i.columns else 0
        metric_card("Profitable Startups", f"{profitable_india:,}")

    st.write("---")

    # Row 1
    c1, c2 = st.columns(2)

    with c1:
        # Replacement for year line chart
        if STAGE_COL_I and FUNDING_COL in df_i.columns:
            stage_funding = df_i.groupby(STAGE_COL_I, dropna=False)[FUNDING_COL].sum().reset_index()
            stage_funding.columns = ["Funding Stage", "Total Funding"]
            stage_funding = stage_funding.sort_values("Total Funding", ascending=False)

            fig = px.bar(
                stage_funding,
                x="Funding Stage",
                y="Total Funding",
                title="Funding by Stage (India)",
                color_discrete_sequence=[CHART_COLOR]
            )
            st.plotly_chart(fig, use_container_width=True)

    with c2:
        if INDUSTRY_COL_I:
            sector_share = df_i[INDUSTRY_COL_I].value_counts().reset_index()
            sector_share.columns = ["Industry", "Count"]

            fig = px.pie(
                sector_share,
                names="Industry",
                values="Count",
                hole=0.5,
                title="Industry Share (India)",
                color_discrete_sequence=THEME_COLORS
            )
            st.plotly_chart(fig, use_container_width=True)

    # Row 2
    c3, c4 = st.columns(2)

    with c3:
        if INDUSTRY_COL_I and FUNDING_COL in df_i.columns:
            top_funded = df_i.groupby(INDUSTRY_COL_I, dropna=False)[FUNDING_COL].sum().reset_index()
            top_funded.columns = ["Industry", "Funding"]
            top_funded = top_funded.sort_values("Funding", ascending=False).head(10)

            fig = px.bar(
                top_funded,
                x="Industry",
                y="Funding",
                title="Top 10 Funded Sectors (India)",
                color_discrete_sequence=[THEME_COLORS[4]]
            )
            fig.update_layout(xaxis_title="Industry", yaxis_title="Funding (M USD)")
            st.plotly_chart(fig, use_container_width=True)

    with c4:
        # REPLACED Top 10 Hubs
        if INDUSTRY_COL_I:
            top_industries = df_i[INDUSTRY_COL_I].value_counts().head(10).reset_index()
            top_industries.columns = ["Industry", "Startup Count"]

            fig = px.bar(
                top_industries,
                x="Industry",
                y="Startup Count",
                title="Top 10 Industries by Startup Count (India)",
                color_discrete_sequence=[THEME_COLORS[2]]
            )
            fig.update_layout(xaxis_title="Industry", yaxis_title="Number of Startups")
            st.plotly_chart(fig, use_container_width=True)

    # Row 3
    c5, c6 = st.columns(2)

    with c5:
        # Added second requested extra chart style replacement
        if REVENUE_COL in df_i.columns and PROFIT_COL in df_i.columns:
            profit_compare = pd.DataFrame({
                "Status": ["Profitable", "Non-Profitable"],
                "Average Revenue": [
                    df_i[df_i[PROFIT_COL] == 1][REVENUE_COL].mean() if not df_i[df_i[PROFIT_COL] == 1].empty else 0,
                    df_i[df_i[PROFIT_COL] == 0][REVENUE_COL].mean() if not df_i[df_i[PROFIT_COL] == 0].empty else 0
                ]
            })

            fig = px.bar(
                profit_compare,
                x="Status",
                y="Average Revenue",
                title="Profit vs Non-Profit Revenue Comparison (India)",
                color="Status",
                color_discrete_sequence=[CHART_COLOR, "#94a3b8"]
            )
            fig.update_layout(xaxis_title="Startup Type", yaxis_title="Average Revenue (M USD)")
            st.plotly_chart(fig, use_container_width=True)

    with c6:
        if PROFIT_COL in df_i.columns:
            profit_counts = pd.DataFrame({
                "Status": ["Profitable", "Not Profitable"],
                "Count": [
                    (df_i[PROFIT_COL] == 1).sum(),
                    (df_i[PROFIT_COL] == 0).sum()
                ]
            })

            fig = px.bar(
                profit_counts,
                x="Status",
                y="Count",
                title="Profitability Split (India)",
                color="Status",
                color_discrete_sequence=[CHART_COLOR, "#94a3b8"]
            )
            st.plotly_chart(fig, use_container_width=True)

# ============================================================
# TAB 2: WORLD DASHBOARD
# ============================================================
with tab2:
    st.subheader("Global Startup Ecosystem (Excluding India)")

    df_w = apply_filters(
        world_exclusive,
        industry_col=INDUSTRY_COL_W,
        country_col=COUNTRY_COL_W,
        selected_industries=selected_industries,
        selected_countries=selected_countries
    )

    # KPIs
    wk1, wk2, wk3, wk4 = st.columns(4)

    with wk1:
        metric_card("Global Startups", f"{len(df_w):,}")

    with wk2:
        total_funding_world = df_w[FUNDING_COL].sum() if FUNDING_COL in df_w.columns else 0
        metric_card("Global Funding", f"$ {total_funding_world:,.1f}M")

    with wk3:
        total_valuation_world = df_w[VALUATION_COL].sum() if VALUATION_COL in df_w.columns else 0
        metric_card("Total Ecosystem Value", f"$ {total_valuation_world:,.1f}M")

    with wk4:
        profitable_world = (df_w[PROFIT_COL] == 1).sum() if PROFIT_COL in df_w.columns else 0
        metric_card("Profitable Startups", f"{profitable_world:,}")

    st.write("---")

    # Map
    if COUNTRY_COL_W:
        geo = df_w[COUNTRY_COL_W].value_counts().reset_index()
        geo.columns = ["Country", "Count"]

        fig = px.choropleth(
            geo,
            locations="Country",
            locationmode="country names",
            color="Count",
            title="Global Geographic Distribution",
            color_continuous_scale="Blues"
        )
        st.plotly_chart(fig, use_container_width=True)

    # Row 1
    c7, c8 = st.columns(2)

    with c7:
        if COUNTRY_COL_W and FUNDING_COL in df_w.columns:
            top_countries = df_w.groupby(COUNTRY_COL_W, dropna=False)[FUNDING_COL].sum().reset_index()
            top_countries.columns = ["Country", "Funding"]
            top_countries = top_countries.sort_values("Funding", ascending=False).head(10)

            fig = px.bar(
                top_countries,
                x="Country",
                y="Funding",
                title="Top 10 Funded Countries",
                color_discrete_sequence=[CHART_COLOR]
            )
            st.plotly_chart(fig, use_container_width=True)

    with c8:
        if INDUSTRY_COL_W:
            global_sector = df_w[INDUSTRY_COL_W].value_counts().reset_index()
            global_sector.columns = ["Industry", "Count"]

            fig = px.pie(
                global_sector,
                names="Industry",
                values="Count",
                title="Global Industry Share",
                color_discrete_sequence=THEME_COLORS
            )
            fig.update_traces(textinfo="percent+label")
            st.plotly_chart(fig, use_container_width=True)

    # Row 2
    c9, c10 = st.columns(2)

    with c9:
        # Added requested "line chart" feel without year column
        if COUNTRY_COL_W and REVENUE_COL in df_w.columns:
            country_revenue = df_w.groupby(COUNTRY_COL_W, dropna=False)[REVENUE_COL].sum().reset_index()
            country_revenue.columns = ["Country", "Revenue"]
            country_revenue = country_revenue.sort_values("Revenue", ascending=False).head(10)

            fig = px.line(
                country_revenue,
                x="Country",
                y="Revenue",
                markers=True,
                title="Top 10 Countries by Revenue (World)",
                color_discrete_sequence=[THEME_COLORS[4]]
            )
            fig.update_layout(xaxis_title="Country", yaxis_title="Revenue (M USD)")
            st.plotly_chart(fig, use_container_width=True)

    with c10:
        if STAGE_COL_W:
            global_stage = df_w[STAGE_COL_W].value_counts().reset_index()
            global_stage.columns = ["Funding Stage", "Count"]

            fig = px.bar(
                global_stage,
                x="Funding Stage",
                y="Count",
                title="Global Funding Stage Distribution",
                color_discrete_sequence=[THEME_COLORS[1]]
            )
            st.plotly_chart(fig, use_container_width=True)

# ============================================================
# TAB 3: INDIA VS WORLD COMPARISON
# ============================================================
with tab3:
    st.subheader("India vs Rest of World Comparison")

    df_comp_i = apply_filters(
        india_raw,
        industry_col=INDUSTRY_COL_I,
        selected_industries=selected_industries
    )

    df_comp_w = apply_filters(
        world_exclusive,
        industry_col=INDUSTRY_COL_W,
        selected_industries=selected_industries
    )

    # KPIs
    ck1, ck2, ck3, ck4 = st.columns(4)

    with ck1:
        density = ((len(df_comp_i) / len(df_comp_w)) * 100) if len(df_comp_w) > 0 else 0
        metric_card("India Startup Density", f"{density:.1f}% of Rest of World")

    with ck2:
        avg_f_i = df_comp_i[FUNDING_COL].mean() if FUNDING_COL in df_comp_i.columns else 0
        avg_f_w = df_comp_w[FUNDING_COL].mean() if FUNDING_COL in df_comp_w.columns else 0
        metric_card("Avg Funding", f"{avg_f_i:,.1f}M vs {avg_f_w:,.1f}M")

    with ck3:
        avg_v_i = df_comp_i[VALUATION_COL].mean() if VALUATION_COL in df_comp_i.columns else 0
        avg_v_w = df_comp_w[VALUATION_COL].mean() if VALUATION_COL in df_comp_w.columns else 0
        gap = (((avg_v_i / avg_v_w) - 1) * 100) if avg_v_w > 0 else 0
        metric_card("Avg Valuation Gap", f"{gap:,.1f}%")

    with ck4:
        india_prof = (df_comp_i[PROFIT_COL] == 1).sum() if PROFIT_COL in df_comp_i.columns else 0
        world_prof = (df_comp_w[PROFIT_COL] == 1).sum() if PROFIT_COL in df_comp_w.columns else 0
        metric_card("Profitable (India vs World)", f"{india_prof:,} vs {world_prof:,}")

    st.write("---")

    # Benchmark chart
    bench_data = pd.DataFrame({
        "Market": ["India", "Rest of World", "India", "Rest of World"],
        "Metric": ["Startup Count", "Startup Count", "Total Funding", "Total Funding"],
        "Value": [
            len(df_comp_i),
            len(df_comp_w),
            df_comp_i[FUNDING_COL].sum() if FUNDING_COL in df_comp_i.columns else 0,
            df_comp_w[FUNDING_COL].sum() if FUNDING_COL in df_comp_w.columns else 0
        ]
    })

    fig = px.bar(
        bench_data,
        x="Metric",
        y="Value",
        color="Market",
        barmode="group",
        title="Ecosystem Benchmark: India vs Rest of World",
        color_discrete_sequence=[CHART_COLOR, "#64748b"]
    )
    st.plotly_chart(fig, use_container_width=True)

    # Row 1
    c11, c12 = st.columns(2)

    with c11:
        # Requested "line chart" for comparison
        compare_line = pd.DataFrame({
            "Metric": ["Startup Count", "Total Funding", "Total Revenue", "Profitable Startups"],
            "India": [
                len(df_comp_i),
                df_comp_i[FUNDING_COL].sum() if FUNDING_COL in df_comp_i.columns else 0,
                df_comp_i[REVENUE_COL].sum() if REVENUE_COL in df_comp_i.columns else 0,
                (df_comp_i[PROFIT_COL] == 1).sum() if PROFIT_COL in df_comp_i.columns else 0
            ],
            "Rest of World": [
                len(df_comp_w),
                df_comp_w[FUNDING_COL].sum() if FUNDING_COL in df_comp_w.columns else 0,
                df_comp_w[REVENUE_COL].sum() if REVENUE_COL in df_comp_w.columns else 0,
                (df_comp_w[PROFIT_COL] == 1).sum() if PROFIT_COL in df_comp_w.columns else 0
            ]
        })

        fig = go.Figure()
        fig.add_trace(go.Scatter(
            x=compare_line["Metric"],
            y=compare_line["India"],
            mode="lines+markers",
            name="India",
            line=dict(color=CHART_COLOR)
        ))
        fig.add_trace(go.Scatter(
            x=compare_line["Metric"],
            y=compare_line["Rest of World"],
            mode="lines+markers",
            name="Rest of World",
            line=dict(color="#0d9488")
        ))
        fig.update_layout(title="India vs World Multi-Metric Line Comparison")
        st.plotly_chart(fig, use_container_width=True)

    with c12:
        if INDUSTRY_COL_I and VALUATION_COL in df_comp_i.columns and INDUSTRY_COL_W and VALUATION_COL in df_comp_w.columns:
            india_val = df_comp_i.groupby(INDUSTRY_COL_I, dropna=False)[VALUATION_COL].mean().reset_index()
            india_val.columns = ["Industry", "India Avg Valuation"]

            world_val = df_comp_w.groupby(INDUSTRY_COL_W, dropna=False)[VALUATION_COL].mean().reset_index()
            world_val.columns = ["Industry", "World Avg Valuation"]

            val_merge = pd.merge(india_val, world_val, on="Industry", how="inner")
            val_merge = val_merge.sort_values("India Avg Valuation", ascending=False).head(8)

            if not val_merge.empty:
                fig = go.Figure(data=[
                    go.Bar(
                        name="India Avg Valuation",
                        x=val_merge["Industry"],
                        y=val_merge["India Avg Valuation"],
                        marker_color=CHART_COLOR
                    ),
                    go.Bar(
                        name="World Avg Valuation",
                        x=val_merge["Industry"],
                        y=val_merge["World Avg Valuation"],
                        marker_color="#64748b"
                    )
                ])
                fig.update_layout(
                    title="Average Valuation by Sector: India vs World",
                    barmode="group"
                )
                st.plotly_chart(fig, use_container_width=True)

    # Row 2
    c13, c14 = st.columns(2)

    with c13:
        if INDUSTRY_COL_I and INDUSTRY_COL_W:
            i_top = df_comp_i[INDUSTRY_COL_I].value_counts(normalize=True).head(5).reset_index()
            i_top.columns = ["Industry", "India Share"]

            w_top = df_comp_w[INDUSTRY_COL_W].value_counts(normalize=True).head(5).reset_index()
            w_top.columns = ["Industry", "World Share"]

            merged = pd.merge(i_top, w_top, on="Industry", how="outer").fillna(0)

            fig = go.Figure(data=[
                go.Bar(
                    name="India Share %",
                    x=merged["Industry"],
                    y=merged["India Share"] * 100,
                    marker_color=CHART_COLOR
                ),
                go.Bar(
                    name="World Share %",
                    x=merged["Industry"],
                    y=merged["World Share"] * 100,
                    marker_color="#0d9488"
                )
            ])
            fig.update_layout(
                title="Top Sector Penetration Comparison (%)",
                barmode="group"
            )
            st.plotly_chart(fig, use_container_width=True)

    with c14:
        if REVENUE_COL in df_comp_i.columns and REVENUE_COL in df_comp_w.columns:
            revenue_compare = pd.DataFrame({
                "Market": ["India", "Rest of World"],
                "Total Revenue": [
                    df_comp_i[REVENUE_COL].sum(),
                    df_comp_w[REVENUE_COL].sum()
                ]
            })

            fig = px.bar(
                revenue_compare,
                x="Market",
                y="Total Revenue",
                title="Revenue Comparison: India vs World",
                color="Market",
                color_discrete_sequence=[CHART_COLOR, "#94a3b8"]
            )
            st.plotly_chart(fig, use_container_width=True)

# =========================
# FOOTER
# =========================
