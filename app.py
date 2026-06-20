import streamlit as st
import pandas as pd
import plotly.express as px
import numpy as np
import io
import os

# ─────────────────────────────────────────────────────────────────────────────
# PAGE CONFIG  (must be the very first Streamlit call)
# ─────────────────────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="Sales Intelligence Suite",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ─────────────────────────────────────────────────────────────────────────────
# GLOBAL STYLES
# ─────────────────────────────────────────────────────────────────────────────
st.markdown(
    """
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800&display=swap');
    html, body, [class*="css"] { font-family: 'Inter', sans-serif; }

    .hero-banner {
        background: linear-gradient(135deg, #1e1b4b 0%, #312e81 40%, #4338ca 70%, #6366f1 100%);
        border-radius: 18px; padding: 3rem 2.5rem; text-align: center;
        margin-bottom: 2rem; box-shadow: 0 20px 60px rgba(99,102,241,0.3);
    }
    .hero-banner h1 {
        color: #ffffff; font-size: 2.8rem; font-weight: 800;
        margin: 0 0 0.5rem 0; letter-spacing: -0.5px;
    }
    .hero-banner p { color: rgba(255,255,255,0.82); font-size: 1.15rem; margin: 0; }

    .feature-card {
        background: linear-gradient(145deg, #f8f9ff, #eef0ff);
        border: 1px solid #c7d2fe; border-radius: 14px;
        padding: 1.6rem 1.2rem; text-align: center;
        transition: transform 0.2s, box-shadow 0.2s;
    }
    .feature-card:hover { transform: translateY(-4px); box-shadow: 0 12px 30px rgba(99,102,241,0.18); }
    .feature-card .icon { font-size: 2.4rem; margin-bottom: 0.6rem; }
    .feature-card h3 { color: #3730a3; font-size: 1.05rem; font-weight: 700; margin: 0 0 0.4rem 0; }
    .feature-card p  { color: #6b7280; font-size: 0.85rem; margin: 0; line-height: 1.5; }

    [data-testid="metric-container"] {
        background: linear-gradient(145deg, #ffffff, #f5f7ff);
        border: 1px solid #e0e7ff; border-radius: 14px;
        padding: 1rem 1.2rem; box-shadow: 0 4px 16px rgba(99,102,241,0.08);
    }
    [data-testid="metric-container"] [data-testid="stMetricLabel"] {
        font-size: 0.78rem !important; font-weight: 600 !important;
        color: #6366f1 !important; text-transform: uppercase; letter-spacing: 0.5px;
    }
    [data-testid="metric-container"] [data-testid="stMetricValue"] {
        font-size: 1.4rem !important; font-weight: 800 !important; color: #1e1b4b !important;
    }

    .section-header {
        font-size: 1.15rem; font-weight: 700; color: #312e81;
        border-left: 4px solid #6366f1; padding-left: 0.75rem; margin: 1.5rem 0 1rem 0;
    }

    [data-testid="stTabs"] [data-baseweb="tab"] { font-weight: 600; font-size: 0.9rem; }

    [data-testid="stSidebar"] { background: linear-gradient(180deg, #1e1b4b 0%, #312e81 100%); }
    [data-testid="stSidebar"] * { color: #e0e7ff !important; }
    [data-testid="stSidebar"] .stButton button {
        background: #6366f1 !important; color: white !important; border: none !important;
        border-radius: 8px !important; font-weight: 600 !important; width: 100%;
    }
    [data-testid="stSidebar"] .stButton button:hover {
        background: #4f46e5 !important; box-shadow: 0 4px 12px rgba(99,102,241,0.4);
    }

    .stDownloadButton button {
        background: linear-gradient(135deg, #059669, #10b981) !important;
        color: white !important; border: none !important; border-radius: 10px !important;
        padding: 0.6rem 1.5rem !important; font-weight: 700 !important; font-size: 1rem !important;
        box-shadow: 0 4px 14px rgba(16,185,129,0.35) !important;
    }
    .stDownloadButton button:hover {
        box-shadow: 0 6px 20px rgba(16,185,129,0.45) !important;
    }

    .stAlert { border-radius: 12px !important; }
    #MainMenu { visibility: hidden; }
    footer { visibility: hidden; }
    </style>
    """,
    unsafe_allow_html=True,
)

