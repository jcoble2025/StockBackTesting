import pandas as pd
data = pd.read_csv('TSLA_5min.csv')
data['MA_10'] = data['close'].rolling(window=10).mean() #last 10 ticker mean
data['MA_100'] = data['close'].rolling(window=100).mean() #last 100 ticker mean
#print(data[['date', 'close', 'MA_10', 'MA_100']].tail())
#test to confirm calculations

data['Signal'] = 0
data.loc[data['MA_10'] > data['MA_100'], 'Signal'] = 1
data.loc[data['MA_10'] < data['MA_100'], 'Signal'] = -1
print(data[['date', 'close', 'MA_10', 'MA_100', 'Signal']])



# Calculate daily returns and strategy returns
data['Daily_Return'] = data['close'].pct_change()
data['Strategy_Return'] = data['Signal'].shift(1) * data['Daily_Return']
data['Cumulative_Profit'] = (1 + data['Strategy_Return']).cumprod()
final_profit = data['Cumulative_Profit'].iloc[-1]-1
print(f"Total Strategy Profit: {final_profit *100:.2f}%")