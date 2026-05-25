import os
import sys
from flask import Flask, render_template, request, jsonify
from sqlalchemy import create_engine, text
from dotenv import load_dotenv
import pandas as pd
from datetime import datetime, timedelta

# Add parent directory to sys.path to import from scripts
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

load_dotenv()

app = Flask(__name__)

# DB Connection
MYSQL_USER = os.getenv("MYSQL_USER")
MYSQL_PASSWORD = os.getenv("MYSQL_PASSWORD")
MYSQL_HOST = os.getenv("MYSQL_HOST")
MYSQL_PORT = os.getenv("MYSQL_PORT")
MYSQL_DATABASE = os.getenv("MYSQL_DATABASE")

DB_URL = f"mysql+pymysql://{MYSQL_USER}:{MYSQL_PASSWORD}@{MYSQL_HOST}:{MYSQL_PORT}/{MYSQL_DATABASE}"
engine = create_engine(DB_URL)

def get_db_data(query, params=None):
    try:
        with engine.connect() as conn:
            result = conn.execute(text(query), params or {})
            if result.returns_rows:
                return pd.DataFrame(result.fetchall(), columns=result.keys())
            return None
    except Exception as e:
        print(f"Database error: {e}")
        return None

def mask_secrets(text_content):
    if not text_content:
        return ""
    token = os.getenv("FINMIND_API_TOKEN")
    pwd = os.getenv("MYSQL_PASSWORD")
    root_pwd = os.getenv("MYSQL_ROOT_PASSWORD")
    if token: text_content = text_content.replace(token, "********")
    if pwd: text_content = text_content.replace(pwd, "********")
    if root_pwd: text_content = text_content.replace(root_pwd, "********")
    return text_content

