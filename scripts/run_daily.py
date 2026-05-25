import sys
import os
from logger_config import setup_logger
from db import test_connection
import fetch_twse, build_features, check_collection_status

logger = setup_logger('run_daily')

def main():
    logger.info("=== Starting Daily Run ===")
    try:
        test_connection()
    except Exception as e:
        logger.critical(f"Database connection failed: {e}. Aborting.")
        sys.exit(1)
        
    twse_res = fetch_twse.main()
    logger.info(f"TWSE Fetch: {twse_res}")
    
    feat_res = build_features.main()
    logger.info(f"Feature Build: {feat_res}")
    
    status_res = check_collection_status.main()
    logger.info(f"Status Check: {status_res}")
    
    if status_res['is_ready']:
        logger.info("System ready for prediction.")
    else:
        logger.info(f"Data collection in progress: {status_res['collected_days']}/14 days")
        
    logger.info("=== Daily Run Completed ===")

if __name__ == "__main__":
    main()
