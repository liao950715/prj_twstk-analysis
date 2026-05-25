# 台股資料分析與隔日漲幅預測系統
# Taiwan Stock Analysis System

## 專案簡介

這是一個台股公開資料蒐集、儲存、分析與 Dashboard 監控系統。系統透過 TWSE Open API、FinMind API 等資料來源取得台股資料，使用 Python 進行資料清洗、分析與寫入 MariaDB，並以 Flask Dashboard 監控資料更新狀態、分析結果與系統執行情況。

本專案的目標是建立一個可自動化更新與分析的台股資料流程，並產生隔日上漲機率較高的股票清單，作為後續觀察與分析依據。

## 核心功能

- **台股公開資料蒐集**: 自動抓取證交所與 FinMind 之股價與法人籌碼資料。
- **資料庫整合**: 使用 MariaDB 存儲結構化交易數據與預測結果。
- **資料清洗與特徵工程**: 基於歷史數據計算分析特徵。
- **隔日上漲機率分析**: 透過 Scikit-learn 模型進行預測並產生 Top 20 觀察清單。
- **Flask Dashboard**: 可視化監控系統狀態、抓取進度與分析日誌。
- **Docker 化環境**: 使用 Docker Compose 快速建置資料庫環境。
- **自動化排程**: 支援每日定時執行資料更新與預測任務。

## AI Agent 開發輔助

本專案使用 **Hermes AI Agent** 協助進行任務拆解、程式修改、資料流程整理、錯誤排查與驗收回報。開發過程中結合 **Gemini 3 Flash Preview** 作為核心邏輯生成與代碼優化之輔助模型。

## 技術架構

- **Language**: Python 3.12
- **Web Framework**: Flask
- **Database**: MariaDB (via Docker)
- **Data Processing**: Pandas, NumPy
- **Machine Learning**: Scikit-learn, Joblib
- **ORM**: SQLAlchemy, PyMySQL
- **API Support**: TWSE Open API, FinMind API, yfinance
- **AI Tooling**: Hermes AI Agent, Gemini 3 Flash Preview

## 專案結構

```text
twstk_prj/
├── web/                # Flask Dashboard 應用
├── scripts/            # 資料抓取、分析與預測腳本
├── sql/                # 資料庫初始化 SQL
├── models/             # 訓練好的模型存檔
├── docs/               # 專案技術文檔
├── logs/               # 系統執行日誌
├── output/             # 分析報告輸出
├── data/               # 暫存原始資料 (已排除)
├── docker-compose.yml  # Docker 環境設定
├── .env.example        # 環境變數範例
├── requirements.txt    # 依賴套件清單
└── README.md
```

## 如何執行

1. **建立 Python 虛擬環境**
   ```bash
   python -m venv venv
   source venv/bin/activate  # Linux/macOS
   ```

2. **安裝套件**
   ```bash
   pip install -r requirements.txt
   ```

3. **設定環境變數**
   ```bash
   cp .env.example .env
   # 編輯 .env 並填入正確的資料庫帳密與 API Token
   ```

4. **啟動 Docker MariaDB**
   ```bash
   docker-compose up -d
   ```

5. **初始化資料庫與抓取資料**
   ```bash
   python scripts/run_daily.py
   ```

6. **啟動 Dashboard**
   ```bash
   python web/app.py
   ```

## 環境變數

請參考 `.env.example` 進行設定：
- `MYSQL_PASSWORD`: 資料庫密碼
- `FINMIND_API_TOKEN`: FinMind 提供的 API Token
- `FLASK_SECRET_KEY`: Flask Session 安全金鑰

## 開發狀態

目前為系統雛形 (Prototype)。已完成核心資料抓取流程、資料庫寫入自動化、基本特徵工程與 Dashboard 展示。

## 未來規劃

- 改善模型評估方式與增加多樣化回測指標。
- 增加更多技術指標 (KD, MACD, RSI) 與基本面因子。
- 強化 Dashboard 視覺化互動功能。
- 完善 Docker 化部署流程與 CI/CD 整合。

## 注意事項

本專案僅作為資料分析、程式開發與 AI Agent 工作流程練習，不構成任何投資建議。投資有風險，入市需謹慎。
