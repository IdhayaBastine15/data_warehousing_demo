"""
Cost of Living Experimentation Platform — Streamlit Dashboard
Reads directly from cost_of_living_demo.db (SQLite).
"""
import os
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import streamlit as st
from sqlalchemy import create_engine

# ── Page config ───────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="Cost of Living Platform",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ── Theme colours ─────────────────────────────────────────────────────────────
REGION_COLORS = {
    "West":      "#7C3AED",
    "Northeast": "#06B6D4",
    "Southeast": "#F59E0B",
    "Midwest":   "#10B981",
    "Southwest": "#EF4444",
}

COST_COLORS = {
    "avg_housing_cost":        "#7C3AED",
    "avg_transportation_cost": "#06B6D4",
    "avg_healthcare_cost":     "#EF4444",
    "avg_food_cost":           "#10B981",
    "avg_childcare_cost":      "#F59E0B",
}

COST_LABELS = {
    "avg_housing_cost":        "Housing",
    "avg_transportation_cost": "Transportation",
    "avg_healthcare_cost":     "Healthcare",
    "avg_food_cost":           "Food",
    "avg_childcare_cost":      "Childcare",
}

# ── Custom CSS ────────────────────────────────────────────────────────────────
st.markdown("""
<style>
/* Main background */
.main .block-container { padding-top: 1.5rem; }

/* KPI cards */
.kpi-card {
    background: linear-gradient(135deg, #1E1E2E 0%, #2A2A3E 100%);
    border: 1px solid #3F3F5A;
    border-radius: 12px;
    padding: 18px 22px;
    text-align: center;
}
.kpi-value {
    font-size: 2rem;
    font-weight: 700;
    color: #7C3AED;
    line-height: 1.1;
}
.kpi-label {
    font-size: 0.78rem;
    color: #9CA3AF;
    margin-top: 4px;
    text-transform: uppercase;
    letter-spacing: 0.05em;
}
.kpi-delta {
    font-size: 0.85rem;
    color: #10B981;
    margin-top: 2px;
}

/* Section headers */
.section-header {
    background: linear-gradient(90deg, #7C3AED22 0%, transparent 100%);
    border-left: 4px solid #7C3AED;
    padding: 8px 14px;
    border-radius: 0 8px 8px 0;
    margin-bottom: 1rem;
}

/* Sidebar */
[data-testid="stSidebar"] { background-color: #1E1E2E; }
[data-testid="stSidebar"] .stRadio label { color: #E2E8F0 !important; }
</style>
""", unsafe_allow_html=True)

# ── Data loading ──────────────────────────────────────────────────────────────
DB_URL = os.getenv("DATABASE_URL", "sqlite:///cost_of_living_demo.db")

@st.cache_data
def load_data():
    engine = create_engine(DB_URL)
    regional = pd.read_sql("SELECT * FROM regional_cost_statistics ORDER BY avg_total_cost DESC", engine)
    processed = pd.read_sql("SELECT * FROM cost_of_living_processed", engine)
    experiments = pd.read_sql("SELECT * FROM experiment_results", engine)
    return regional, processed, experiments

regional, processed, experiments = load_data()

# ── Sidebar ───────────────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown("## 📊 Navigation")
    page = st.radio(
        "",
        ["🏠 Overview", "🗺️ Regional Analysis", "🏙️ State Explorer", "🧪 A/B Experiments"],
        label_visibility="collapsed",
    )
    st.markdown("---")
    st.markdown("### 🔍 Filters")
    selected_regions = st.multiselect(
        "Regions",
        options=sorted(regional["region"].tolist()),
        default=sorted(regional["region"].tolist()),
    )
    st.markdown("---")
    st.markdown(
        "<div style='color:#6B7280;font-size:0.75rem;'>"
        "📁 Source: EPI Family Budget Calculator<br>"
        "🗄️ SQLite · PySpark ETL · FastAPI<br>"
        "🔬 Welch t-test · Cohen's d · 95% CI"
        "</div>",
        unsafe_allow_html=True,
    )

