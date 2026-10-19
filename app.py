import io
import json
from pathlib import Path

import pandas as pd
import plotly.express as px
import streamlit as st

st.set_page_config(
    page_title="Personal Finance Analyzer",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded",
)

APP_DIR = Path(__file__).parent
DEFAULT_DATA = APP_DIR / "data" / "cleaned_transactions.csv"

st.markdown("""
<style>
    .stApp { background: #f5f7fb; }
    [data-testid="stSidebar"] { background: #111827; }
    [data-testid="stSidebar"] * { color: #f9fafb; }
    .hero {
        background: linear-gradient(120deg, #111827, #1e3a8a);
        padding: 1.5rem 1.7rem; border-radius: 18px; color: white;
        margin-bottom: 1rem;
    }
    .hero h1 { color: white; margin: 0; }
    .hero p { color: #dbeafe; margin: .45rem 0 0 0; }
    div[data-testid="stMetric"] {
        background: white; border: 1px solid #e5e7eb;
        padding: 1rem; border-radius: 14px;
        box-shadow: 0 2px 8px rgba(15,23,42,.04);
    }
    .section-title { color: #111827; font-weight: 700; }
</style>
""", unsafe_allow_html=True)

def standardize_columns(frame):
    frame = frame.copy()
    frame.columns = [
        str(c).strip().replace(" ", "_").replace("-", "_")
        for c in frame.columns
    ]
    aliases = {
        "OrderDate": "Order_Date",
        "Order_Date": "Order_Date",
        "ProductName": "Product_Name",
        "Product_Name": "Product_Name",
        "OrderID": "Order_ID",
        "Order_ID": "Order_ID",
    }
    frame = frame.rename(columns={c: aliases.get(c, c) for c in frame.columns})
    required = ["Sales", "Profit", "Quantity"]
    missing = [c for c in required if c not in frame.columns]
    if missing:
        raise ValueError(
            "The file is missing required column(s): " + ", ".join(missing)
            + ". Expected at least Sales, Profit, Quantity, and preferably "
              "Order_Date, Category, Geography, Product_Name."
        )
    for col in required:
        frame[col] = pd.to_numeric(frame[col], errors="coerce")
    if "Order_Date" in frame.columns:
        frame["Order_Date"] = pd.to_datetime(frame["Order_Date"], errors="coerce")
    else:
        frame["Order_Date"] = pd.NaT
    for col in ["Category", "Geography", "Product_Name", "Order_ID"]:
        if col not in frame.columns:
            frame[col] = "Unknown"
        frame[col] = frame[col].fillna("Unknown").astype(str)
    frame = frame.dropna(subset=["Sales", "Profit", "Quantity"])
    return frame

@st.cache_data(show_spinner=False)
def read_csv_bytes(raw):
    return pd.read_csv(io.BytesIO(raw))

@st.cache_data(show_spinner=False)
def read_json_bytes(raw):
    return pd.read_json(io.BytesIO(raw))

def fmt_money(value):
    return f"{value:,.2f}"

st.sidebar.title("📊 FinanceFlow")
st.sidebar.caption("Personal Finance Analyzer")
st.sidebar.markdown("---")
st.sidebar.subheader("Load your dataset")
uploaded = st.sidebar.file_uploader(
    "Upload cleaned CSV or JSON",
    type=["csv", "json"],
    help="CSV or JSON should include Sales, Profit and Quantity. "
         "Order_Date, Category, Geography and Product_Name improve the analysis."
)

raw_frame = None
source_label = ""

try:
    if uploaded is not None:
        file_bytes = uploaded.getvalue()
        if uploaded.name.lower().endswith(".json"):
            raw_frame = read_json_bytes(file_bytes)
        else:
            raw_frame = read_csv_bytes(file_bytes)
        source_label = uploaded.name
    elif DEFAULT_DATA.exists():
        raw_frame = pd.read_csv(DEFAULT_DATA)
        source_label = "bundled cleaned_transactions.csv"
except Exception as exc:
    st.error(f"Could not read the uploaded file: {exc}")
    st.stop()

st.markdown("""
<div class="hero">
  <h1>Personal Finance Analyzer</h1>
  <p>Explore sales, profit, product performance and transaction trends.</p>
</div>
""", unsafe_allow_html=True)

if raw_frame is None:
    st.info(
        "Upload your existing cleaned dataset using the sidebar to begin. "
        "In Colab, download `finance_analyzer_output/cleaned_transactions.csv` "
        "and then select it here. For deployment, you can also place that file "
        "in the project's `data` folder before uploading the project."
    )
    st.markdown("### Expected dataset columns")
    st.code("Order_Date, Category, Product_Name, Geography, Sales, Quantity, Profit")
    st.stop()

try:
    df = standardize_columns(raw_frame)
except Exception as exc:
    st.error(str(exc))
    st.stop()

if df.empty:
    st.warning("No usable rows were found after cleaning the numeric columns.")
    st.stop()

st.caption(f"Data source: **{source_label}** · {len(df):,} usable transactions")

st.sidebar.subheader("Filters")
categories = ["All"] + sorted(df["Category"].dropna().unique().tolist())
geographies = ["All"] + sorted(df["Geography"].dropna().unique().tolist())
selected_category = st.sidebar.selectbox("Category", categories)
selected_geography = st.sidebar.selectbox("Geography", geographies)

