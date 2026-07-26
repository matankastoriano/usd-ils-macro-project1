import os
import pandas as pd
import streamlit as st
import plotly.graph_objects as go
from sqlalchemy import create_engine

# --- Connection ---
engine = create_engine(
    f"postgresql://postgres:{os.environ['DB_PASSWORD']}@localhost:5432/usd_ils_macro"
)

# --- Page setup ---
st.set_page_config(page_title="USD/ILS Macro Dashboard", layout="wide")
st.title("USD/ILS Exchange Rate & Macro Indicators")

# --- Query: daily FX with 30- and 90-day moving averages ---
fx_query = """
    SELECT
        obs_date,
        value AS usd_ils,
        ROUND(AVG(value) OVER (ORDER BY obs_date ROWS BETWEEN 29 PRECEDING AND CURRENT ROW), 4) AS ma_30,
        ROUND(AVG(value) OVER (ORDER BY obs_date ROWS BETWEEN 89 PRECEDING AND CURRENT ROW), 4) AS ma_90,
        ROUND(STDDEV(value) OVER (ORDER BY obs_date ROWS BETWEEN 29 PRECEDING AND CURRENT ROW), 4) AS vol_30
    FROM observations
    WHERE indicator_id = 7
    ORDER BY obs_date;
"""
fx = pd.read_sql(fx_query, engine)

# --- Chart ---
st.subheader("USD/ILS with 30- and 90-Day Moving Averages")

fig = go.Figure()
fig.add_trace(go.Scatter(x=fx["obs_date"], y=fx["usd_ils"],
                         name="USD/ILS", line=dict(color="lightgray", width=1)))
fig.add_trace(go.Scatter(x=fx["obs_date"], y=fx["ma_30"],
                         name="30-day MA", line=dict(color="royalblue", width=2)))
fig.add_trace(go.Scatter(x=fx["obs_date"], y=fx["ma_90"],
                         name="90-day MA", line=dict(color="firebrick", width=2)))
fig.update_layout(xaxis_title="Date", yaxis_title="ILS per USD", hovermode="x unified")

st.plotly_chart(fig, use_container_width=True)

# --- Chart: rolling 30-day FX volatility ---
st.subheader("USD/ILS 30-Day Rolling Volatility")

fig_vol = go.Figure()
fig_vol.add_trace(go.Scatter(x=fx["obs_date"], y=fx["vol_30"],
                             name="30-day volatility", line=dict(color="mediumpurple", width=1.5),
                             fill="tozeroy", fillcolor="rgba(147,112,219,0.15)"))
fig_vol.update_layout(xaxis_title="Date", yaxis_title="Std. dev. (30-day)", hovermode="x unified")

st.plotly_chart(fig_vol, use_container_width=True)

# --- Query: YoY inflation, both countries ---
infl_query = """
    SELECT
        obs_date,
        indicator_id,
        ROUND(
            100.0 * (value - LAG(value, 12) OVER (PARTITION BY indicator_id ORDER BY obs_date))
                  / LAG(value, 12) OVER (PARTITION BY indicator_id ORDER BY obs_date),
            2
        ) AS yoy_inflation_pct
    FROM observations
    WHERE indicator_id IN (1, 5)
    ORDER BY indicator_id, obs_date;
"""
infl = pd.read_sql(infl_query, engine)

st.subheader("Year-over-Year Inflation: US vs. Israel")

fig2 = go.Figure()
fig2.add_trace(go.Scatter(
    x=infl[infl["indicator_id"] == 1]["obs_date"],
    y=infl[infl["indicator_id"] == 1]["yoy_inflation_pct"],
    name="US (CPI)", line=dict(color="royalblue", width=2)))
fig2.add_trace(go.Scatter(
    x=infl[infl["indicator_id"] == 5]["obs_date"],
    y=infl[infl["indicator_id"] == 5]["yoy_inflation_pct"],
    name="Israel (CPI)", line=dict(color="firebrick", width=2)))
