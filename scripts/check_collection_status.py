from db import read_sql, execute_sql
from logger_config import setup_logger
import pandas as pd
from datetime import datetime

logger = setup_logger('check_status')

def main():
    logger.info("Checking collection status...")
    days_df = read_sql("SELECT COUNT(DISTINCT trade_date) as cnt FROM daily_price")
    collected_days = int(days_df['cnt'][0])
    
    stocks_df = read_sql("SELECT COUNT(*) as cnt FROM stock_master")
    prices_df = read_sql("SELECT COUNT(*) as cnt FROM daily_price")
    features_df = read_sql("SELECT COUNT(*) as cnt FROM stock_features")
    
    is_ready = 1 if collected_days >= 14 else 0
    msg = f"Collected {collected_days} days. Ready: {is_ready}"
    
    execute_sql("""
        INSERT INTO system_status (status_date, collected_days, stock_count, daily_price_rows, feature_rows, is_ready_for_prediction, message)
        VALUES (CURDATE(), :cd, :sc, :dp, :fr, :ready, :msg)
        ON DUPLICATE KEY UPDATE collected_days=VALUES(collected_days), is_ready_for_prediction=VALUES(is_ready_for_prediction)
    """, {'cd': collected_days, 'sc': int(stocks_df['cnt'][0]), 'dp': int(prices_df['cnt'][0]), 'fr': int(features_df['cnt'][0]), 'ready': is_ready, 'msg': msg})
    
    report = pd.DataFrame([{
        'status_date': datetime.now().strftime('%Y-%m-%d'),
        'collected_days': collected_days,
        'stock_count': int(stocks_df['cnt'][0]),
        'is_ready': is_ready
    }])
    report.to_csv('/home/noir/py3_prj/twstk_prj/output/data_collection_report.csv', index=False)
    
    return {"success": True, "collected_days": collected_days, "is_ready": is_ready}

if __name__ == "__main__":
    main()