# ─────────────────────────────────────────────────────────────────────────────
# SESSION STATE
# ─────────────────────────────────────────────────────────────────────────────
if "reset_trigger" not in st.session_state:
    st.session_state["reset_trigger"] = 0

if "main_uploaded_bytes" not in st.session_state:
    st.session_state["main_uploaded_bytes"] = None

if "main_uploaded_name" not in st.session_state:
    st.session_state["main_uploaded_name"] = None



# ─────────────────────────────────────────────────────────────────────────────
# HELPER — detect ID column for deduplication
# ─────────────────────────────────────────────────────────────────────────────
def _detect_id_col(df: pd.DataFrame) -> str | None:
    """Return the first column whose name ends with '_ID' or 'ID', else None."""
    for col in df.columns:
        if col.upper().endswith("_ID") or col.upper() == "ID":
            return col
    return None


# ─────────────────────────────────────────────────────────────────────────────
# DATA CLEANING PIPELINE  (cached so filters don't re-run it)
# ─────────────────────────────────────────────────────────────────────────────
@st.cache_data(show_spinner=False)
def clean_data(raw_bytes: bytes):
    """Run the full cleaning pipeline. Returns (cleaned_df, report_dict)."""
    import io as _io
    df = pd.read_csv(_io.BytesIO(raw_bytes))

    # Strip stray whitespace from column names
    df.columns = df.columns.str.strip()

    report = {}

    # 2a — Deduplication (auto-detect ID column; fallback to full-row dedup)
    before = len(df)
    id_col = _detect_id_col(df)
    if id_col:
        df = df.drop_duplicates(subset=id_col, keep="first")
    else:
        df = df.drop_duplicates(keep="first")
    report["dupes_removed"] = before - len(df)

    # 2b — Null handling on core numeric columns (only if they exist)
    null_cols = [c for c in ["Quantity_Sold", "Unit_Price", "Unit_Cost"] if c in df.columns]
    nulls_before = df[null_cols].isnull().sum().sum()
    for col in null_cols:
        df[col] = df[col].fillna(df[col].median())
    report["nulls_filled"] = int(nulls_before)

    # 2c — Outlier capping on Unit_Price (IQR)
    if "Unit_Price" in df.columns:
        Q1 = df["Unit_Price"].quantile(0.25)
        Q3 = df["Unit_Price"].quantile(0.75)
        upper_fence = Q3 + 1.5 * (Q3 - Q1)
        report["outliers_capped"] = int((df["Unit_Price"] > upper_fence).sum())
        df["Unit_Price"] = df["Unit_Price"].clip(upper=upper_fence)
    else:
        report["outliers_capped"] = 0

    # 2d — Date parsing (accepts Sale_Date or Date)
    date_col = "Sale_Date" if "Sale_Date" in df.columns else "Date"
    if date_col in df.columns:
        df[date_col] = pd.to_datetime(df[date_col], errors="coerce")
        df["Month"]     = df[date_col].dt.strftime("%b")
        df["Month_Num"] = df[date_col].dt.month
        df["Quarter"]   = df[date_col].dt.to_period("Q").astype(str)
    else:
        df["Month"] = "Unknown"
        df["Month_Num"] = 0
        df["Quarter"] = "Unknown"

    # 2e — Derived columns
    if "Unit_Price" in df.columns and "Unit_Cost" in df.columns and "Quantity_Sold" in df.columns:
        df["Profit"] = (df["Unit_Price"] - df["Unit_Cost"]) * df["Quantity_Sold"]
    else:
        df["Profit"] = 0.0

    if "Sales_Amount" in df.columns:
        df["Profit_Margin_%"] = (df["Profit"] / df["Sales_Amount"].replace(0, np.nan)) * 100
    else:
        df["Profit_Margin_%"] = 0.0

    report["clean_rows"] = len(df)
    report["id_col"] = id_col or "row"   # store for later use
    return df, report