# Filter dataframes by selected regions
regional_f   = regional[regional["region"].isin(selected_regions)]
processed_f  = processed[processed["region"].isin(selected_regions)]
experiments_f = experiments[
    experiments["control_region"].isin(selected_regions) &
    experiments["treatment_region"].isin(selected_regions)
]


# ═══════════════════════════════════════════════════════════════════════════════
# PAGE 1 — OVERVIEW
# ═══════════════════════════════════════════════════════════════════════════════
if page == "🏠 Overview":
    st.markdown("# 📊 Cost of Living Experimentation Platform")
    st.markdown("*US county-level cost-of-living data · PySpark ETL pipeline · Statistical A/B testing*")
    st.markdown("---")

    # KPI row
    most_exp  = regional.iloc[0]
    least_exp = regional.iloc[-1]
    best_aff  = regional.loc[regional["avg_affordability_ratio"].idxmax()]
    sig_count = int(experiments["significant"].sum())
    total_exp = len(experiments)

    k1, k2, k3, k4, k5 = st.columns(5)
    for col, val, label, delta in [
        (k1, f"{len(processed):,}", "Counties Analysed",   "from 3,000 source rows"),
        (k2, f"${most_exp['avg_total_cost']:,.0f}", "Highest Avg Cost / yr", most_exp["region"]),
        (k3, f"${least_exp['avg_total_cost']:,.0f}", "Lowest Avg Cost / yr", least_exp["region"]),
        (k4, f"{best_aff['avg_affordability_ratio']:.2f}×", "Best Affordability Ratio", best_aff["region"]),
        (k5, f"{sig_count}/{total_exp}", "Significant Experiments", "at p < 0.05"),
    ]:
        col.markdown(
            f"<div class='kpi-card'>"
            f"<div class='kpi-value'>{val}</div>"
            f"<div class='kpi-label'>{label}</div>"
            f"<div class='kpi-delta'>{delta}</div>"
            f"</div>",
            unsafe_allow_html=True,
        )

    st.markdown("<br>", unsafe_allow_html=True)

    # ── Row 1: Total cost bar + affordability bar ─────────────────────────────
    col_left, col_right = st.columns(2)

    with col_left:
        st.markdown("<div class='section-header'><b>Average Annual Cost of Living by Region</b></div>",
                    unsafe_allow_html=True)
        fig = px.bar(
            regional_f.sort_values("avg_total_cost", ascending=True),
            x="avg_total_cost", y="region",
            orientation="h",
            color="region",
            color_discrete_map=REGION_COLORS,
            text="avg_total_cost",
            template="plotly_dark",
        )
        fig.update_traces(
            texttemplate="$%{text:,.0f}",
            textposition="outside",
            marker_line_width=0,
        )
        fig.update_layout(
            showlegend=False, xaxis_title="Annual Cost (USD)",
            yaxis_title="", plot_bgcolor="#1E1E2E",
            paper_bgcolor="#1E1E2E", height=320,
            margin=dict(l=0, r=60, t=10, b=10),
        )
        fig.update_xaxes(tickprefix="$", tickformat=",")
        st.plotly_chart(fig, use_container_width=True)

    with col_right:
        st.markdown("<div class='section-header'><b>Affordability Ratio — Income vs Cost of Living</b></div>",
                    unsafe_allow_html=True)
        fig2 = px.bar(
            regional_f.sort_values("avg_affordability_ratio", ascending=True),
            x="avg_affordability_ratio", y="region",
            orientation="h",
            color="avg_affordability_ratio",
            color_continuous_scale=["#EF4444", "#F59E0B", "#10B981"],
            text="avg_affordability_ratio",
            template="plotly_dark",
        )
        fig2.update_traces(
            texttemplate="%{text:.2f}×",
            textposition="outside",
            marker_line_width=0,
        )
        fig2.update_layout(
            showlegend=False, xaxis_title="Affordability Ratio (income ÷ total cost)",
            yaxis_title="", plot_bgcolor="#1E1E2E",
            paper_bgcolor="#1E1E2E", height=320,
            margin=dict(l=0, r=60, t=10, b=10),
            coloraxis_showscale=False,
        )
        st.plotly_chart(fig2, use_container_width=True)

    # ── Row 2: Stacked cost breakdown + scatter ───────────────────────────────
    st.markdown("<div class='section-header'><b>Annual Cost Breakdown by Category and Region</b></div>",
                unsafe_allow_html=True)

    cost_cols = list(COST_LABELS.keys())
    melt = regional_f.melt(id_vars="region", value_vars=cost_cols,
                           var_name="category", value_name="cost")
    melt["category_label"] = melt["category"].map(COST_LABELS)

    fig3 = px.bar(
        melt,
        x="region", y="cost",
        color="category_label",
        barmode="group",
        color_discrete_sequence=list(COST_COLORS.values()),
        template="plotly_dark",
        text="cost",
    )
    fig3.update_traces(texttemplate="$%{text:,.0f}", textposition="outside", textfont_size=9)
    fig3.update_layout(
        xaxis_title="", yaxis_title="Annual Cost (USD)",
        plot_bgcolor="#1E1E2E", paper_bgcolor="#1E1E2E",
        height=380, legend_title="Category",
        margin=dict(l=0, r=0, t=10, b=10),
    )
    fig3.update_yaxes(tickprefix="$", tickformat=",")
    st.plotly_chart(fig3, use_container_width=True)

    # ── Row 3: Income vs Cost scatter ─────────────────────────────────────────
    st.markdown("<div class='section-header'><b>Median Income vs Total Cost — County Level</b></div>",
                unsafe_allow_html=True)

    scatter_df = processed_f[processed_f["region"] != "Other"].copy()
    fig4 = px.scatter(
        scatter_df,
        x="total_cost", y="median_family_income",
        color="region",
        color_discrete_map=REGION_COLORS,
        size="total_cost",
        size_max=8,
        hover_name="county",
        hover_data={"state": True, "total_cost": ":$,.0f",
                    "median_family_income": ":$,.0f", "region": False},
        template="plotly_dark",
        opacity=0.65,
    )
    # Break-even line
    min_v = min(scatter_df["total_cost"].min(), scatter_df["median_family_income"].min())
    max_v = max(scatter_df["total_cost"].max(), scatter_df["median_family_income"].max())
    fig4.add_shape(type="line", x0=min_v, y0=min_v, x1=max_v, y1=max_v,
                   line=dict(color="#6B7280", dash="dash", width=1.5))
    fig4.add_annotation(x=max_v * 0.9, y=max_v * 0.92,
                        text="Break-even line",
                        showarrow=False, font=dict(color="#9CA3AF", size=11))
    fig4.update_layout(
        xaxis_title="Annual Total Cost (USD)",
        yaxis_title="Median Family Income (USD)",
        plot_bgcolor="#1E1E2E", paper_bgcolor="#1E1E2E",
        height=420, margin=dict(l=0, r=0, t=10, b=10),
    )
    fig4.update_xaxes(tickprefix="$", tickformat=",")
    fig4.update_yaxes(tickprefix="$", tickformat=",")
    st.plotly_chart(fig4, use_container_width=True)


