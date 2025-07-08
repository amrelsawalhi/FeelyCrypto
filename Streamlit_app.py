import streamlit as st
import pandas as pd
import altair as alt
import psycopg2
from datetime import datetime, timedelta

# --------- Styling ---------
st.set_page_config("FeelyCrypto", layout="wide")
st.markdown(
    """
    <style>
        .main {
            max-width: 800px;
            margin: auto;
        }
        .stRadio > div {
            flex-direction: row;
        }
    </style>
    """,
    unsafe_allow_html=True,
)

# --------- DB Connection ---------
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
    df_price = pd.read_sql("SELECT * FROM fact_price_with_change;", conn)
    df_fgi = pd.read_sql("SELECT * FROM fact_fear_greed;", conn)
    df_news = pd.read_sql("SELECT * FROM news_articles ORDER BY published_at DESC;", conn)
    return df_price, df_fgi, df_news

price_df, fgi_df, news_df = load_data()

# --------- Top Section: Metrics ---------
st.title("📊 FeelyCrypto")

latest_btc = price_df[price_df.coin_id == 1].sort_values("timestamp").iloc[-1]
latest_eth = price_df[price_df.coin_id == 2].sort_values("timestamp").iloc[-1]
latest_fgi = fgi_df.sort_values("timestamp").iloc[-1]

col1, col2, col3 = st.columns(3)
col1.metric("BTC", f"${latest_btc['close']:.2f}", f"{latest_btc['pct_change']}%")
col2.metric("ETH", f"${latest_eth['close']:.2f}", f"{latest_eth['pct_change']}%")
col3.metric("Fear & Greed", latest_fgi['classification'], int(latest_fgi['value']))

st.markdown("---")

# --------- Recommendation Engine ---------
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

st.markdown("---")

# --------- Filters ---------
st.subheader("Price History")
col1, col2 = st.columns([2, 3])
with col1:
    selected_coin = st.radio("Coin", [1, 2], format_func=lambda x: "BTC" if x == 1 else "ETH", horizontal=True)
with col2:
    time_range = st.radio("Time Range", ["30D", "90D", "180D", "Max"], horizontal=True)

# --------- Time Filter ---------
today = datetime.now()
if time_range == "30D":
    start_date = today - timedelta(days=30)
elif time_range == "90D":
    start_date = today - timedelta(days=90)
elif time_range == "180D":
    start_date = today - timedelta(days=180)
else:
    start_date = price_df["timestamp"].min()

# --------- Price Chart ---------
chart_df = price_df[price_df.coin_id == selected_coin].copy()
chart_df["timestamp"] = pd.to_datetime(chart_df["timestamp"])
chart_df = chart_df[chart_df["timestamp"] >= start_date]

price_chart = alt.Chart(chart_df).mark_line().encode(
    x="timestamp:T",
    y="close:Q"
).properties(width=1000, height=300)

st.altair_chart(price_chart, use_container_width=True)

# --------- FGI Chart ---------
st.subheader("Fear & Greed Index")

fgi_df["timestamp"] = pd.to_datetime(fgi_df["timestamp"])
fgi_filtered = fgi_df[fgi_df["timestamp"] >= start_date]

fgi_chart = alt.Chart(fgi_filtered).mark_line(color="orange").encode(
    x="timestamp:T",
    y="value:Q"
).properties(width=1000, height=200)

st.altair_chart(fgi_chart, use_container_width=True)

st.markdown("---")

# --------- News Feed ---------
st.subheader("Recent News")
st.markdown("**Legend**  🟢 Positive 🔴 Negative 🟡 Neutral")

for _, row in news_df.iterrows():
    sentiment_icon = {"positive": "🟢", "negative": "🔴", "neutral": "🟡"}.get(row["sentiment"], "⚪")
    label = f"{sentiment_icon} {row['title']} (Confidence: {row['confidence']:.2f})"
    with st.expander(label):
        st.write(row["content"])

