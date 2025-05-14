import pandas as pd
import os

data = pd.read_csv('/Users/jacksoncoble/StockBackTesting/Back Test/TSLA_5min.csv')

# Check for required columns
required_cols = {'date', 'close', 'volume'}
if not required_cols.issubset(data.columns):
    raise ValueError(f"CSV must contain columns: {required_cols}")

# Save the original close prices for buy and hold calculation
original_close = data['close'].copy()

data['MA_10'] = data['close'].rolling(window=10).mean()
data['MA_500'] = data['close'].rolling(window=200).mean()

# Calculate rolling average volume for the last 24 hours (assuming 5min bars: 12 bars/hour * 24 = 288)
data['Avg_Vol_24h'] = data['volume'].rolling(window=288).mean()

# Drop rows with NaN in moving averages or average volume
data = data.dropna(subset=['MA_10', 'MA_500', 'Avg_Vol_24h']).reset_index(drop=True)

data['Signal'] = 0
# Only trade if volume is within 25% of the 24h average volume
within_25pct = (data['volume'] >= 0.75 * data['Avg_Vol_24h']) & (data['volume'] <= 1.25 * data['Avg_Vol_24h'])

data.loc[(data['MA_10'] > data['MA_500']) & within_25pct, 'Signal'] = 1
data.loc[(data['MA_10'] < data['MA_500']) & within_25pct, 'Signal'] = -1

print(data[['date', 'close', 'volume', 'MA_10', 'MA_500', 'Avg_Vol_24h', 'Signal']].tail())

# Calculate daily returns and strategy returns
data['Daily_Return'] = data['close'].pct_change()
data['Strategy_Return'] = data['Signal'].shift(1) * data['Daily_Return']
data['Cumulative_Profit'] = (1 + data['Strategy_Return'].fillna(0)).cumprod()

# Calculate buy-and-hold profit for the entire dataset (before dropping NaNs)
buy_and_hold_profit = (original_close.iloc[-1] / original_close.iloc[0]) - 1

if not data.empty:
    final_profit = data['Cumulative_Profit'].iloc[-1] - 1
    print(f"Total Strategy Profit: {final_profit * 100:.2f}%")
    print(f"Buy and Hold Profit (entire dataset): {buy_and_hold_profit * 100:.2f}%")
else:
    print("No data available after preprocessing.")