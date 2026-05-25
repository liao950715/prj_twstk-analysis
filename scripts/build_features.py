import pandas as pd
import numpy as np
from db import execute_sql, read_sql, get_engine
from logger_config import setup_logger

logger = setup_logger('build_features')

def calculate_rsi(series, period=14):
    delta = series.diff()
    gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()
    rs = gain / loss
    return 100 - (100 / (1 + rs))

def main():
    logger.info("Starting feature building...")
    df = read_sql("SELECT * FROM daily_price ORDER BY stock_id, trade_date")
    if df.empty: return {"success": False}
    
    results = []
    for sid, group in df.groupby('stock_id'):
        group = group.sort_values('trade_date')
        group['return_1d'] = group['close_price'].pct_change(1)
        group['return_3d'] = group['close_price'].pct_change(3)
        group['return_5d'] = group['close_price'].pct_change(5)
        group['ma3'] = group['close_price'].rolling(3).mean()
        group['ma5'] = group['close_price'].rolling(5).mean()
        group['ma10'] = group['close_price'].rolling(10).mean()
        group['volume_ma3'] = group['volume'].rolling(3).mean()
        group['volume_ma5'] = group['volume'].rolling(5).mean()
        group['volume_change_3d'] = group['volume'].pct_change(3)
        group['volume_change_5d'] = group['volume'].pct_change(5)
        group['rsi7'] = calculate_rsi(group['close_price'], 7)
        group['rsi14'] = calculate_rsi(group['close_price'], 14)
        group['volatility_3d'] = group['return_1d'].rolling(3).std()
        group['volatility_5d'] = group['return_1d'].rolling(5).std()
        group['price_position_14d'] = (group['close_price'] - group['close_price'].rolling(14).min()) / (group['close_price'].rolling(14).max() - group['close_price'].rolling(14).min())
        group['label_next_day_up'] = (group['close_price'].shift(-1) > group['close_price']).astype(float)
        results.append(group)
        
    final_df = pd.concat(results)
    cols = ['stock_id', 'trade_date', 'close_price', 'return_1d', 'return_3d', 'return_5d', 'ma3', 'ma5', 'ma10', 'volume_ma3', 'volume_ma5', 'volume_change_3d', 'volume_change_5d', 'rsi7', 'rsi14', 'volatility_3d', 'volatility_5d', 'price_position_14d', 'label_next_day_up']
    
    for _, row in final_df[cols].iterrows():
        d = row.to_dict()
        for k, v in d.items():
            if pd.isna(v): d[k] = None
        
        execute_sql("""
            INSERT INTO stock_features (stock_id, trade_date, close_price, return_1d, return_3d, return_5d, ma3, ma5, ma10, volume_ma3, volume_ma5, volume_change_3d, volume_change_5d, rsi7, rsi14, volatility_3d, volatility_5d, price_position_14d, label_next_day_up)
            VALUES (:stock_id, :trade_date, :close_price, :return_1d, :return_3d, :return_5d, :ma3, :ma5, :ma10, :volume_ma3, :volume_ma5, :volume_change_3d, :volume_change_5d, :rsi7, :rsi14, :volatility_3d, :volatility_5d, :price_position_14d, :label_next_day_up)
            ON DUPLICATE KEY UPDATE close_price=VALUES(close_price), return_1d=VALUES(return_1d), label_next_day_up=VALUES(label_next_day_up)
        """, d)
    return {"success": True}

if __name__ == "__main__":
    main()
