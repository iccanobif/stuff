# TODO: Prova questo invece che plotly http://rrag.github.io/react-stockcharts/documentation.html

import json
import plotly
import plotly.graph_objs as go
import numpy as np

log = json.load(open("structuredlog.json", "r"))
prices = [x["price"] for x in log if "price" in x]
fastSMAs = [x["fastSMAValue"] for x in log if "fastSMAValue" in x]
slowSMAs = [x["slowSMAValue"] for x in log if "slowSMAValue" in x]
volume = [x["volume"] for x in log if "price" in x]
x = list(range(0, len(prices)))

data = [go.Scatter(x = x, y = prices, name="prices"), \
        go.Scatter(x = x, y = fastSMAs, name="fastSMA"), \
        go.Scatter(x = x, y = slowSMAs, name="slowSMA")]

plotly.offline.plot(data, filename='graph.html')