# ─────────────────────────────────────────────────────────────────────────────
# EXCEL EXPORT
# ─────────────────────────────────────────────────────────────────────────────
def build_excel(filtered_df: pd.DataFrame, leaderboard: pd.DataFrame) -> bytes:
    output = io.BytesIO()
    with pd.ExcelWriter(output, engine="xlsxwriter") as writer:
        drop_cols = ["Month_Num", "Region_and_Sales_Rep"]
        filtered_df.drop(columns=drop_cols, errors="ignore").to_excel(
            writer, sheet_name="Cleaned Data", index=False
        )
        try:
            pivot = filtered_df.pivot_table(
                index="Region", columns="Product_Category",
                values="Sales_Amount", aggfunc="sum",
                margins=True, margins_name="Grand Total",
            )
            pivot.to_excel(writer, sheet_name="Pivot Region x Category")
        except Exception:
            pd.DataFrame({"Note": ["Pivot not available"]}).to_excel(
                writer, sheet_name="Pivot Region x Category", index=False
            )
        leaderboard.to_excel(writer, sheet_name="Sales Rep Summary", index=False)
    output.seek(0)
    return output.read()


# ─────────────────────────────────────────────────────────────────────────────
# HERO BANNER
# ─────────────────────────────────────────────────────────────────────────────
st.markdown(
    """
    <div class="hero-banner">
        <h1>📊 Sales Intelligence Suite</h1>
        <p>Automated Data Cleaning &nbsp;+&nbsp; Business Intelligence Dashboard</p>
    </div>
    """,
    unsafe_allow_html=True,
)

# ─────────────────────────────────────────────────────────────────────────────
# DATASET LOADING
# ─────────────────────────────────────────────────────────────────────────────
DEFAULT_CSV = os.path.join(os.path.dirname(os.path.abspath(__file__)), "sales_data.csv")

st.sidebar.markdown('<div class="section-header" style="margin-top:0; color:#e0e7ff; border-left-color:#a5b4fc;">📤 Upload Dataset</div>', unsafe_allow_html=True)
uploaded_file = st.sidebar.file_uploader(
    "Upload a sales CSV",
    type=["csv"],
    key="sidebar_csv_uploader",
    label_visibility="collapsed"
)

raw_bytes = None
source_name = None

# Sidebar takes precedence, then main uploader, then default CSV file
if uploaded_file is not None:
    raw_bytes = uploaded_file.read()
    source_name = uploaded_file.name
    # Reset main uploader states to prevent conflict
    st.session_state["main_uploaded_bytes"] = None
    st.session_state["main_uploaded_name"] = None
elif st.session_state["main_uploaded_bytes"] is not None:
    raw_bytes = st.session_state["main_uploaded_bytes"]
    source_name = st.session_state["main_uploaded_name"]
elif os.path.exists(DEFAULT_CSV):
    with open(DEFAULT_CSV, "rb") as f:
        raw_bytes = f.read()
    source_name = "sales_data.csv (Default)"

# If main page uploaded file is present, show clean/clear button in sidebar
if st.session_state["main_uploaded_bytes"] is not None:
    if st.sidebar.button("❌ Clear Custom Upload"):
        st.session_state["main_uploaded_bytes"] = None
        st.session_state["main_uploaded_name"] = None
        st.rerun()

