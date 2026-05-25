import os
import time
import requests
import pandas as pd
from datetime import datetime, timedelta
from dotenv import load_dotenv
from db import execute_sql
from logger_config import setup_logger

# Load environment variables
load_dotenv(os.path.join(os.path.dirname(__file__), '../.env'))

logger = setup_logger('fetch_finmind')

FINMIND_API_URL = os.getenv('FINMIND_API_URL', 'https://api.finmindtrade.com/api/v4/data')
FINMIND_API_TOKEN = os.getenv('FINMIND_API_TOKEN', '')

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

def finmind_request(params):
    """
    統一 FinMind API 請求函式，自動帶入 token 並記錄日誌
    """
    if FINMIND_API_TOKEN:
        params["token"] = FINMIND_API_TOKEN
    
    try:
        # 不要印出完整 token 在日誌中
        safe_params = params.copy()
        if "token" in safe_params and safe_params["token"]:
            token_val = safe_params["token"]
            safe_params["token"] = f"{token_val[:10]}...{token_val[-10:]}" if len(token_val) > 20 else "***"
        
        endpoint_display = f"{FINMIND_API_URL}?{safe_params}"
        
        response = requests.get(FINMIND_API_URL, params=params, timeout=30)
        status_code = response.status_code
        
        log_api_request('FinMind', endpoint_display, status_code == 200, status_code)
        
        if status_code == 200:
            return response.json()
        else:
            logger.error(f"FinMind request failed. Status: {status_code}, Msg: {response.text}")
            return None
    except Exception as e:
        logger.error(f"FinMind request error: {e}")
        log_api_request('FinMind', FINMIND_API_URL, False, error_message=e)
        return None

def test_token(stock_id="2330"):
    """
    小型 FinMind token 測試
    """
    end_date = datetime.now().strftime('%Y-%m-%d')
    start_date = (datetime.now() - timedelta(days=10)).strftime('%Y-%m-%d')
    
    params = {
        "dataset": "TaiwanStockPrice",
        "data_id": stock_id,
        "start_date": start_date,
        "end_date": end_date
    }
    
    logger.info(f"Running FinMind test for {stock_id} from {start_date} to {end_date}...")
    result = finmind_request(params)
    
    if result and result.get('msg') == 'success' and result.get('data'):
        rows = len(result['data'])
        msg = f"FinMind test success: {rows} rows fetched for {stock_id}"
        logger.info(msg)
        return True, msg
    else:
        error_msg = f"FinMind test failed. Result: {result}"
        logger.error(error_msg)
        return False, error_msg

def main():
    # 保留限流設定
    MAX_REQUESTS_PER_HOUR = int(os.getenv('FINMIND_MAX_REQUESTS_PER_HOUR', 550))
    SLEEP_SECONDS = int(os.getenv('FINMIND_SLEEP_SECONDS', 7))
    
    success, msg = test_token("2330")
    return {"success": success, "message": msg}

if __name__ == "__main__":
    main()