# ═══════════════════════════════════════════════════════════════════════════════
# PAGE 2 — REGIONAL ANALYSIS
# ═══════════════════════════════════════════════════════════════════════════════
elif page == "🗺️ Regional Analysis":
    st.markdown("# 🗺️ Regional Cost Analysis")
    st.markdown("*Deep-dive into each US Census region's cost structure*")
    st.markdown("---")

    # ── Radar chart ───────────────────────────────────────────────────────────
    st.markdown("<div class='section-header'><b>Cost Category Radar — Region Profiles</b></div>",
                unsafe_allow_html=True)

    categories = list(COST_LABELS.values())
    cols_order  = list(COST_LABELS.keys())

    fig_radar = go.Figure()
    for _, row in regional_f.iterrows():
        values = [row[c] for c in cols_order]
        values.append(values[0])
        fig_radar.add_trace(go.Scatterpolar(
            r=values,
            theta=categories + [categories[0]],
            fill="toself",
            name=row["region"],
            line_color=REGION_COLORS.get(row["region"], "#888"),
            opacity=0.6,
        ))
    fig_radar.update_layout(
        polar=dict(
            bgcolor="#1E1E2E",
            radialaxis=dict(visible=True, tickprefix="$", tickformat=",",
                            gridcolor="#3F3F5A", color="#9CA3AF"),
            angularaxis=dict(gridcolor="#3F3F5A", color="#E2E8F0"),
        ),
        paper_bgcolor="#1E1E2E", template="plotly_dark",
        height=480, legend=dict(x=1.05, y=0.5),
        margin=dict(l=60, r=140, t=20, b=20),
    )
    st.plotly_chart(fig_radar, use_container_width=True)

    # ── Two columns: treemap + county distribution ────────────────────────────
    c1, c2 = st.columns(2)

    with c1:
        st.markdown("<div class='section-header'><b>Cost Composition Treemap</b></div>",
                    unsafe_allow_html=True)
        melt2 = regional_f.melt(id_vars="region", value_vars=list(COST_LABELS.keys()),
                                var_name="category", value_name="cost")
        melt2["label"] = melt2["category"].map(COST_LABELS)

        fig_tree = px.treemap(
            melt2, path=["region", "label"], values="cost",
            color="cost",
            color_continuous_scale=["#1E1E2E", "#7C3AED", "#06B6D4"],
            template="plotly_dark",
        )
        fig_tree.update_traces(
            texttemplate="<b>%{label}</b><br>$%{value:,.0f}",
            textfont_size=11,
        )
        fig_tree.update_layout(
            paper_bgcolor="#1E1E2E", height=400,
            margin=dict(l=0, r=0, t=10, b=0),
            coloraxis_showscale=False,
        )
        st.plotly_chart(fig_tree, use_container_width=True)

    with c2:
        st.markdown("<div class='section-header'><b>County Count & Avg Income by Region</b></div>",
                    unsafe_allow_html=True)

        fig_duo = make_subplots(specs=[[{"secondary_y": True}]])
        fig_duo.add_trace(
            go.Bar(
                x=regional_f["region"],
                y=regional_f["county_count"],
                name="County Count",
                marker_color=[REGION_COLORS.get(r, "#888") for r in regional_f["region"]],
                opacity=0.8,
            ),
            secondary_y=False,
        )
        fig_duo.add_trace(
            go.Scatter(
                x=regional_f["region"],
                y=regional_f["avg_median_income"],
                name="Avg Median Income",
                mode="lines+markers",
                line=dict(color="#F59E0B", width=2.5),
                marker=dict(size=9, color="#F59E0B"),
            ),
            secondary_y=True,
        )
        fig_duo.update_layout(
            template="plotly_dark", paper_bgcolor="#1E1E2E",
            plot_bgcolor="#1E1E2E", height=400,
            legend=dict(x=0, y=1),
            margin=dict(l=0, r=10, t=10, b=10),
        )
        fig_duo.update_yaxes(title_text="County Count", secondary_y=False,
                             gridcolor="#3F3F5A")
        fig_duo.update_yaxes(title_text="Avg Median Income (USD)", secondary_y=True,
                             tickprefix="$", tickformat=",")
        st.plotly_chart(fig_duo, use_container_width=True)

    # ── Distribution box plots ─────────────────────────────────────────────────
    st.markdown("<div class='section-header'><b>County-Level Cost Distribution by Region</b></div>",
                unsafe_allow_html=True)

    metric_choice = st.selectbox(
        "Select cost metric",
        ["total_cost", "housing_cost", "food_cost",
         "healthcare_cost", "transportation_cost", "median_family_income"],
        format_func=lambda x: x.replace("_", " ").title(),
    )
    box_df = processed_f[processed_f["region"] != "Other"]
    fig_box = px.box(
        box_df, x="region", y=metric_choice,
        color="region",
        color_discrete_map=REGION_COLORS,
        points="outliers",
        template="plotly_dark",
    )
    fig_box.update_layout(
        xaxis_title="", yaxis_title=metric_choice.replace("_", " ").title() + " (USD)",
        plot_bgcolor="#1E1E2E", paper_bgcolor="#1E1E2E",
        height=400, showlegend=False,
        margin=dict(l=0, r=0, t=10, b=10),
    )
    fig_box.update_yaxes(tickprefix="$", tickformat=",")
    st.plotly_chart(fig_box, use_container_width=True)


