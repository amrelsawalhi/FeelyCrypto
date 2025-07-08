import pandas as pd
import requests
from datetime import datetime, timedelta


def fetch_binance_daily_ohlcv(symbols=["BTCUSDT", "ETHUSDT"], interval="1d", start_date=None, limit=1):
    coin_map = {"BTCUSDT": 1, "ETHUSDT": 2}
    start_date = start_date or (datetime.now() - timedelta(days=1)).strftime('%Y-%m-%d')
    start_time = int(pd.Timestamp(start_date).timestamp() * 1000)

    frames = []
    url = "https://api.binance.com/api/v3/klines"

    for symbol in symbols:
        coin_id = coin_map[symbol]
        params = {
            "symbol": symbol,
            "interval": interval,
            "limit": limit,
            "startTime": start_time,
        }

        r = requests.get(url, params=params)
        if r.status_code != 200:
            print(f"Error fetching {symbol}: {r.json()}")
            continue

        data = r.json()
        if not data:
            continue

        df = pd.DataFrame(data, columns=[
            'timestamp', 'open', 'high', 'low', 'close', 'volume',
            'close_time', 'quote_asset_volume', 'num_trades',
            'taker_buy_base_asset_volume', 'taker_buy_quote_asset_volume', 'ignore'
        ])

        df = df.loc[:, ['timestamp', 'open', 'high', 'low', 'close', 'volume']]
        df['timestamp'] = pd.to_datetime(df['timestamp'], unit='ms')
        df.loc[:, ['open', 'high', 'low', 'close', 'volume']] = df.loc[:, ['open', 'high', 'low', 'close', 'volume']].astype(float)
        df.insert(0, 'coin_id', coin_id)

        frames.append(df)
    
    return pd.concat(frames, ignore_index=True)


def fetch_fgi(url='https://api.alternative.me/fng/?limit=5', timeout=10):
    response = requests.get(url, timeout=timeout)
    response.raise_for_status()

    data = response.json()
    data_list = data.get("data", [])
    if not data_list:
        return None

    rows = []
    for item in data_list:
        ts = pd.to_datetime(pd.to_numeric(item['timestamp'], errors='coerce'), unit='s', utc=True)
        value = int(item['value'])
        classification = item['value_classification']
        rows.append({
            "timestamp": ts,
            "value": value,
            "classification": classification
        })

    df = pd.DataFrame(rows)
    
    return df