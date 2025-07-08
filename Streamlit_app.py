import streamlit as st
import pandas as pd
import altair as alt
from supabase import create_client
from datetime import datetime

# Initialize Supabase connection
@st.cache_resource
def init_connection():
    url = st.secrets["SUPABASE_URL"]
    key = st.secrets["SUPABASE_KEY"]
    return create_client(url, key)

supabase = init_connection()

# Load data from Supabase
@st.cache_data(ttl=3600)
def load_data():
    prices = supabase.table("fact_price_with_change").select("*").execute().data
    fgi = supabase.table("fact_fear_greed").select("*").execute().data
    news = supabase.table("news_articles").select("*").order("published_at", desc=True).execute().data
    return pd.DataFrame(prices), pd.DataFrame(fgi), pd.DataFrame(news)

price_df, fgi_df, news_df = load_data()

# Config
st.set_page_config("FeelyCrypto", layout="wide")
st.title("📊 FeelyCrypto Dashboard")

# Top bar: BTC, ETH, FGI metrics
latest_btc = price_df[price_df.coin_id == 1].sort_values("timestamp").iloc[-1]
latest_eth = price_df[price_df.coin_id == 2].sort_values("timestamp").iloc[-1]
latest_fgi = fgi_df.sort_values("timestamp").iloc[-1]

col1, col2, col3 = st.columns(3)
col1.metric("BTC", f"${latest_btc['close']:.2f}", f"{latest_btc['pct_change']}%")
col2.metric("ETH", f"${latest_eth['close']:.2f}", f"{latest_eth['pct_change']}%")
col3.metric("Fear & Greed", latest_fgi['classification'], latest_fgi['value'])

# Recommendation Engine
sent_counts = news_df["sentiment"].value_counts()
avg_sentiment = sent_counts.idxmax() if not sent_counts.empty else "neutral"
fgi_val = latest_fgi["value"]

if fgi_val < 40 and avg_sentiment == "negative":
    recommendation = "🟢 Good time to buy"
elif fgi_val > 75 and avg_sentiment == "positive":
    recommendation = "🔴 Good time to sell"
else:
    recommendation = "🟡 Wait for clearer signal"

st.subheader("Recommendation")
st.info(recommendation)

# Price chart with toggle
st.subheader("Price History")
selected_coin = st.radio("Select Coin", options=[1, 2], format_func=lambda x: "BTC" if x == 1 else "ETH", horizontal=True)
chart_df = price_df[price_df.coin_id == selected_coin].copy()
chart_df["timestamp"] = pd.to_datetime(chart_df["timestamp"])

line_chart = alt.Chart(chart_df).mark_line().encode(
    x="timestamp:T",
    y="close:Q"
).properties(width=900, height=300)

st.altair_chart(line_chart, use_container_width=True)

# Pie Chart of News Sentiment
st.subheader("News Sentiment Summary")
pie_df = pd.DataFrame({"sentiment": sent_counts.index, "count": sent_counts.values})

pie = alt.Chart(pie_df).mark_arc().encode(
    theta="count:Q",
    color="sentiment:N",
    tooltip=["sentiment", "count"]
).properties(width=400, height=300)

st.altair_chart(pie, use_container_width=False)

# News Feed
st.subheader("Recent News")
for _, row in news_df.iterrows():
    with st.expander(row["title"]):
        st.write(row["content"])