# ═══════════════════════════════════════════════════════════════════════════════
# PAGE 3 — STATE EXPLORER
# ═══════════════════════════════════════════════════════════════════════════════
elif page == "🏙️ State Explorer":
    st.markdown("# 🏙️ State-Level Explorer")
    st.markdown("*Drill down to individual states and counties*")
    st.markdown("---")

    # State aggregates
    state_df = (
        processed_f[processed_f["region"] != "Other"]
        .groupby(["state", "region"])
        .agg(
            avg_total_cost=("total_cost", "mean"),
            avg_housing_cost=("housing_cost", "mean"),
            avg_food_cost=("food_cost", "mean"),
            avg_healthcare_cost=("healthcare_cost", "mean"),
            avg_transportation_cost=("transportation_cost", "mean"),
            avg_median_income=("median_family_income", "mean"),
            avg_affordability_ratio=("affordability_ratio", "mean"),
            county_count=("total_cost", "count"),
        )
        .round(2)
        .reset_index()
    )

    # ── Top / bottom 10 toggle ────────────────────────────────────────────────
    c1, c2 = st.columns([3, 1])
    with c1:
        sort_metric = st.selectbox(
            "Sort states by",
            ["avg_total_cost", "avg_housing_cost", "avg_median_income",
             "avg_affordability_ratio", "avg_healthcare_cost"],
            format_func=lambda x: x.replace("avg_", "").replace("_", " ").title(),
        )
    with c2:
        top_n = st.slider("Top N states", 5, 30, 15)

    top_states = state_df.sort_values(sort_metric, ascending=False).head(top_n)

    fig_states = px.bar(
        top_states.sort_values(sort_metric, ascending=True),
        x=sort_metric, y="state",
        orientation="h",
        color="region",
        color_discrete_map=REGION_COLORS,
        text=sort_metric,
        template="plotly_dark",
        hover_data={"county_count": True, "avg_affordability_ratio": ":.2f"},
    )
    fig_states.update_traces(
        texttemplate="$%{text:,.0f}" if "ratio" not in sort_metric else "%{text:.2f}×",
        textposition="outside",
    )
    fig_states.update_layout(
        plot_bgcolor="#1E1E2E", paper_bgcolor="#1E1E2E",
        xaxis_title=sort_metric.replace("_", " ").title(),
        yaxis_title="", height=max(350, top_n * 28),
        margin=dict(l=0, r=80, t=10, b=10),
    )
    if "ratio" not in sort_metric:
        fig_states.update_xaxes(tickprefix="$", tickformat=",")
    st.plotly_chart(fig_states, use_container_width=True)

    # ── County drill-down ─────────────────────────────────────────────────────
    st.markdown("<div class='section-header'><b>County Drill-Down</b></div>",
                unsafe_allow_html=True)

    state_list = sorted(processed_f["state"].dropna().unique().tolist())
    sel_state = st.selectbox("Select a state", state_list)

    county_df = (
        processed_f[processed_f["state"] == sel_state]
        .sort_values("total_cost", ascending=False)
        [["county", "total_cost", "housing_cost", "food_cost",
          "healthcare_cost", "transportation_cost",
          "median_family_income", "affordability_ratio"]]
    )

    c1, c2 = st.columns([1.2, 1])
    with c1:
        st.dataframe(
            county_df.style
            .format({
                "total_cost": "${:,.0f}", "housing_cost": "${:,.0f}",
                "food_cost": "${:,.0f}", "healthcare_cost": "${:,.0f}",
                "transportation_cost": "${:,.0f}",
                "median_family_income": "${:,.0f}",
                "affordability_ratio": "{:.2f}×",
            })
            .background_gradient(subset=["total_cost"], cmap="RdYlGn_r"),
            use_container_width=True,
            height=380,
        )
    with c2:
        if not county_df.empty:
            fig_county = px.bar(
                county_df.head(12).sort_values("total_cost", ascending=True),
                x="total_cost", y="county",
                orientation="h",
                color="affordability_ratio",
                color_continuous_scale=["#EF4444", "#F59E0B", "#10B981"],
                text="total_cost",
                template="plotly_dark",
                labels={"total_cost": "Annual Cost", "affordability_ratio": "Aff. Ratio"},
            )
            fig_county.update_traces(texttemplate="$%{text:,.0f}", textposition="outside")
            fig_county.update_layout(
                plot_bgcolor="#1E1E2E", paper_bgcolor="#1E1E2E",
                height=380, coloraxis_showscale=False,
                margin=dict(l=0, r=80, t=10, b=10),
                yaxis_title="", xaxis_title="Annual Cost (USD)",
            )
            fig_county.update_xaxes(tickprefix="$", tickformat=",")
            st.plotly_chart(fig_county, use_container_width=True)


