import requests
import pandas as pd
import os
from datetime import datetime
from db import get_engine, execute_sql
from logger_config import setup_logger

logger = setup_logger('fetch_twse')

def clean_twse_number(value):
    if pd.isna(value) or value == '--' or value == '':
        return None
    try:
        return float(str(value).replace(',', ''))
    except:
        return None

def log_api_request(api_name, endpoint, success, status_code=None, error_message=None):
    sql = """
    INSERT INTO api_request_log (api_name, endpoint, status_code, success, error_message)
    VALUES (:api_name, :endpoint, :status_code, :success, :error_message)
    """
    try:
        execute_sql(sql, {
            'api_name': api_name,
            'endpoint': endpoint,
            'status_code': status_code,
            'success': 1 if success else 0,
            'error_message': str(error_message) if error_message else None
        })
    except Exception as e:
        logger.error(f"Failed to log API request: {e}")

def fetch_twse_stock_day_all():
    url = os.getenv('TWSE_STOCK_DAY_ALL_URL')
    try:
        resp = requests.get(url, timeout=30)
        log_api_request('TWSE', url, resp.status_code == 200, resp.status_code)
        if resp.status_code == 200:
            return resp.json()
        return None
    except Exception as e:
        logger.error(f"TWSE fetch failed: {e}")
        log_api_request('TWSE', url, False, error_message=e)
        return None

def main():
    logger.info("Starting TWSE fetch...")
    data = fetch_twse_stock_day_all()
    if not data:
        return {"success": False, "data_source": "TWSE", "message": "No data from TWSE"}
    
    df = pd.DataFrame(data)
    col_map = {
        'Code': 'stock_id', 'Name': 'stock_name',
        'TradeVolume': 'volume', 'TradeValue': 'turnover_amount',
        'OpeningPrice': 'open_price', 'HighestPrice': 'high_price',
        'LowestPrice': 'low_price', 'ClosingPrice': 'close_price',
        'Change': 'price_change', 'Transaction': 'transaction_count'
    }
    zh_map = {
        '證券代號': 'stock_id', '證券名稱': 'stock_name',
        '成交股數': 'volume', '成交金額': 'turnover_amount',
        '開盤價': 'open_price', '最高價': 'high_price',
        '最低價': 'low_price', '收盤價': 'close_price',
        '漲跌價差': 'price_change', '成交筆數': 'transaction_count'
    }
    
    current_map = {}
    for k, v in col_map.items():
        if k in df.columns: current_map[k] = v
    if not current_map:
        for k, v in zh_map.items():
            if k in df.columns: current_map[k] = v
            
    if 'stock_id' not in current_map.values():
        logger.error(f"Columns not found in TWSE data: {df.columns}")
        return {"success": False, "message": "Schema mismatch"}
        
    df = df.rename(columns=current_map)
    df = df[list(current_map.values())]
    
    trade_date = datetime.now().strftime('%Y-%m-%d')
    df['trade_date'] = trade_date
    df['data_source'] = 'TWSE'
    
    num_cols = ['volume', 'turnover_amount', 'open_price', 'high_price', 'low_price', 'close_price', 'price_change', 'transaction_count']
    for col in num_cols:
        df[col] = df[col].apply(clean_twse_number)
    
    # Upsert stock_master
    master_df = df[['stock_id', 'stock_name']].drop_duplicates()
    master_df['market_type'] = '上市'
    for _, row in master_df.iterrows():
        execute_sql("""
            INSERT INTO stock_master (stock_id, stock_name, market_type) 
            VALUES (:id, :name, :mtype)
            ON DUPLICATE KEY UPDATE stock_name=VALUES(stock_name)
        """, {'id': row['stock_id'], 'name': row['stock_name'], 'mtype': row['market_type']})
        
    # Upsert daily_price
    df = df.dropna(subset=['close_price'])
    for _, row in df.iterrows():
        execute_sql("""
            INSERT INTO daily_price (stock_id, trade_date, open_price, high_price, low_price, close_price, price_change, volume, turnover_amount, transaction_count, data_source)
            VALUES (:stock_id, :trade_date, :open_price, :high_price, :low_price, :close_price, :price_change, :volume, :turnover_amount, :transaction_count, :data_source)
            ON DUPLICATE KEY UPDATE open_price=VALUES(open_price), high_price=VALUES(high_price), low_price=VALUES(low_price), close_price=VALUES(close_price), price_change=VALUES(price_change), volume=VALUES(volume), data_source=VALUES(data_source)
        """, row.to_dict())
        
    return {"success": True, "data_source": "TWSE", "rows": len(df)}

if __name__ == "__main__":
    main()
