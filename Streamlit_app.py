import streamlit as st
import pandas as pd
import altair as alt
from datetime import datetime, timedelta
import psycopg2

# Page config
st.set_page_config("FeelyCrypto", layout="wide")

# Theme settings (defined in .streamlit/config.toml)

# Database connection
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

    df_price["timestamp"] = pd.to_datetime(df_price["timestamp"])
    df_fgi["timestamp"] = pd.to_datetime(df_fgi["timestamp"])

    return df_price, df_fgi, df_news

price_df, fgi_df, news_df = load_data()

# Market snapshot and recommendation
st.markdown("## 🧭 Market Snapshot")

latest_btc = price_df[price_df.coin_id == 1].sort_values("timestamp").iloc[-1]
latest_eth = price_df[price_df.coin_id == 2].sort_values("timestamp").iloc[-1]
latest_fgi = fgi_df.sort_values("timestamp").iloc[-1]

sent_counts = news_df["sentiment"].value_counts()
avg_sentiment = sent_counts.idxmax() if not sent_counts.empty else "neutral"
fgi_val = latest_fgi["value"]

if fgi_val < 40 and avg_sentiment == "negative":
    recommendation = "🟢 Good time to buy"
elif fgi_val > 75 and avg_sentiment == "positive":
    recommendation = "🔴 Good time to sell"
else:
    recommendation = "🟡 Wait for clearer signal"

col1, col2, col3, col4 = st.columns([1, 1, 1, 2])
col1.metric("BTC", f"${latest_btc['close']:.2f}", f"{latest_btc['pct_change']}%")
col2.metric("ETH", f"${latest_eth['close']:.2f}", f"{latest_eth['pct_change']}%")
col3.metric("Fear & Greed", latest_fgi['classification'], int(latest_fgi['value']))
col4.success(recommendation)

# Coin and date range selector
st.markdown("### 📊 Market Trends")
selected_coin = st.radio("Select Coin", options=[1, 2], format_func=lambda x: "BTC" if x == 1 else "ETH", horizontal=True)
range_opt = st.radio("Time Range", ["30D", "90D", "180D", "Max"], horizontal=True)

if range_opt != "Max":
    days = int(range_opt.replace("D", ""))
    cutoff = datetime.now() - timedelta(days=days)
    chart_df = price_df[(price_df["coin_id"] == selected_coin) & (price_df["timestamp"] >= cutoff)]
    fgi_chart_df = fgi_df[fgi_df["timestamp"] >= cutoff]
else:
    chart_df = price_df[price_df["coin_id"] == selected_coin]
    fgi_chart_df = fgi_df.copy()

# Charts side-by-side
col5, col6 = st.columns(2)
with col5:
    st.altair_chart(
        alt.Chart(chart_df).mark_line().encode(
            x="timestamp:T",
            y="close:Q"
        ).properties(width=400, height=300),
        use_container_width=True
    )

with col6:
    st.altair_chart(
        alt.Chart(fgi_chart_df).mark_line(color="orange").encode(
            x="timestamp:T",
            y="value:Q"
        ).properties(width=400, height=300),
        use_container_width=True
    )

# News sentiment pie
st.markdown("### 🔀 News Sentiment Summary")
pie_df = pd.DataFrame({"sentiment": sent_counts.index, "count": sent_counts.values})
pie = alt.Chart(pie_df).mark_arc().encode(
    theta="count:Q",
    color=alt.Color("sentiment:N", scale=alt.Scale(range=["#2ecc71", "#f1c40f", "#e74c3c"])),
    tooltip=["sentiment", "count"]
)
st.altair_chart(pie, use_container_width=False)

# News Feed
st.markdown("### 📰 Recent News")
for _, row in news_df.iterrows():
    st.markdown(f"""
    <div style='padding: 1rem; margin-bottom: 1rem; border: 1px solid #ddd; border-radius: 0.5rem; background-color: #fff;'>
        <strong>{row['title']}</strong><br>
        <span style='color: #888;'>Sentiment: {row['sentiment']}, Confidence: {row['confidence']}</span>
        <details style='margin-top: 0.5rem;'>
            <summary>Read more</summary>
            <p>{row['content']}</p>
        </details>
    </div>
    """, unsafe_allow_html=True)
