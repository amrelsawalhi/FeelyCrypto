import streamlit as st
import pandas as pd
import altair as alt
import psycopg2
from datetime import datetime, timedelta

# --- Streamlit Config ---
st.set_page_config("FeelyCrypto", layout="wide")
st.title("📊 FeelyCrypto Dashboard")

# --- Custom Styling ---
st.markdown("""
<style>
    .headline {
        font-weight: 600;
        font-size: 1.1em;
    }
    .confidence {
        font-size: 0.9em;
        color: #888;
    }
</style>
""", unsafe_allow_html=True)

# --- Connect to DB ---
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

# --- Load Data ---
@st.cache_data(ttl=3600)
def load_data():
    price = pd.read_sql("SELECT * FROM fact_price_with_change;", conn)
    fgi = pd.read_sql("SELECT * FROM fact_fear_greed;", conn)
    news = pd.read_sql("SELECT * FROM news_articles ORDER BY published_at DESC;", conn)
    return price, fgi, news

price_df, fgi_df, news_df = load_data()

# --- Preprocess ---
price_df["timestamp"] = pd.to_datetime(price_df["timestamp"])
fgi_df["timestamp"] = pd.to_datetime(fgi_df["timestamp"])

# --- Get latest data for metrics ---
latest_btc = price_df[price_df.coin_id == 1].sort_values("timestamp").iloc[-1]
latest_eth = price_df[price_df.coin_id == 2].sort_values("timestamp").iloc[-1]
latest_fgi = fgi_df.sort_values("timestamp").iloc[-1]

# --- Top Metrics Bar ---
col1, col2, col3 = st.columns(3)
col1.metric("BTC", f"${latest_btc['close']:.2f}", f"{latest_btc['pct_change']}%")
col2.metric("ETH", f"${latest_eth['close']:.2f}", f"{latest_eth['pct_change']}%")
col3.metric("Fear & Greed", latest_fgi['classification'], int(latest_fgi['value']))

# --- Recommendation Engine ---
sent_counts = news_df["sentiment"].value_counts()
avg_sentiment = sent_counts.idxmax() if not sent_counts.empty else "neutral"
fgi_val = latest_fgi["value"]

if fgi_val < 40 and avg_sentiment == "negative":
    recommendation = "🟢 Good time to buy"
elif fgi_val > 75 and avg_sentiment == "positive":
    recommendation = "🔴 Good time to sell"
else:
    recommendation = "🟡 Wait for clearer signal"

st.subheader("Market Recommendation")
st.markdown(f"### {recommendation}")

# --- Price Chart Section ---
st.subheader("Price History")

col_coin, col_range = st.columns([1, 2])
coin = col_coin.radio("Coin", [1, 2], format_func=lambda x: "BTC" if x == 1 else "ETH", horizontal=True)
range_opt = col_range.radio("Time Range", ["30D", "90D", "180D", "Max"], horizontal=True)

chart_df = price_df[price_df.coin_id == coin]
if range_opt != "Max":
    days = int(range_opt.replace("D", ""))
    cutoff = datetime.now() - timedelta(days=days)
    chart_df = chart_df[chart_df["timestamp"] >= cutoff]

line = alt.Chart(chart_df).mark_line().encode(
    x="timestamp:T",
    y="close:Q"
).properties(width=900, height=300)

st.altair_chart(line, use_container_width=True)

# --- FGI Chart ---
st.subheader("Fear & Greed Over Time")
fgi_line = alt.Chart(fgi_df).mark_line(color="orange").encode(
    x="timestamp:T",
    y="value:Q"
).properties(width=900, height=250)

st.altair_chart(fgi_line, use_container_width=True)

# --- Pie Chart ---
st.subheader("News Sentiment Summary")
pie_df = pd.DataFrame({"sentiment": sent_counts.index, "count": sent_counts.values})

donut = alt.Chart(pie_df).mark_arc(innerRadius=50).encode(
    theta="count:Q",
    color=alt.Color("sentiment:N", scale=alt.Scale(
        domain=["positive", "neutral", "negative"],
        range=["#2ecc71", "#f1c40f", "#e74c3c"]
    )),
    tooltip=["sentiment", "count"]
).properties(width=400, height=300)

st.altair_chart(donut, use_container_width=False)

# --- News Feed ---
st.subheader("Recent News")
for _, row in news_df.iterrows():
    sentiment_icon = {"positive": "🟢", "neutral": "🟡", "negative": "🔴"}.get(row["sentiment"], "⚪")
    st.markdown(f"""<div class="headline">{sentiment_icon} {row['title']}</div>
    <div class="confidence">Sentiment: {row['sentiment'].capitalize()} | Confidence: {row['confidence']:.2f}</div>""",
    unsafe_allow_html=True)
    with st.expander("Read More"):
        st.write(row["content"])