# ─────────────────────────────────────────────────────────────────────────────
# LANDING STATE (no data yet)
# ─────────────────────────────────────────────────────────────────────────────
if raw_bytes is None:
    st.markdown("<br>", unsafe_allow_html=True)
    st.info("💡 **Download the dataset** from [kaggle.com/datasets/vinothkannaece/sales-dataset](https://www.kaggle.com/datasets/vinothkannaece/sales-dataset) and upload it below or in the sidebar.", icon="ℹ️")
    
    main_uploaded = st.file_uploader(
        "Upload your sales CSV file to get started",
        type=["csv"],
        key="main_csv_uploader"
    )
    if main_uploaded is not None:
        st.session_state["main_uploaded_bytes"] = main_uploaded.read()
        st.session_state["main_uploaded_name"] = main_uploaded.name
        st.rerun()

    c1, c2, c3 = st.columns(3, gap="large")
    cards = [
        ("🧹", "Auto Clean", "Deduplication, null imputation, IQR outlier capping, and date parsing — fully hands-free."),
        ("📈", "Visualize",  "Interactive Plotly charts — revenue trends, category breakdown, regional share, and rep leaderboard."),
        ("📥", "Export Excel", "One-click .xlsx export with three sheets: cleaned data, pivot table, and sales-rep summary."),
    ]
    for col, (icon, title, desc) in zip([c1, c2, c3], cards):
        col.markdown(
            f'<div class="feature-card"><div class="icon">{icon}</div>'
            f'<h3>{title}</h3><p>{desc}</p></div>',
            unsafe_allow_html=True,
        )
    st.stop()


# ─────────────────────────────────────────────────────────────────────────────
# RUN CLEANING PIPELINE
# ─────────────────────────────────────────────────────────────────────────────
with st.spinner("🧹 Cleaning your data…"):
    df, report = clean_data(raw_bytes)

st.success(f"✅ Data cleaning complete! Loaded **{source_name}**.", icon="✅")
qc1, qc2, qc3, qc4 = st.columns(4)
qc1.metric("🧹 Duplicates Removed", f"{report['dupes_removed']:,}")
qc2.metric("🩹 Nulls Filled",        f"{report['nulls_filled']:,}")
qc3.metric("📉 Outliers Capped",     f"{report['outliers_capped']:,}")
qc4.metric("✅ Clean Rows",           f"{report['clean_rows']:,}")
st.markdown("<br>", unsafe_allow_html=True)

id_col = report.get("id_col", "row")

# ─────────────────────────────────────────────────────────────────────────────
# SIDEBAR FILTERS
# ─────────────────────────────────────────────────────────────────────────────
st.sidebar.header("🔍 Filters")

all_regions    = sorted(df["Region"].dropna().unique().tolist()) if "Region" in df.columns else []
all_quarters   = sorted(df["Quarter"].dropna().unique().tolist())
all_cust_types = ["All"] + sorted(df["Customer_Type"].dropna().unique().tolist()) if "Customer_Type" in df.columns else ["All"]

rk = st.session_state["reset_trigger"]

selected_regions = st.sidebar.multiselect(
    "Region", options=all_regions, default=all_regions, key=f"region_{rk}"
)
selected_quarter = st.sidebar.selectbox(
    "Quarter", options=["All"] + all_quarters, index=0, key=f"quarter_{rk}"
)
selected_cust = st.sidebar.radio(
    "Customer Type", options=all_cust_types, index=0, key=f"cust_{rk}"
)

if st.sidebar.button("🔄 Reset Filters"):
    st.session_state["reset_trigger"] += 1
    st.rerun()

# Apply filters
filtered_df = df.copy()
if selected_regions and "Region" in filtered_df.columns:
    filtered_df = filtered_df[filtered_df["Region"].isin(selected_regions)]
if selected_quarter != "All":
    filtered_df = filtered_df[filtered_df["Quarter"] == selected_quarter]
if selected_cust != "All" and "Customer_Type" in filtered_df.columns:
    filtered_df = filtered_df[filtered_df["Customer_Type"] == selected_cust]

