# FeelyCrypto - Professional UI Streamlit App

import streamlit as st
import pandas as pd
import altair as alt
from datetime import datetime
import psycopg2

# ----- CONFIG -----
st.set_page_config("FeelyCrypto", layout="wide")
st.markdown("""
    <style>
    .big-font { font-size:30px !important; }
    .section-header { margin-top: 2rem; margin-bottom: 1rem; font-weight: 700; font-size: 22px; }
    </style>
""", unsafe_allow_html=True)

# ----- DB CONNECTION -----
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

# ----- HEADER -----
st.markdown("<div class='big-font'>📊 FeelyCrypto</div>", unsafe_allow_html=True)
st.caption("Real-time insights powered by crypto price action, sentiment, and fear & greed index")
st.divider()

# ----- METRICS -----
latest_btc = price_df[price_df.coin_id == 1].sort_values("timestamp").iloc[-1]
latest_eth = price_df[price_df.coin_id == 2].sort_values("timestamp").iloc[-1]
latest_fgi = fgi_df.sort_values("timestamp").iloc[-1]

col1, col2, col3 = st.columns(3)
col1.metric("BTC", f"${latest_btc['close']:.2f}", f"{latest_btc['pct_change']}%")
col2.metric("ETH", f"${latest_eth['close']:.2f}", f"{latest_eth['pct_change']}%")
col3.metric("Fear & Greed", latest_fgi['classification'], int(latest_fgi['value']))

# ----- RECOMMENDATION -----
sent_counts = news_df["sentiment"].value_counts()
avg_sentiment = sent_counts.idxmax() if not sent_counts.empty else "neutral"
fgi_val = latest_fgi["value"]

if fgi_val < 40 and avg_sentiment == "negative":
    recommendation = "🟢 Good time to buy"
elif fgi_val > 75 and avg_sentiment == "positive":
    recommendation = "🔴 Good time to sell"
else:
    recommendation = "🟡 Wait for clearer signal"

st.markdown("<div class='section-header'>Recommendation</div>", unsafe_allow_html=True)
st.info(recommendation)

# ----- FILTERS -----
st.markdown("<div class='section-header'>Filters</div>", unsafe_allow_html=True)
filter_col1, filter_col2 = st.columns([1, 2])
selected_coin = filter_col1.radio("Coin", [1, 2], format_func=lambda x: "BTC" if x == 1 else "ETH", horizontal=True)
range_option = filter_col2.selectbox("Time Range", ["30D", "90D", "180D", "MAX"])

# ----- DATA FILTERING -----
chart_df = price_df[price_df.coin_id == selected_coin].copy()
chart_df["timestamp"] = pd.to_datetime(chart_df["timestamp"])

if range_option != "MAX":
    days = int(range_option.replace("D", ""))
    cutoff = chart_df["timestamp"].max() - pd.Timedelta(days=days)
    chart_df = chart_df[chart_df["timestamp"] >= cutoff]
    fgi_df = fgi_df[pd.to_datetime(fgi_df["timestamp"]) >= cutoff]

# ----- PRICE CHART -----
st.markdown("<div class='section-header'>Price History</div>", unsafe_allow_html=True)
price_chart = alt.Chart(chart_df).mark_line().encode(
    x="timestamp:T",
    y="close:Q"
).properties(width=900, height=300)

st.altair_chart(price_chart, use_container_width=True)

# ----- FGI CHART -----
st.markdown("<div class='section-header'>Fear & Greed Over Time</div>", unsafe_allow_html=True)
fgi_df["timestamp"] = pd.to_datetime(fgi_df["timestamp"])
fgi_line = alt.Chart(fgi_df).mark_line().encode(
    x="timestamp:T",
    y="value:Q"
).properties(width=900, height=200)

st.altair_chart(fgi_line, use_container_width=True)

# ----- PIE CHART -----
st.markdown("<div class='section-header'>News Sentiment Summary</div>", unsafe_allow_html=True)
pie_df = pd.DataFrame({"sentiment": sent_counts.index, "count": sent_counts.values})
pie = alt.Chart(pie_df).mark_arc().encode(
    theta="count:Q",
    color="sentiment:N",
    tooltip=["sentiment", "count"]
).properties(width=400, height=300)

st.altair_chart(pie, use_container_width=False)

# ----- NEWS FEED -----
st.markdown("<div class='section-header'>Recent News</div>", unsafe_allow_html=True)
for _, row in news_df.iterrows():
    label = f"{'🟢' if row['sentiment']=='positive' else '🔴' if row['sentiment']=='negative' else '🟡'} {row['title']} ({int(row['confidence']*100)}%)"
    with st.expander(label):
        st.write(row["content"])

# ----- END -----
st.divider()
st.caption("FeelyCrypto © 2025")