fig2.update_layout(xaxis_title="Date", yaxis_title="YoY inflation (%)", hovermode="x unified")

st.plotly_chart(fig2, use_container_width=True)

# --- Query: US-Israel interest rate differential ---
diff_query = """
    WITH us_rate AS (
        SELECT obs_date, value AS fed_funds
        FROM observations
        WHERE indicator_id = 3
    ),
    il_rate AS (
        SELECT obs_date, value AS boi_rate
        FROM observations
        WHERE indicator_id = 6
    )
    SELECT
        us_rate.obs_date,
        ROUND(fed_funds, 2)  AS fed_funds,
        ROUND(boi_rate, 2)   AS boi_rate,
        ROUND(fed_funds - boi_rate, 2) AS rate_differential
    FROM us_rate
    JOIN il_rate ON us_rate.obs_date = il_rate.obs_date
    ORDER BY us_rate.obs_date;
"""
diff = pd.read_sql(diff_query, engine)

st.subheader("US–Israel Interest Rate Differential")

fig3 = go.Figure()
# Both underlying rates, lighter
fig3.add_trace(go.Scatter(x=diff["obs_date"], y=diff["fed_funds"],
                          name="US Fed Funds", line=dict(color="royalblue", width=1.5)))
fig3.add_trace(go.Scatter(x=diff["obs_date"], y=diff["boi_rate"],
                          name="Bank of Israel", line=dict(color="firebrick", width=1.5)))
# The differential as a filled area, emphasized
fig3.add_trace(go.Scatter(x=diff["obs_date"], y=diff["rate_differential"],
                          name="Differential (US − IL)", line=dict(color="seagreen", width=2),
                          fill="tozeroy", fillcolor="rgba(46,139,87,0.15)"))
fig3.add_hline(y=0, line_dash="dash", line_color="gray")
fig3.update_layout(xaxis_title="Date", yaxis_title="Rate (%)", hovermode="x unified")

st.plotly_chart(fig3, use_container_width=True)

# --- Query: rolling 12-month correlation, rate differential vs USD/ILS ---
corr_query = """
    WITH monthly_fx AS (
        SELECT date_trunc('month', obs_date)::date AS month,
               ROUND(AVG(value), 4) AS avg_fx
        FROM observations
        WHERE indicator_id = 7
        GROUP BY date_trunc('month', obs_date)::date
    ),
    us_rate AS (
        SELECT obs_date, value AS fed_funds FROM observations WHERE indicator_id = 3
    ),
    il_rate AS (
        SELECT obs_date, value AS boi_rate FROM observations WHERE indicator_id = 6
    ),
    diff AS (
        SELECT us_rate.obs_date AS month,
               ROUND(fed_funds - boi_rate, 2) AS rate_differential
        FROM us_rate
        JOIN il_rate ON us_rate.obs_date = il_rate.obs_date
    )
    SELECT
        monthly_fx.month,
        ROUND(CORR(avg_fx, rate_differential) OVER (ORDER BY monthly_fx.month ROWS BETWEEN 11 PRECEDING AND CURRENT ROW)::numeric, 3) AS rolling_corr_12m
    FROM monthly_fx
    JOIN diff ON monthly_fx.month = diff.month
    ORDER BY monthly_fx.month;
"""
corr = pd.read_sql(corr_query, engine)

st.subheader("Rolling 12-Month Correlation: Rate Differential vs. USD/ILS")

fig4 = go.Figure()
fig4.add_trace(go.Scatter(x=corr["month"], y=corr["rolling_corr_12m"],
                          name="12-mo correlation", line=dict(color="darkorange", width=2),
                          fill="tozeroy", fillcolor="rgba(255,140,0,0.12)"))
fig4.add_hline(y=0, line_dash="dash", line_color="gray")
fig4.update_layout(xaxis_title="Date", yaxis_title="Correlation (−1 to 1)",
                   yaxis_range=[-1, 1], hovermode="x unified")

st.plotly_chart(fig4, use_container_width=True)