st.sidebar.markdown("---")
st.sidebar.markdown(
    f"<span style='font-size:0.85rem;'>📋 Showing <b>{len(filtered_df):,}</b> rows</span>",
    unsafe_allow_html=True,
)

if filtered_df.empty:
    st.warning("⚠️ No data matches the selected filters. Please adjust your selections.")
    st.stop()


# ─────────────────────────────────────────────────────────────────────────────
# KPI CARDS
# ─────────────────────────────────────────────────────────────────────────────
st.markdown('<div class="section-header">📌 Key Performance Indicators</div>', unsafe_allow_html=True)
k1, k2, k3, k4, k5 = st.columns(5)
k1.metric("💰 Total Revenue",      f"₹{filtered_df['Sales_Amount'].sum():,.0f}")
k2.metric("📦 Total Transactions", f"{len(filtered_df):,}")
k3.metric("📈 Avg Order Value",    f"₹{filtered_df['Sales_Amount'].mean():,.0f}")
k4.metric("🏆 Top Region",
          filtered_df.groupby("Region")["Sales_Amount"].sum().idxmax()
          if "Region" in filtered_df.columns and not filtered_df.empty else "—")
k5.metric("💡 Avg Profit Margin",  f"{filtered_df['Profit_Margin_%'].mean():.1f}%")


# ─────────────────────────────────────────────────────────────────────────────
# TABS + CHARTS
# ─────────────────────────────────────────────────────────────────────────────
st.markdown("<br>", unsafe_allow_html=True)
tab_rev, tab_trend, tab_reps, tab_raw = st.tabs(
    ["📊 Revenue", "📅 Trends", "👥 Sales Reps", "🗂️ Raw Data"]
)

_layout = dict(plot_bgcolor="rgba(0,0,0,0)", paper_bgcolor="rgba(0,0,0,0)")

# ── Tab 1: Revenue ─────────────────────────────────────────────────────────────
with tab_rev:
    cl, cr = st.columns(2, gap="large")
    with cl:
        d = filtered_df.groupby("Product_Category")["Sales_Amount"].sum().reset_index()
        fig = px.bar(d, x="Product_Category", y="Sales_Amount",
                     title="Revenue by Category", color="Product_Category",
                     color_discrete_sequence=px.colors.qualitative.Vivid,
                     labels={"Sales_Amount": "Revenue (₹)", "Product_Category": "Category"})
        fig.update_layout(showlegend=False, **_layout)
        fig.update_traces(marker_line_width=0)
        st.plotly_chart(fig, width="stretch")
    with cr:
        d = filtered_df.groupby("Region")["Sales_Amount"].sum().reset_index()
        fig = px.pie(d, names="Region", values="Sales_Amount",
                     title="Revenue by Region", hole=0.45,
                     color_discrete_sequence=px.colors.qualitative.Pastel)
        fig.update_layout(**_layout)
        st.plotly_chart(fig, width="stretch")

# ── Tab 2: Trends ──────────────────────────────────────────────────────────────
with tab_trend:
    monthly = (
        filtered_df.groupby(["Month_Num", "Month"])["Sales_Amount"]
        .sum().reset_index().sort_values("Month_Num")
    )
    fig = px.line(monthly, x="Month", y="Sales_Amount",
                  title="Monthly Revenue Trend", markers=True,
                  labels={"Sales_Amount": "Revenue (₹)"})
    fig.update_traces(line_color="#6366f1", line_width=3, marker=dict(size=9, color="#6366f1"))
    fig.update_layout(**_layout)
    st.plotly_chart(fig, width="stretch")

    d2 = (
        filtered_df.groupby(["Product_Category", "Customer_Type"])["Sales_Amount"]
        .sum().reset_index()
    )
    fig2 = px.bar(d2, x="Product_Category", y="Sales_Amount", color="Customer_Type",
                  title="New vs Returning Revenue by Category", barmode="group",
                  labels={"Sales_Amount": "Revenue (₹)", "Product_Category": "Category"},
                  color_discrete_sequence=["#6366f1", "#f59e0b"])
    fig2.update_layout(**_layout)
    st.plotly_chart(fig2, width="stretch")

