# Project Status

## 目前完成內容
- 台股資料蒐集模組 (TWSE, FinMind, yfinance)
- MariaDB 資料庫架構與自動化寫入
- 機器學習分析流程 (特徵工程、模型訓練、隔日漲幅預測)
- Flask Dashboard 監控系統
- 自動化排程執行腳本

## 目前資料流程
1. `run_daily.py` 啟動每日任務。
2. 透過 `fetch_twse.py` 與 `fetch_finmind.py` 抓取最新股價與籌碼資料。
3. 資料清洗後存入 MariaDB。
4. `build_features.py` 產生模型所需特徵。
5. `predict_top20.py` 產生預測清單。
6. Dashboard 展示結果。

## 可執行腳本
- `scripts/run_daily.py`: 每日完整自動化流程。
- `scripts/fetch_twse.py`: 單獨抓取證交所資料。
- `scripts/fetch_finmind.py`: 單獨抓取 FinMind 資料。
- `web/app.py`: 啟動 Flask Dashboard。

## Dashboard 狀態
- 基本系統監控、日誌查看、預測結果展示。

## 已知問題
- 部分冷門股資料可能缺失。
- 模型準確率仍有提升空間。

## 下一步
- 增加技術指標 (KD, RSI, MACD)。
- 建立自動化回測系統。
