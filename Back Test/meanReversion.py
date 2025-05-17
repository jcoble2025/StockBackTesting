import pandas as pd
import os

# Read CSV, parse dates, and sort by date to ensure correct order
data = pd.read_csv('/Users/jacksoncoble/StockBackTesting-3/Back Test/TSLA_5min.csv', parse_dates=['date'])
data = data.sort_values('date').reset_index(drop=True)

# Check for required columns
required_cols = {'date', 'close', 'volume'}
if not required_cols.issubset(data.columns):
    raise ValueError(f"CSV must contain columns: {required_cols}")

# Save the original close prices for buy and hold calculation
original_close = data['close'].copy()

# Set moving average windows
short_window = 25
long_window = 600

# Define separate volume thresholds for above and below average
volume_threshold_below = 0.88  # 88% below average
volume_threshold_above = 5.00  # 500% above average

print(f"\nTesting MA combination: MA_{short_window} vs MA_{long_window}")

# Calculate moving averages
data[f'MA_{short_window}'] = data['close'].rolling(window=short_window).mean()
data[f'MA_{long_window}'] = data['close'].rolling(window=long_window).mean()

# Calculate 24-hour volume metrics (288 = 12 5-min bars per hour * 24 hours)
data['Avg_Vol_24h'] = data['volume'].rolling(window=288).mean()
data['Vol_Lower_Bound'] = data['Avg_Vol_24h'] * (1 - volume_threshold_below)
data['Vol_Upper_Bound'] = data['Avg_Vol_24h'] * (1 + volume_threshold_above)

# Drop rows with NaN and reset index for safe integer indexing
temp_data = data.dropna(subset=[f'MA_{short_window}', f'MA_{long_window}', 'Avg_Vol_24h', 'Vol_Lower_Bound', 'Vol_Upper_Bound']).copy()
temp_data = temp_data.reset_index(drop=True)

# Signal logic
temp_data['Signal'] = 0
within_volume_range = (temp_data['volume'] >= temp_data['Vol_Lower_Bound']) & (temp_data['volume'] <= temp_data['Vol_Upper_Bound'])
temp_data.loc[(temp_data[f'MA_{short_window}'] > temp_data[f'MA_{long_window}']) & within_volume_range, 'Signal'] = 1
temp_data.loc[(temp_data[f'MA_{short_window}'] < temp_data[f'MA_{long_window}']) & within_volume_range, 'Signal'] = -1

# --- Aggressive Sizing: Use leverage or a higher fraction of cash ---
leverage = 1.0  # 1.0 = no leverage, 2.0 = 2x leverage, etc.

# Define what percentage of liquidity (cash) to invest per trade (e.g., 1.0 = 100%, 0.5 = 50%)
liquidity_pct = 2.0  # Change this value as desired

initial_cash = 1_000_000
cash = initial_cash
position = 0  # Number of shares held
temp_data['Position'] = 0
temp_data['Holdings'] = 0.0
temp_data['Cash'] = float(initial_cash)
temp_data['Total_Equity'] = float(initial_cash)

for i, row in temp_data.iterrows():
    if i == 0:
        temp_data.at[i, 'Position'] = 0
        temp_data.at[i, 'Holdings'] = 0.0
        temp_data.at[i, 'Cash'] = float(initial_cash)
        temp_data.at[i, 'Total_Equity'] = float(initial_cash)
        continue

    prev_position = temp_data.at[i-1, 'Position']
    prev_cash = temp_data.at[i-1, 'Cash']
    price = row['close']
    signal = row['Signal']

    # Buy signal: invest a percentage of liquidity with leverage if not already in position
    if signal == 1 and prev_position == 0:
        buying_power = prev_cash * leverage * liquidity_pct
        shares_to_buy = int(buying_power // price)
        cost = shares_to_buy * price
        position = shares_to_buy
        cash = prev_cash - cost
    # Sell signal: close position if in position
    elif signal == -1 and prev_position > 0:
        cash = prev_cash + prev_position * price
        position = 0
    else:
        position = prev_position
        cash = prev_cash

    holdings = position * price
    total_equity = cash + holdings

    temp_data.at[i, 'Position'] = position
    temp_data.at[i, 'Holdings'] = holdings
    temp_data.at[i, 'Cash'] = cash
    temp_data.at[i, 'Total_Equity'] = total_equity

# Calculate returns
temp_data['Daily_Return'] = temp_data['close'].pct_change()
temp_data['Strategy_Return'] = temp_data['Signal'].shift(1) * temp_data['Daily_Return']
temp_data['Cumulative_Profit'] = (1 + temp_data['Strategy_Return'].fillna(0)).cumprod()

# Log all trades to CSV with P&L, position size, and holdings
trades = temp_data[temp_data['Signal'] != 0][['date', 'close', 'volume', 'Signal', 'Position', 'Holdings', 'Cash', 'Total_Equity']].copy()
trades['Trade_Type'] = trades['Signal'].map({1: 'Buy', -1: 'Sell'})
trades['PnL'] = 0.0
last_entry_price = None
last_entry_type = None
last_shares = 0

for i, row in trades.iterrows():
    if row['Trade_Type'] == 'Buy':
        last_entry_price = row['close']
        last_entry_type = 'Buy'
        last_shares = row['Position']
        trades.at[i, 'PnL'] = 0.0  # No PnL on entry
    elif row['Trade_Type'] == 'Sell' and last_entry_type == 'Buy' and last_entry_price is not None:
        trades.at[i, 'PnL'] = (row['close'] - last_entry_price) * last_shares
        last_entry_price = None
        last_entry_type = None
        last_shares = 0
    elif row['Trade_Type'] == 'Sell':
        trades.at[i, 'PnL'] = 0.0  # No shorting logic here

trades.to_csv('/Users/jacksoncoble/StockBackTesting-3/Back Test/trade_log.csv', index=False)
print(f"Trade log saved to trade_log.csv with {len(trades)} trades.")

# Print summary
if not temp_data.empty:
    final_profit = temp_data['Total_Equity'].iloc[-1] - initial_cash
    print(f"Final Equity: ${temp_data['Total_Equity'].iloc[-1]:,.2f}")
    print(f"Total Profit: ${final_profit:,.2f} ({final_profit/initial_cash*100:.2f}%)")

# Calculate and display buy-and-hold profit
buy_and_hold_profit = (original_close.iloc[-1] / original_close.iloc[0]) - 1
print(f"Buy and Hold Strategy: {buy_and_hold_profit * 100:8.2f}%")
print(f"I am better by {((temp_data['Total_Equity'].iloc[-1] / initial_cash - 1 - buy_and_hold_profit) * 100):8.2f}%")