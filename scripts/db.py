import os
from sqlalchemy import create_engine, text
from dotenv import load_dotenv
from logger_config import setup_logger

load_dotenv(os.path.join(os.path.dirname(__file__), '../.env'))
logger = setup_logger('db')

def get_engine():
    user = os.getenv('MYSQL_USER')
    password = os.getenv('MYSQL_PASSWORD')
    host = os.getenv('MYSQL_HOST')
    port = os.getenv('MYSQL_PORT')
    db = os.getenv('MYSQL_DATABASE')
    url = f"mysql+pymysql://{user}:{password}@{host}:{port}/{db}?charset=utf8mb4"
    return create_engine(url)

def test_connection():
    try:
        engine = get_engine()
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
        return True
    except Exception as e:
        logger.error(f"DB Connection failed: {e}")
        raise

def execute_sql(sql, params=None):
    engine = get_engine()
    with engine.connect() as conn:
        result = conn.execute(text(sql), params or {})
        conn.commit()
        return result

def read_sql(sql, params=None):
    import pandas as pd
    engine = get_engine()
    return pd.read_sql(text(sql), engine, params=params)
