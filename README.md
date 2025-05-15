# StockBackTesting
This script implements a **mean reversion trading strategy** on 5-minute bar data for TSLA. Here’s what it does, step by step:

1. **Loads Data:**  
   Reads a CSV file containing 5-minute OHLCV data for TSLA, parses dates, and sorts by date.

2. **Checks Columns:**  
   Ensures the CSV contains the required columns: `date`, `close`, and `volume`.

3. **Sets Parameters:**  
   - Uses a short moving average window of 25 bars (`MA_25`)
   - Uses a long moving average window of 600 bars (`MA_600`)
   - Sets volume thresholds: 88% below and 500% above the 24-hour average volume

4. **Calculates Indicators:**  
   - Computes the short and long moving averages
   - Computes the 24-hour rolling average volume and upper/lower volume bounds

5. **Filters Data:**  
   Drops rows with missing values in any of the calculated columns and resets the index for safe integer-based access.

6. **Generates Trading Signals:**  
   - **Buy (Signal = 1):** When `MA_25` crosses above `MA_600` and volume is within the specified bounds
   - **Sell (Signal = -1):** When `MA_25` crosses below `MA_600` and volume is within the specified bounds

7. **Simulates Trading:**  
   - Starts with $1,000,000 in cash
   - Buys as many shares as possible on a buy signal if not already in a position
   - Sells all shares on a sell signal if in a position
   - Tracks position size, holdings value, cash, and total equity at each step

8. **Calculates Returns:**  
   - Computes daily returns, strategy returns, and cumulative profit

9. **Logs Trades:**  
   - Records every buy and sell signal, including date, price, volume, position size, holdings, cash, total equity, trade type, and profit/loss (PnL) for each round-trip trade
   - Saves this log to `trade_log.csv`

10. **Prints Results:**  
    - Prints the final equity, total profit (absolute and percentage), and compares the strategy’s performance to a buy-and-hold approach

---

**In summary:**  
This script backtests a mean reversion strategy using moving averages and volume filters, simulates realistic position sizing, logs all trades with PnL, and compares the strategy’s performance to buy-and-hold.