import os
from pathlib import Path

import pandas as pd
import streamlit as st
from dotenv import load_dotenv
from sqlalchemy import create_engine
import plotly.express as px


load_dotenv()

CSV = Path(__file__).resolve().parent.parent / "export" / "mart_district_affordability.csv"
TEXT_COLS = ["district_code", "district_name"]

@st.cache_data
def load_mart() -> tuple[pd.DataFrame, str]:
    try:
        url = (
            f"postgresql+psycopg2://{os.environ['WAREHOUSE_USER']}:{os.environ['WAREHOUSE_PASSWORD']}"
            f"@localhost:{os.environ['WAREHOUSE_PORT']}/{os.environ['WAREHOUSE_DB']}"
            )
        df = pd.read_sql("select * from analytics.mart_district_affordability", create_engine(url))
        num_cols = df.select_dtypes("object").columns.difference(TEXT_COLS)
        df[num_cols] = df[num_cols].astype(float)
        CSV.parent.mkdir(exist_ok=True)
        df.to_csv(CSV, index=False)
        return df, "live Postgres warehouse"
    except Exception:
        return pd.read_csv(CSV, dtype={"district_code": str}), "exported CSV snapshot"

df, source = load_mart()

MEDIAN_COLS = {"income_median_to_mean", "income_median_adj_eur_est", "rent_to_income_ratio_median_adj_est"}
HAS_MEDIAN = MEDIAN_COLS <= set(df.columns)

st.title("Barcelona housing affordability")
st.caption(f"District of Barcelona, 2015-2023 · data source: {source} ")

# Sidebar
st.sidebar.header("Filters")
district = st.sidebar.selectbox("District", sorted(df["district_name"].unique()))
years = sorted(df["year"].unique())
year = st.sidebar.select_slider("Year", options=years, value=years[-1])
median = False
if HAS_MEDIAN:
    basis = st.sidebar.radio("Income basis", ["Mean (headline)", "Median-adjusted (estimate)"], index=0)
    median = basis.startswith("Median")
else:
    st.sidebar.caption("Median view unavailable: data snapshot predates it.")

ratio_col   = "rent_to_income_ratio_median_adj_est" if median else "rent_to_income_ratio"
income_col  = "income_median_adj_eur_est" if median else "income_eur"
tag         = " (median-adjusted estimate)" if median else ""

#Heatmap
st.subheader(f"Rent-to-income ratio by district and year{tag}")
pivot = df.pivot(index="district_name", columns="year", values=ratio_col)
pivot = pivot.sort_values(pivot.columns.max(), ascending=False)

fig = px.imshow(
        pivot,
        text_auto=".2f",
        aspect="auto",
        color_continuous_scale="YlOrRd",
        labels=dict(x="Year", y="District", color="Rent / income")
        )

fig.update_xaxes(type="category", side="top")
st.plotly_chart(fig, use_container_width=True)

if HAS_MEDIAN:
    with st.expander("Median / mean income factor (per consumption unit)"):
        m = df[df["year"] == year].sort_values("income_median_to_mean")
        fig_m = px.bar(m, x="income_median_to_mean", y="district_name", orientation="h",
                       labels=dict(income_median_to_mean="Median / mean", district_name="District"))
        fig_m.update_xaxes(range=[0.6, 1])
        st.plotly_chart(fig_m, use_container_width=True)
        st.caption(f"{year}. Below 1 = the typical resident earns less than the average. "
                   "Estimate: per consumption unit, all residents (not renters), applied to household income.")

# Snapshot
d = df[df["district_name"] == district].sort_values("year")
cur = d[d["year"] == year].iloc[0]
prev = d[d["year"] == year - 1]


def pct_delta(col):
    if prev.empty or pd.isna(prev.iloc[0][col]) or pd.isna(cur[col]):
        return None
    return f"{cur[col] / prev.iloc[0][col] - 1:+.1%}"


st.subheader(f"{district}, {year}")
c1, c2, c3, c4 = st.columns(4)
c1.metric(f"Household income{' (est.)' if median else ''}", f"€{cur[income_col]:,.0f}", pct_delta(income_col))
c2.metric("Rent / month", f"€{cur['rent_eur_month']:,.0f}", pct_delta("rent_eur_month"), delta_color="inverse")
ratio_delta = None
if not prev.empty and pd.notna(prev.iloc[0][ratio_col]):
    ratio_delta = f"{(cur[ratio_col] - prev.iloc[0][ratio_col]) * 100:+.1f} pp"
c3.metric(f"Rent-to-income{' (est.)' if median else ''}", f"{cur[ratio_col]:.1%}", ratio_delta, delta_color="inverse")
c4.metric("Median rent / m²", f"€{cur['rent_eur_m2_median']:,.2f}", pct_delta("rent_eur_m2_median"), delta_color="inverse")

# ---- real vs nominal
st.subheader(f"Rent vs income: nominal and real indices, {district}")
series = ["rent_index_nominal", "rent_index_real", "income_index_nominal", "income_index_real"]
long = d.melt(id_vars="year", value_vars=series, var_name="series", value_name="index_value")
long["measure"] = long["series"].str.split("_").str[0]
long["basis"] = long["series"].str.split("_").str[-1]
fig2 = px.line(
    long,
    x="year",
    y="index_value",
    color="measure",
    line_dash="basis",
    markers=True,
    color_discrete_map={"rent": "#ef553b", "income": "#4c9be8"},
    line_dash_map={"nominal": "solid", "real": "dot"},
    labels=dict(year="Year", index_value="Index (2015 = 100)", measure="Measure", basis="Basis"),
)
fig2.update_xaxes(dtick=1)
fig2.add_hline(y=100, line_width=1, line_color="grey")
st.plotly_chart(fig2, use_container_width=True)
st.caption("Solid = nominal, dotted = real (deflated with INE CPI). Index 2015 = 100. Index charts use mean income regardless of the basis toggle.")

with st.expander("Raw data"):
    st.dataframe(df)


