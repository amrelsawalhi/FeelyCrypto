import streamlit as st
import pandas as pd
import altair as alt
from supabase import create_client
from datetime import datetime
import psycopg2

# Initialize Supabase connection
@st.cache_resource
def init_connection():
    return psycopg2.connect(
        host=st.secrets["host"],
        port=st.secrets["port"],
        database=st.secrets["dbname"],
        user=st.secrets["user"],
        password=st.secrets["password"]
    )

conn = init_connection()

@st.cache_data(ttl=3600)
def load_data():
    price_query = "SELECT * FROM fact_price_with_change;"
    fgi_query = "SELECT * FROM fact_fear_greed;"
    news_query = "SELECT * FROM news_articles ORDER BY published_at DESC;"

    df_price = pd.read_sql(price_query, conn)
    df_fgi = pd.read_sql(fgi_query, conn)
    df_news = pd.read_sql(news_query, conn)

    return df_price, df_fgi, df_news

price_df, fgi_df, news_df = load_data()
st.write("Columns in price_df:", price_df.columns.tolist())
st.write("Unique coin_ids:", price_df['coin_id'].unique())
st.write("Sample of price_df:", price_df.head())
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
