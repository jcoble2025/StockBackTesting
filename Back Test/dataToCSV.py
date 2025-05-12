from alpha_vantage.timeseries import TimeSeries
api_key = "UOQHB0PX20BCGFOB"
ts = TimeSeries(key=api_key, output_format='pandas')

data, _ = ts.get_intraday(
    symbol="TSLA",
    interval="5min",
    outputsize="full"
)
data.to_csv("TSLA_5min.csv")