@app.route('/')
def index():
    stats = {}
    
    try:
        with engine.connect() as conn:
            # 1. 系統狀態總覽
            stats['stock_master_count'] = conn.execute(text("SELECT COUNT(*) FROM stock_master")).scalar()
            stats['daily_price_count'] = conn.execute(text("SELECT COUNT(*) FROM daily_price")).scalar()
            stats['stock_features_count'] = conn.execute(text("SELECT COUNT(*) FROM stock_features")).scalar()
            
            check_table = conn.execute(text("SHOW TABLES LIKE 'prediction_top20'")).fetchone()
            if check_table:
                stats['prediction_top20_count'] = conn.execute(text("SELECT COUNT(*) FROM prediction_top20")).scalar()
            else:
                stats['prediction_top20_count'] = 0
            
            trade_days_res = conn.execute(text("SELECT COUNT(DISTINCT trade_date), MIN(trade_date), MAX(trade_date) FROM daily_price")).fetchone()
            stats['collected_trade_days'] = trade_days_res[0] or 0
            stats['first_trade_date'] = trade_days_res[1]
            stats['latest_trade_date'] = trade_days_res[2]
            stats['is_ready'] = stats['collected_trade_days'] >= 14
            stats['days_to_go'] = max(0, 14 - stats['collected_trade_days'])
            
            # 2. 每日更新資料量
            daily_vol_df = get_db_data("""
                SELECT trade_date, COUNT(*) AS rows_count, MIN(created_at) AS first_created_at, MAX(updated_at) AS last_updated_at
                FROM daily_price GROUP BY trade_date ORDER BY trade_date DESC LIMIT 20
            """)
            stats['daily_vol'] = daily_vol_df.to_dict(orient='records') if daily_vol_df is not None else []
            
            # 3. 今日更新狀態
            today_status_res = conn.execute(text("""
                SELECT trade_date, COUNT(*) AS rows_count, MIN(updated_at) AS first_updated_at, MAX(updated_at) AS last_updated_at
                FROM daily_price GROUP BY trade_date ORDER BY trade_date DESC LIMIT 1
            """)).fetchone()
            if today_status_res:
                stats['today_status'] = {
                    'trade_date': today_status_res[0],
                    'rows_count': today_status_res[1],
                    'first_updated_at': today_status_res[2],
                    'last_updated_at': today_status_res[3],
                    'is_today': str(today_status_res[0]) == datetime.now().strftime('%Y-%m-%d')
                }
            else:
                stats['today_status'] = None
                
            # 4. 資料來源分布
            src_dist = conn.execute(text("SELECT data_source, COUNT(*) FROM daily_price GROUP BY data_source ORDER BY COUNT(*) DESC")).fetchall()
            stats['data_source_dist'] = {row[0]: row[1] for row in src_dist}
            
            # 5. API request 狀態
            api_stats_df = get_db_data("""
                SELECT api_name, status_code, success, COUNT(*) AS cnt
                FROM api_request_log GROUP BY api_name, status_code, success ORDER BY api_name, status_code
            """)
            stats['api_stats'] = api_stats_df.to_dict(orient='records') if api_stats_df is not None else []
            
            finmind_hour = conn.execute(text("""
                SELECT COUNT(*) FROM api_request_log 
                WHERE api_name = 'FinMind' AND request_time >= NOW() - INTERVAL 1 HOUR
            """)).scalar()
            stats['finmind_requests_last_hour'] = finmind_hour or 0
            
            has_errors = conn.execute(text("SELECT COUNT(*) FROM api_request_log WHERE status_code IN (402, 403)")).scalar()
            stats['api_has_limit_errors'] = has_errors > 0
            
            # 8. Feature 狀態
            feat_stats_res = conn.execute(text("""
                SELECT COUNT(*) AS feature_rows, COUNT(DISTINCT trade_date) AS feature_trade_days, 
                       MIN(trade_date) AS first_feature_date, MAX(trade_date) AS latest_feature_date
                FROM stock_features
            """)).fetchone()
            stats['feature_stats'] = {
                'total_rows': feat_stats_res[0],
                'trade_days': feat_stats_res[1],
                'first_date': feat_stats_res[2],
                'latest_date': feat_stats_res[3]
            }
            
            feat_daily_df = get_db_data("""
                SELECT trade_date, COUNT(*) AS rows_count FROM stock_features GROUP BY trade_date ORDER BY trade_date DESC LIMIT 20
            """)
            stats['feature_daily'] = feat_daily_df.to_dict(orient='records') if feat_daily_df is not None else []
            
            # 9. Top20 狀態
            top20_info = conn.execute(text("SELECT COUNT(*), MAX(prediction_date) FROM prediction_top20") if check_table else text("SELECT 0, NULL")).fetchone()
            stats['top20_stats'] = {
                'total_rows': top20_info[0] or 0,
                'latest_date': top20_info[1]
            }
            
            if stats['top20_stats']['total_rows'] > 0:
                top20_df = get_db_data("""
                    SELECT p.rank_no, p.stock_id, s.stock_name, p.predicted_up_prob, p.score
                    FROM prediction_top20 p LEFT JOIN stock_master s ON p.stock_id = s.stock_id
                    WHERE p.prediction_date = (SELECT MAX(prediction_date) FROM prediction_top20)
                    ORDER BY p.rank_no ASC LIMIT 20
                """)
                stats['latest_top20'] = top20_df.to_dict(orient='records') if top20_df is not None else []
            else:
                stats['latest_top20'] = []
                
            # 10. 自我改進建議
            imp_stats = conn.execute(text("SELECT severity, COUNT(*) FROM improvement_suggestions GROUP BY severity")).fetchall()
            stats['improvement_stats'] = {row[0]: row[1] for row in imp_stats}
            
            imp_recent_df = get_db_data("""
                SELECT issue_type, severity, description, suggested_action, created_at
                FROM improvement_suggestions ORDER BY created_at DESC LIMIT 5
            """)
            stats['improvement_recent'] = imp_recent_df.to_dict(orient='records') if imp_recent_df is not None else []
            
    except Exception as e:
        print(f"Index route DB error: {e}")
        # stats['error'] = str(e)

    # 6 & 7. Logs 健康狀態
    def analyze_log(path, n=20):
        if not os.path.exists(path):
            return {"exists": False, "mtime": "N/A", "lines": "", "has_error": False, "has_import_error": False}
        mtime = datetime.fromtimestamp(os.path.getmtime(path)).strftime('%Y-%m-%d %H:%M:%S')
        try:
            with os.popen(f"tail -n {n} {path}") as f:
                content = f.read()
                content = mask_secrets(content)
                has_error = "ERROR" in content.upper() or "TRACEBACK" in content.upper()
                has_import_error = "IMPORTERROR" in content.upper() or "RELATIVE IMPORT" in content.upper()
                return {"exists": True, "mtime": mtime, "lines": content, "has_error": has_error, "has_import_error": has_import_error}
        except:
            return {"exists": True, "mtime": mtime, "lines": "Error reading", "has_error": True, "has_import_error": False}

    stats['cron_health'] = analyze_log("/home/noir/py3_prj/twstk_prj/logs/cron.log")
    stats['app_health'] = analyze_log("/home/noir/py3_prj/twstk_prj/logs/app.log")

    return render_template('index.html', stats=stats)

