import pandas as pd
import matplotlib.pyplot as plt

# Load the trade log CSV
df = pd.read_csv('trade_log.csv', comment='/', engine='python')

# Convert 'date' column to datetime
df['date'] = pd.to_datetime(df['date'])

# Plot the Total_Equity over time
plt.figure(figsize=(12, 6))
plt.plot(df['date'], df['Total_Equity'], marker='o', linestyle='-', color='b')
plt.title('Total Portfolio Value Over Time')
plt.xlabel('Date')
plt.ylabel('Total Portfolio Value')
plt.grid(True)
plt.tight_layout()
plt.show()