# ── Tab 3: Sales Reps ──────────────────────────────────────────────────────────
with tab_reps:
    agg_col = id_col if id_col in filtered_df.columns else filtered_df.columns[0]
    leaderboard = (
        filtered_df.groupby("Sales_Rep")
        .agg(
            Total_Transactions=(agg_col, "count"),
            Total_Revenue=("Sales_Amount", "sum"),
            Avg_Deal_Size=("Sales_Amount", "mean"),
            Total_Profit=("Profit", "sum"),
            Avg_Profit_Margin=("Profit_Margin_%", "mean"),
        )
        .sort_values("Total_Revenue", ascending=False)
        .reset_index()
    )
    leaderboard.insert(0, "Rank", range(1, len(leaderboard) + 1))

    disp = leaderboard.copy()
    disp["Total_Revenue"]     = disp["Total_Revenue"].map("₹{:,.0f}".format)
    disp["Avg_Deal_Size"]     = disp["Avg_Deal_Size"].map("₹{:,.0f}".format)
    disp["Total_Profit"]      = disp["Total_Profit"].map("₹{:,.0f}".format)
    disp["Avg_Profit_Margin"] = disp["Avg_Profit_Margin"].map("{:.1f}%".format)

    st.markdown('<div class="section-header">🏅 Sales Rep Leaderboard</div>', unsafe_allow_html=True)
    st.dataframe(disp, width="stretch", hide_index=True)

    fig = px.bar(leaderboard.sort_values("Total_Revenue"),
                 x="Total_Revenue", y="Sales_Rep", orientation="h",
                 title="Sales Rep — Total Revenue Ranking",
                 color="Total_Revenue", color_continuous_scale="Purples",
                 labels={"Total_Revenue": "Revenue (₹)", "Sales_Rep": "Rep"})
    fig.update_layout(coloraxis_showscale=False, **_layout)
    st.plotly_chart(fig, width="stretch")

# ── Tab 4: Raw Data ────────────────────────────────────────────────────────────
with tab_raw:
    st.markdown(
        f'<p style="color:#6b7280;font-size:0.9rem;">Showing <b>{len(filtered_df):,}</b> rows after filters</p>',
        unsafe_allow_html=True,
    )
    st.dataframe(filtered_df, width="stretch", hide_index=True)


# ─────────────────────────────────────────────────────────────────────────────
# EXCEL EXPORT
# ─────────────────────────────────────────────────────────────────────────────
st.markdown("<br>", unsafe_allow_html=True)
st.markdown('<div class="section-header">📥 Export Report</div>', unsafe_allow_html=True)

agg_col = id_col if id_col in filtered_df.columns else filtered_df.columns[0]
lb_export = (
    filtered_df.groupby("Sales_Rep")
    .agg(
        Total_Transactions=(agg_col, "count"),
        Total_Revenue=("Sales_Amount", "sum"),
        Avg_Deal_Size=("Sales_Amount", "mean"),
        Total_Profit=("Profit", "sum"),
        Avg_Profit_Margin=("Profit_Margin_%", "mean"),
    )
    .sort_values("Total_Revenue", ascending=False)
    .reset_index()
)
lb_export.insert(0, "Rank", range(1, len(lb_export) + 1))

st.download_button(
    label="📥 Download Excel Report",
    data=build_excel(filtered_df, lb_export),
    file_name="sales_intelligence_report.xlsx",
    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
)
st.caption("Exports 3 sheets: **Cleaned Data** · **Pivot Region × Category** · **Sales Rep Summary**")

# ─────────────────────────────────────────────────────────────────────────────
# FOOTER
# ─────────────────────────────────────────────────────────────────────────────
st.markdown("---")
st.caption("Sales Intelligence Suite • Built with Streamlit + Pandas + Plotly")