@app.route('/stocks')
def stocks():
    df = get_db_data("SELECT stock_id, stock_name, market_type, industry, is_active, updated_at FROM stock_master LIMIT 100")
    stocks_list = df.to_dict(orient='records') if df is not None else []
    return render_template('stocks.html', stocks=stocks_list)

@app.route('/daily-price')
def daily_price():
    df = get_db_data("SELECT stock_id, trade_date, open_price, high_price, low_price, close_price, volume, turnover_amount, data_source FROM daily_price ORDER BY trade_date DESC, stock_id ASC LIMIT 200")
    prices = df.to_dict(orient='records') if df is not None else []
    return render_template('daily_price.html', prices=prices)

@app.route('/features')
def features():
    df = get_db_data("SELECT stock_id, trade_date, close_price, return_1d, ma3, ma5, rsi7, rsi14, volume_change_3d, label_next_day_up FROM stock_features ORDER BY trade_date DESC, stock_id ASC LIMIT 200")
    features_list = df.to_dict(orient='records') if df is not None else []
    return render_template('features.html', features=features_list)

@app.route('/top20')
def top20():
    try:
        with engine.connect() as conn:
            check_table = conn.execute(text("SHOW TABLES LIKE 'prediction_top20'")).fetchone()
            if not check_table:
                return render_template('top20.html', ready=False, message="prediction_top20 table does not exist yet.")
            
            trade_days = conn.execute(text("SELECT COUNT(DISTINCT trade_date) FROM daily_price")).scalar()
            if trade_days < 14:
                return render_template('top20.html', ready=False, message="目前仍在 14 個交易日資料蒐集期，尚未產生正式 Top20。")
            
            df = get_db_data("""
                SELECT p.rank_no, p.prediction_date, p.target_date, p.stock_id, s.stock_name, 
                       p.predicted_up_prob, p.score, p.close_price, p.rsi14, p.volume_change_5d, p.model_version 
                FROM prediction_top20 p
                LEFT JOIN stock_master s ON p.stock_id = s.stock_id
                ORDER BY p.prediction_date DESC, p.rank_no ASC
                LIMIT 20
            """)
            top20_list = df.to_dict(orient='records') if df is not None else []
            return render_template('top20.html', ready=True, top20=top20_list)
    except Exception as e:
        return f"Error: {e}"

@app.route('/logs')
def logs():
    def get_last_lines(filepath, n=100):
        if not os.path.exists(filepath):
            return "File not found."
        try:
            with os.popen(f"tail -n {n} {filepath}") as f:
                lines = f.read()
                lines = mask_secrets(lines)
                return lines
        except:
            return "Error reading log."

    app_log = get_last_lines("/home/noir/py3_prj/twstk_prj/logs/app.log")
    cron_log = get_last_lines("/home/noir/py3_prj/twstk_prj/logs/cron.log")
    
    return render_template('logs.html', app_log=app_log, cron_log=cron_log)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=False)
