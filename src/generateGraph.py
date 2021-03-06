# TODO: Try this instead of plotly http://rrag.github.io/react-stockcharts/documentation.html
# This one might be good, too, it was in the pandas tutorial https://matplotlib.org/

import json
import plotly
import plotly.graph_objs as go
import numpy as np

log = json.load(open("../output_files/structuredlog.json", "r"))
prices = [x["price"] for x in log if "price" in x]
fastEMAs = [x["fastEMAValue"] for x in log if "fastEMAValue" in x]
slowEMAs = [x["slowEMAValue"] for x in log if "slowEMAValue" in x]
volume = [x["volume"] for x in log if "price" in x]
x = list(range(0, len(prices)))

data = [go.Scatter(x = x, y = prices, name="prices"), \
        go.Scatter(x = x, y = fastEMAs, name="fastEMA"), \
        go.Scatter(x = x, y = slowEMAs, name="slowEMA")]

plotly.offline.plot(data, filename='../output_files/graph.html')