# ═══════════════════════════════════════════════════════════════════════════════
# PAGE 4 — A/B EXPERIMENTS
# ═══════════════════════════════════════════════════════════════════════════════
elif page == "🧪 A/B Experiments":
    st.markdown("# 🧪 A/B Experiment Results")
    st.markdown("*Welch's t-test · Cohen's d effect size · 95% Confidence Interval*")
    st.markdown("---")

    # KPI row
    total  = len(experiments_f)
    sig    = int(experiments_f["significant"].sum())
    k1, k2, k3, k4 = st.columns(4)
    for col, val, label, delta in [
        (k1, str(total),    "Total Experiments",       "all pairwise region pairs"),
        (k2, str(sig),      "Significant Results",     f"p < 0.05  ({100*sig//total if total else 0}%)"),
        (k3, f"{experiments_f['p_value'].min():.4f}", "Lowest p-value", "strongest signal"),
        (k4, f"{experiments_f['cohens_d'].abs().max():.3f}", "Largest |Cohen's d|", "strongest effect size"),
    ]:
        col.markdown(
            f"<div class='kpi-card'>"
            f"<div class='kpi-value'>{val}</div>"
            f"<div class='kpi-label'>{label}</div>"
            f"<div class='kpi-delta'>{delta}</div>"
            f"</div>",
            unsafe_allow_html=True,
        )

    st.markdown("<br>", unsafe_allow_html=True)

    # ── Metric filter ──────────────────────────────────────────────────────────
    metrics = sorted(experiments_f["metric"].unique().tolist())
    sel_metric = st.selectbox(
        "Metric",
        metrics,
        format_func=lambda x: x.replace("_", " ").title(),
    )
    exp_m = experiments_f[experiments_f["metric"] == sel_metric].copy()
    exp_m["sig_label"] = exp_m["significant"].map({True: "✓ Significant", False: "✗ Not significant"})

    # ── p-value + Cohen's d bubble chart ──────────────────────────────────────
    c1, c2 = st.columns(2)

    with c1:
        st.markdown("<div class='section-header'><b>p-value by Experiment Pair</b></div>",
                    unsafe_allow_html=True)
        exp_m["pair"] = exp_m["control_region"] + " vs " + exp_m["treatment_region"]
        fig_pval = px.bar(
            exp_m.sort_values("p_value"),
            x="pair", y="p_value",
            color="sig_label",
            color_discrete_map={
                "✓ Significant":    "#10B981",
                "✗ Not significant": "#EF4444",
            },
            text="p_value",
            template="plotly_dark",
        )
        fig_pval.add_hline(y=0.05, line_dash="dash", line_color="#F59E0B",
                           annotation_text="α = 0.05", annotation_position="top right")
        fig_pval.update_traces(texttemplate="%{text:.4f}", textposition="outside",
                               textfont_size=9)
        fig_pval.update_layout(
            xaxis_tickangle=-35, xaxis_title="",
            yaxis_title="p-value", plot_bgcolor="#1E1E2E",
            paper_bgcolor="#1E1E2E", height=380,
            margin=dict(l=0, r=0, t=10, b=80),
            legend_title="",
        )
        st.plotly_chart(fig_pval, use_container_width=True)

    with c2:
        st.markdown("<div class='section-header'><b>Effect Size — Cohen's d</b></div>",
                    unsafe_allow_html=True)
        fig_cd = px.bar(
            exp_m.sort_values("cohens_d"),
            x="cohens_d", y="pair",
            orientation="h",
            color="cohens_d",
            color_continuous_scale=["#EF4444", "#6B7280", "#10B981"],
            text="cohens_d",
            template="plotly_dark",
        )
        fig_cd.update_traces(texttemplate="%{text:.3f}", textposition="outside")
        fig_cd.add_vline(x=0, line_color="#9CA3AF", line_width=1)
        fig_cd.update_layout(
            xaxis_title="Cohen's d  (negative = control is lower cost)",
            yaxis_title="", plot_bgcolor="#1E1E2E",
            paper_bgcolor="#1E1E2E", height=380,
            coloraxis_showscale=False,
            margin=dict(l=0, r=60, t=10, b=10),
        )
        st.plotly_chart(fig_cd, use_container_width=True)

    # ── Confidence interval forest plot ───────────────────────────────────────
    st.markdown("<div class='section-header'><b>95% Confidence Intervals on Mean Difference</b></div>",
                unsafe_allow_html=True)

    fig_ci = go.Figure()
    for _, row in exp_m.sort_values("p_value").iterrows():
        pair   = f"{row['control_region']} vs {row['treatment_region']}"
        color  = "#10B981" if row["significant"] else "#EF4444"
        mean_d = row["treatment_mean"] - row["control_mean"]
        fig_ci.add_trace(go.Scatter(
            x=[row["ci_lower"], row["ci_upper"]],
            y=[pair, pair],
            mode="lines",
            line=dict(color=color, width=3),
            showlegend=False,
        ))
        fig_ci.add_trace(go.Scatter(
            x=[mean_d],
            y=[pair],
            mode="markers",
            marker=dict(color=color, size=10, symbol="diamond"),
            name=pair,
            showlegend=False,
        ))

    fig_ci.add_vline(x=0, line_dash="dash", line_color="#9CA3AF", line_width=1.5)
    fig_ci.update_layout(
        template="plotly_dark", paper_bgcolor="#1E1E2E", plot_bgcolor="#1E1E2E",
        xaxis_title=f"Mean Difference in {sel_metric.replace('_', ' ').title()} (Treatment − Control)",
        yaxis_title="", height=380,
        margin=dict(l=0, r=0, t=10, b=10),
    )
    st.plotly_chart(fig_ci, use_container_width=True)

    # ── Full results table ─────────────────────────────────────────────────────
    st.markdown("<div class='section-header'><b>Full Experiment Results Table</b></div>",
                unsafe_allow_html=True)

    display_cols = [
        "pair", "control_mean", "treatment_mean", "lift_pct",
        "p_value", "cohens_d", "ci_lower", "ci_upper", "sig_label", "winner",
    ]
    exp_m["pair"] = exp_m["control_region"] + " vs " + exp_m["treatment_region"]

    st.dataframe(
        exp_m[display_cols]
        .sort_values("p_value")
        .rename(columns={
            "pair": "Experiment", "control_mean": "Control Mean",
            "treatment_mean": "Treatment Mean", "lift_pct": "Lift %",
            "p_value": "p-value", "cohens_d": "Cohen's d",
            "ci_lower": "CI Lower", "ci_upper": "CI Upper",
            "sig_label": "Result", "winner": "Winner",
        })
        .style
        .format({
            "Control Mean": "${:,.0f}" if sel_metric != "affordability_ratio" else "{:.3f}",
            "Treatment Mean": "${:,.0f}" if sel_metric != "affordability_ratio" else "{:.3f}",
            "Lift %": "{:+.1f}%",
            "p-value": "{:.4f}",
            "Cohen's d": "{:.3f}",
            "CI Lower": "{:,.2f}",
            "CI Upper": "{:,.2f}",
        })
        .applymap(
            lambda v: "background-color:#052e16;color:#10B981" if v == "✓ Significant"
            else ("background-color:#2d1515;color:#EF4444" if v == "✗ Not significant" else ""),
            subset=["Result"],
        ),
        use_container_width=True,
        height=400,
    )
