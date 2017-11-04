import json 

completeTickerData = json.load(open("BTC-LTC.json", "r"))
for market in completeTickerData:
    marketName = market["market"]
    if "BTC-LTC" == marketName:
        string = json.dumps(market)
        f = open("BTC-LTC stripped.json", "w")
        f.write(string)
        f.close()