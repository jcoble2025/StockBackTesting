import pandas as pd
import os

# Read CSV, parse dates, and sort by date to ensure correct order
data = pd.read_csv('/Users/jacksoncoble/StockBackTesting/Back Test/TSLA_5min.csv', parse_dates=['date'])
data = data.sort_values('date').reset_index(drop=True)

# Check for required columns
required_cols = {'date', 'close', 'volume'}
if not required_cols.issubset(data.columns):
    raise ValueError(f"CSV must contain columns: {required_cols}")

# Save the original close prices for buy and hold calculation
original_close = data['close'].copy()

# Define separate volume thresholds for above and below average
volume_threshold_below = .88  # 25% below average
volume_threshold_above = 500  # 50% above average

# Test different long-term MA windows
results = []
for long_window in range(100, 1001, 100):
    print(f"\nTesting MA combination: MA_10 vs MA_{long_window}")
    
    # Calculate moving averages
    data['MA_10'] = data['close'].rolling(window=30).mean()
    data[f'MA_{long_window}'] = data['close'].rolling(window=long_window).mean()
    
    # Calculate 24-hour volume metrics (288 = 12 5-min bars per hour * 24 hours)
    data['Avg_Vol_24h'] = data['volume'].rolling(window=288).mean()
    data['Vol_Lower_Bound'] = data['Avg_Vol_24h'] * (1 - volume_threshold_below)
    data['Vol_Upper_Bound'] = data['Avg_Vol_24h'] * (1 + volume_threshold_above)
    
    # Drop rows with NaN
    temp_data = data.dropna(subset=['MA_10', f'MA_{long_window}', 'Avg_Vol_24h', 'Vol_Lower_Bound', 'Vol_Upper_Bound']).copy()
    
    # Signal logic
    temp_data['Signal'] = 0
    within_volume_range = (temp_data['volume'] >= temp_data['Vol_Lower_Bound']) & (temp_data['volume'] <= temp_data['Vol_Upper_Bound'])
    temp_data.loc[(temp_data['MA_10'] > temp_data[f'MA_{long_window}']) & within_volume_range, 'Signal'] = 1
    temp_data.loc[(temp_data['MA_10'] < temp_data[f'MA_{long_window}']) & within_volume_range, 'Signal'] = -1
    
    # Calculate returns
    temp_data['Daily_Return'] = temp_data['close'].pct_change()
    temp_data['Strategy_Return'] = temp_data['Signal'].shift(1) * temp_data['Daily_Return']
    temp_data['Cumulative_Profit'] = (1 + temp_data['Strategy_Return'].fillna(0)).cumprod()
    
    if not temp_data.empty:
        final_profit = temp_data['Cumulative_Profit'].iloc[-1] - 1
        results.append({
            'Long_Window': long_window,
            'Profit': final_profit * 100
        })
        print(f"MA_{long_window} Strategy Profit: {final_profit * 100:.2f}%")

# Print summary of results
print("\nStrategy Results Summary:")
print("=" * 50)
print("Moving Average Window | Profit (%)")
print("-" * 50)

# Convert results to DataFrame and sort by Long_Window
results_df = pd.DataFrame(results)
results_df['Long_Window'] = results_df['Long_Window'].astype(int)
results_df = results_df.sort_values('Long_Window')

# Print formatted results
for _, row in results_df.iterrows():
    print(f"MA_{int(row['Long_Window']):4d}           | {row['Profit']:8.2f}%")
print("=" * 50)

# Calculate and display buy-and-hold profit
buy_and_hold_profit = (original_close.iloc[-1] / original_close.iloc[0]) - 1
print(f"\nBuy and Hold Strategy | {buy_and_hold_profit * 100:8.2f}%")