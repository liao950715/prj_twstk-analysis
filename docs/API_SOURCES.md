# API Sources

## TWSE Open API
- 用途: 取得台股每日收盤行情、個股成交資訊。
- 限制: 頻率限制較寬鬆，適合作為主要資料源。

## FinMind API
- 用途: 取得法人買賣超、歷史價位等進階資料。
- 限制: 免費版有每小時請求次數限制。

## yfinance (Fallback)
- 用途: 作為證交所或 FinMind 資料異常時的備援方案。
