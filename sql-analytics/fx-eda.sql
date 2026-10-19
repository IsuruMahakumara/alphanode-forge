
WITH RankedDays AS (
    SELECT pair, trade_date, open, high, low, close,
           ROW_NUMBER() OVER (
               PARTITION BY DATE_FORMAT(trade_date, '%Y-%m')
               ORDER BY trade_date ASC
               ) as rn
    FROM yfinance_fx_eod
    WHERE pair = 'usd/lkr'
      AND DAY(trade_date) >= 25
)
SELECT  trade_date,  low
FROM RankedDays
WHERE rn = 1;