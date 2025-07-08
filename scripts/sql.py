from psycopg2.extras import execute_values
import pandas as pd

def insert_binance_data(df, connection):
    if  df is None or df.empty:
        print("No Binance data to insert")
        return

    query = """
        INSERT INTO fact_price (coin_id, timestamp, open, high, low, close, volume)
        VALUES %s
        ON CONFLICT (coin_id, timestamp) DO NOTHING;
    """

    data = [
        (
            int(row['coin_id']),
            row['timestamp'],
            float(row['open']),
            float(row['high']),
            float(row['low']),
            float(row['close']),
            float(row['volume'])
        )
        for _, row in df.iterrows()
    ]

    with connection.cursor() as cur:
        execute_values(cur, query, data)
        connection.commit()
        print(f"{cur.rowcount} rows inserted into fact_price.")


def insert_fear_and_greed_index(df, connection):
    if  df is None or df.empty:
        print("No FGI data to insert.")
        return

    query = """
        INSERT INTO fact_fear_greed (timestamp, value, classification)
        VALUES %s
        ON CONFLICT (timestamp) DO NOTHING;
    """

    data = [
        (
            row['timestamp'],
            int(row['value']),
            row['classification']
        )
        for _, row in df.iterrows()
    ]

    with connection.cursor() as cur:
        execute_values(cur, query, data)
        connection.commit()
        print(f"{cur.rowcount} rows inserted into fact_fear_greed.")

def insert_news_data(df, connection):
    if df is None or df.empty:
        print("No news articles to insert.")
        return

    query = """
        INSERT INTO news_articles (published_at, title, content, source, sentiment, confidence)
        VALUES %s
        ON CONFLICT (title, published_at) DO NOTHING;
    """

    data = [
        (
            row['published_at'],
            row['title'],
            row['content'],
            row.get('source', 'CoinDesk'),
            row.get('sentiment', None),
            row.get('confidence', None)
        )
        for _, row in df.iterrows()
    ]

    with connection.cursor() as cur:
        execute_values(cur, query, data)
        connection.commit()
        print(f"{cur.rowcount} news articles inserted.")
