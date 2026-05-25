# Database Schema

## 資料庫名稱
- `stock_db` (預設)

## 主要資料表
1. `stock_info`: 股票基本資料 (代碼、名稱、產業)。
2. `daily_price`: 每日股價資料 (開高低收、成交量)。
3. `chip_info`: 籌碼面資料 (法人買賣超)。
4. `predictions`: 模型預測結果。

## 欄位摘要
- `stock_id` (PK): 股票代碼。
- `date` (PK): 交易日期。

## 每張表用途
- `daily_price` 用於計算技術面特徵。
- `chip_info` 用於分析法人動向。
