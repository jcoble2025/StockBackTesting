import pandas as pd
import numpy as np
from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer

# Load price data
data = pd.read_csv('/Users/jacksoncoble/StockBackTesting-3/Back Test/TSLA_5min.csv', parse_dates=['date'])
data = data.sort_values('date').reset_index(drop=True)

# Load real news data (must have 'datetime' and 'headline' columns)
news = pd.read_csv('/Users/jacksoncoble/StockBackTesting-3/Back Test/TSLA_Sample_News.csv', parse_dates=['datetime'])

# Score news headlines using VADER and map to 1-10
analyzer = SentimentIntensityAnalyzer()
def score_headline(text):
    compound = analyzer.polarity_scores(str(text))['compound']
    # Map compound (-1 to 1) to score (1 to 10)
    return int(round((compound + 1) * 4.5 + 1))

news['news_strength'] = news['headline'].apply(score_headline)

# Assign news_strength to the closest price bar at or after the news time
data['news_strength'] = np.nan
news = news.sort_values('datetime')
for _, row in news.iterrows():
    idx = data[data['date'] >= row['datetime']].index.min()
    if pd.notna(idx):
        data.at[idx, 'news_strength'] = row['news_strength']

# Generate trading signals based on news strength
data['Signal'] = 0.0
mask = data['news_strength'].notna()
# Map 1-10 to -1 to +1 linearly: Signal = (news_strength - 5.5) / 4.5
data.loc[mask, 'Signal'] = (data.loc[mask, 'news_strength'] - 5.5) / 4.5

# --- Larger sizings for strong news ---
# If news_strength is 1 or 10, use 100% of capital; if 2 or 9, use 75%; if 3 or 8, use 50%; else scale linearly
def sizing_factor(strength):
    if strength == 1 or strength == 10:
        return 1.0
    elif strength == 2 or strength == 9:
        return 0.75
    elif strength == 3 or strength == 8:
        return 0.5
    elif strength == 4 or strength == 7:
        return 0.3
    elif strength == 5 or strength == 6:
        return 0.15
    else:
        return 0.0

data['Sizing'] = data['news_strength'].apply(lambda x: sizing_factor(x) if not np.isnan(x) else 0.0)

# Calculate returns
data['Daily_Return'] = data['close'].pct_change()
data['Strategy_Return'] = data['Signal'].shift(1).fillna(0) * data['Daily_Return']
data['Cumulative_Profit'] = (1 + data['Strategy_Return'].fillna(0)).cumprod()

# Simulate trading with position sizing and P&L tracking
initial_cash = 1_000_000
cash = initial_cash
position = 0
entry_price = None
data['Position'] = 0
data['Holdings'] = 0.0
data['Cash'] = initial_cash
data['Total_Equity'] = initial_cash

for i, row in data.iterrows():
    if i == 0:
        data.at[i, 'Position'] = 0
        data.at[i, 'Holdings'] = 0.0
        data.at[i, 'Cash'] = initial_cash
        data.at[i, 'Total_Equity'] = initial_cash
        continue

    prev_position = data.at[i-1, 'Position']
    prev_cash = data.at[i-1, 'Cash']
    price = row['close']
    signal = row['Signal']
    sizing = row['Sizing']

    # Buy signal: go in with sizing if not already in position
    if signal > 0 and prev_position == 0 and sizing > 0:
        shares_to_buy = int((prev_cash * sizing) // price)
        cost = shares_to_buy * price
        position = shares_to_buy
        cash = prev_cash - cost
        entry_price = price if shares_to_buy > 0 else None
    # Sell signal: close position if in position
    elif signal < 0 and prev_position > 0:
        cash = prev_cash + prev_position * price
        position = 0
        entry_price = None
    else:
        position = prev_position
        cash = prev_cash

    holdings = position * price
    total_equity = cash + holdings

    data.at[i, 'Position'] = position
    data.at[i, 'Holdings'] = holdings
    data.at[i, 'Cash'] = cash
    data.at[i, 'Total_Equity'] = total_equity

# Log all trades to CSV with P&L, position size, and holdings
trades = data[data['Signal'] != 0][['date', 'close', 'volume', 'news_strength', 'Signal', 'Sizing', 'Position', 'Holdings', 'Cash', 'Total_Equity']].copy()
trades['Trade_Type'] = trades['Signal'].apply(lambda x: 'Buy' if x > 0 else 'Sell')
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

# --- Add PnL for any open position at the end ---
if data['Position'].iloc[-1] > 0:
    last_buy_idx = trades[trades['Trade_Type'] == 'Buy'].index[-1]
    last_buy_price = trades.at[last_buy_idx, 'close']
    last_shares = trades.at[last_buy_idx, 'Position']
    final_price = data['close'].iloc[-1]
    trades.at[last_buy_idx, 'PnL'] = (final_price - last_buy_price) * last_shares

trades.to_csv('/Users/jacksoncoble/StockBackTesting-3/Back Test/newsTradeLog.csv', index=False)
print(f"Trade log saved to newsTradeLog.csv with {len(trades)} trades.")

# Buy and hold for comparison
buy_and_hold_profit = (data['close'].iloc[-1] / data['close'].iloc[0]) - 1

# Print results
final_profit = data['Cumulative_Profit'].iloc[-1] - 1
print(f"News Trading Strategy Profit: {final_profit * 100:.2f}%")
print(f"Buy and Hold Profit: {buy_and_hold_profit * 100:.2f}%")

# Optional: Show last few rows
print(data[['date', 'close', 'news_strength', 'Signal', 'Sizing', 'Cumulative_Profit']].tail())