date_min = df["Order_Date"].min()
date_max = df["Order_Date"].max()
date_filter_enabled = pd.notna(date_min) and pd.notna(date_max)
if date_filter_enabled:
    chosen_dates = st.sidebar.date_input(
        "Order date range",
        value=(date_min.date(), date_max.date()),
        min_value=date_min.date(),
        max_value=date_max.date(),
    )
else:
    chosen_dates = None
    st.sidebar.caption("No valid Order_Date column found; date filter is unavailable.")

filtered = df.copy()
if selected_category != "All":
    filtered = filtered[filtered["Category"] == selected_category]
if selected_geography != "All":
    filtered = filtered[filtered["Geography"] == selected_geography]
if date_filter_enabled and isinstance(chosen_dates, (tuple, list)) and len(chosen_dates) == 2:
    start_date, end_date = chosen_dates
    filtered = filtered[
        filtered["Order_Date"].dt.date.between(start_date, end_date)
    ]

if filtered.empty:
    st.warning("No transactions match these filters. Adjust the sidebar filters.")
    st.stop()

total_sales = filtered["Sales"].sum()
total_profit = filtered["Profit"].sum()
total_quantity = filtered["Quantity"].sum()
margin = (total_profit / total_sales * 100) if total_sales else 0.0

c1, c2, c3, c4 = st.columns(4)
c1.metric("Total Sales", fmt_money(total_sales))
c2.metric("Total Profit", fmt_money(total_profit))
c3.metric("Quantity Sold", f"{total_quantity:,.0f}")
c4.metric("Profit Margin", f"{margin:.2f}%")

st.markdown("### Sales overview")
left, right = st.columns(2)

with left:
    dated = filtered.dropna(subset=["Order_Date"])
    if not dated.empty:
        monthly = (
            dated.set_index("Order_Date")
            .resample("MS")
            .agg(Sales=("Sales", "sum"), Profit=("Profit", "sum"))
            .reset_index()
        )
        monthly_long = monthly.melt(
            id_vars="Order_Date", value_vars=["Sales", "Profit"],
            var_name="Metric", value_name="Amount"
        )
        fig = px.line(
            monthly_long, x="Order_Date", y="Amount", color="Metric",
            markers=True, title="Monthly Sales and Profit",
            template="plotly_white"
        )
        fig.update_layout(legend_title_text="", margin=dict(l=10, r=10, t=55, b=10))
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.info("Monthly chart needs valid Order_Date values.")

with right:
    category_summary = (
        filtered.groupby("Category", as_index=False)
        .agg(Sales=("Sales", "sum"), Profit=("Profit", "sum"))
        .sort_values("Sales", ascending=False)
    )
    fig = px.bar(
        category_summary, x="Category", y=["Sales", "Profit"],
        barmode="group", title="Sales and Profit by Category",
        template="plotly_white"
    )
    fig.update_layout(xaxis_tickangle=-25, margin=dict(l=10, r=10, t=55, b=10))
    st.plotly_chart(fig, use_container_width=True)

st.markdown("### Product and geography analysis")
left, right = st.columns(2)
with left:
    product_summary = (
        filtered.groupby("Product_Name", as_index=False)
        .agg(Sales=("Sales", "sum"), Profit=("Profit", "sum"))
    )
    top_products = product_summary.nlargest(10, "Sales").sort_values("Sales")
    fig = px.bar(
        top_products, x="Sales", y="Product_Name", orientation="h",
        title="Top 10 Products by Sales", template="plotly_white"
    )
    fig.update_layout(yaxis_title="", margin=dict(l=10, r=10, t=55, b=10))
    st.plotly_chart(fig, use_container_width=True)

with right:
    geography_summary = (
        filtered.groupby("Geography", as_index=False)
        .agg(Sales=("Sales", "sum"), Profit=("Profit", "sum"))
    )
    top_geographies = geography_summary.nlargest(10, "Sales").sort_values("Sales")
    fig = px.bar(
        top_geographies, x="Sales", y="Geography", orientation="h",
        title="Top 10 Geographies by Sales", template="plotly_white"
    )
    fig.update_layout(yaxis_title="", margin=dict(l=10, r=10, t=55, b=10))
    st.plotly_chart(fig, use_container_width=True)

st.markdown("### Profitability")
low_profit = product_summary.nsmallest(10, "Profit")
st.dataframe(
    low_profit.style.format({"Sales": "{:,.2f}", "Profit": "{:,.2f}"}),
    use_container_width=True,
    hide_index=True,
)

with st.expander("View filtered transactions"):
    st.dataframe(filtered, use_container_width=True, hide_index=True)

csv_data = filtered.to_csv(index=False).encode("utf-8")
json_data = filtered.to_json(orient="records", date_format="iso", indent=2).encode("utf-8")
dl1, dl2 = st.columns(2)
dl1.download_button(
    "⬇️ Download filtered CSV", data=csv_data,
    file_name="filtered_transactions.csv", mime="text/csv",
    use_container_width=True
)
dl2.download_button(
    "⬇️ Download filtered JSON", data=json_data,
    file_name="filtered_transactions.json", mime="application/json",
    use_container_width=True
)

st.markdown("---")
st.caption("Personal Finance Analyzer · Educational project · Results reflect the uploaded dataset and selected filters.")
