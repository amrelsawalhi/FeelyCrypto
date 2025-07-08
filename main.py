from scripts.api import fetch_binance_daily_ohlcv, fetch_fgi
from scripts.sql import insert_binance_data, insert_fear_and_greed_index, insert_news_data
from scripts.db import db_connection
from scripts.news import fetch_coindesk_news_rss
from scripts.prepare4analysis import clean_and_lemmatize_df, prepare_news_for_analysis
from scripts.model import predict_sentiment


def main():

    con = None
    try:
        binance_df = fetch_binance_daily_ohlcv()
        fgi_df = fetch_fgi()
        news_df = fetch_coindesk_news_rss()
        
        single_column_df = prepare_news_for_analysis(news_df)
        
        news_df_cleaned = clean_and_lemmatize_df(single_column_df)
    
        labels, confidences = predict_sentiment(news_df_cleaned)

        news_df["sentiment"] = labels
        news_df["confidence"] = confidences
        news_df = news_df[['published_at', 'title', 'content', 'source', 'sentiment', 'confidence']]
        
        con = db_connection()

        insert_binance_data(binance_df, con)
        insert_fear_and_greed_index(fgi_df, con)
        insert_news_data(news_df, con)

    except Exception as e:
        print(f"Error: {e}")

    finally:
        if con:
            con.close()


if __name__ == "__main__":
    main()