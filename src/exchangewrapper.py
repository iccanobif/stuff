import datetime, calendar, json, os, time, requests, hashlib, hmac

import config, utilities
from dtos import Candle, Tick
from logger import Logger

class ExchangeWrapperForBacktesting:

    class TickIterator:
        def __init__(self, marketName):
            self.marketName = marketName
            self.f = open(config.backtestingDataDirectory + "/" + marketName + ".json")
            self.currTick = None

        def get(self, timestamp):
            if self.f.closed:
                return None
            # Can't ask for ticks that were already read
            if self.currTick is not None and timestamp < self.currTick.getTimestamp():
                Logger.log("timestamp " + str(timestamp))
                Logger.log("currTick.getTimestamp " + str(self.currTick.getTimestamp()))
                raise Exception("gotta make it so that the caller doesn't bother getting candles for markets that haven't even been listed yet :)")
            # If asked for tick in the future, go find it even if i have to skip some
            while self.currTick is None or self.currTick.getTimestamp() < timestamp:
                line = self.f.readline()
                if line == "":
                     self.f.close()
                     return None
                self.currTick = Candle(self.marketName, json.loads(line))
            return self.currTick # Returns the current tick (it's the one I was asked for)

    def __init__(self):
        self.currentTime = datetime.datetime.strptime("2017-09-06T00:00:00", config.timestampStringFormat)
        self.iterators = dict()

        self.currentBalance = 100
        self.currentCurrency = config.baseCurrency

        for marketName in os.listdir(config.backtestingDataDirectory):
            if not marketName.endswith(".json"):
                continue
            marketName = marketName.replace(".json", "")
            self.iterators[marketName] = self.TickIterator(marketName)

    def getCurrentTick(self, marketName):
        # Returns a Tick object
        candle = self.iterators[marketName].get(self.currentTime)
        return Tick(candle)

    def getCurrentCandle(self, marketName):
        # Returns a Candle object
        return self.iterators[marketName].get(self.currentTime)

    def wait(self):
        # Simulate the passage of time when backtesting
        # Adds 60 seconds
        Logger.log("Waiting...")
        self.currentTime = self.currentTime + datetime.timedelta(seconds=60)

    def getMarketList(self):
        return self.iterators.keys()

    def buy(self, market, quantity, rate):
        # 1 CURR = rate BTC
        if self.currentCurrency != "BTC":
            raise Exception("Already bought!")
        Logger.log("BUY!")
        self.currentBalance = self.currentBalance / rate * config.bittrexCommission
        self.currentCurrency = market.split("-")[1]

    #TODO: make quantity and rate optional, at least for the backtester
    def sell(self, market, quantity, rate):
        if self.currentCurrency == "BTC":
            raise Exception("Already sold!")
        Logger.log("SELL!")
        self.currentBalance = self.currentBalance * rate * config.bittrexCommission
        self.currentCurrency = "BTC"

    def getCurrentBalance(self):
        return self.currentBalance

    def getCurrentCurrency(self):
        return self.currentCurrency

    def getMarketSummary(self):
        return [{"MarketName": m, "BaseVolume": 9999} for m in self.iterators.keys()]

class ExchangeWrapper:

    def getCurrentTick(self, marketName):
        # Returns an object with the properties Bid, Ask and Last
        initialTime = time.clock()
        response = requests.get("https://bittrex.com/api/v1.1/public/getticker?market=%s" % marketName)
        response.raise_for_status()
        j = response.json()
        if j["success"] != True:
            raise Exception(j["message"])
        output = Tick()
        output.market = marketName
        output.price = j["result"]["Last"]
        output.ask = j["result"]["Ask"]
        output.bid = j["result"]["Bid"]
        output.timestamp = datetime.datetime.fromtimestamp(time.time())
        # print(time.clock() - initialTime)
        return output
 
    def getCurrentCandle(self, marketName, timeWindow = "oneMin"):
        # Alas, this is very unreliable! Can return candles in the wrong order, skips candles...
        url = "https://bittrex.com/Api/v2.0/pub/market/GetLatestTick?marketName=%s&tickInterval=%s" % (marketName, timeWindow)
        response = requests.get(url)
        response.raise_for_status()
        j = response.json()
        if j["success"] != True:
            raise Exception(j["message"])
        return Candle(marketName, j["result"][0])

    def GetAllCandles(self, marketName, timeWindow = "oneMin"):
        url = "https://bittrex.com/Api/v2.0/pub/market/GetTicks?marketName=%s&tickInterval=%s" % (marketName, timeWindow)
        response = requests.get(url)
        response.raise_for_status()
        j = response.json()
        if j["success"] != True:
            raise Exception(j["message"])
        return [Candle(marketName, x) for x in j["result"]]

    def getMarketList(self):
        response = requests.get("https://bittrex.com/api/v1.1/public/getmarkets")
        response.raise_for_status()
        j = response.json()
        if j["success"] != True:
            raise Exception(j["message"])
        return [x for x in response.json()["result"] if x["BaseCurrency"] == "BTC"]

    def getMarketSummary(self):
        # This one's got statistics for the last 24 hours
        response = requests.get("https://bittrex.com/api/v1.1/public/getmarketsummaries")
        response.raise_for_status()
        j = response.json()
        if j["success"] != True:
            raise Exception(j["message"])
        return [x for x in response.json()["result"] if x["MarketName"].startswith("BTC-")]

    def getSellOrderBook(self, marketName):
        url = "https://bittrex.com/api/v1.1/public/getorderbook?market=%s&type=sell" % marketName
        response = requests.get(url)
        response.raise_for_status()
        j = response.json()
        if j["success"] != True:
            raise Exception(j["message"])
        return j["result"]

    def getBuyOrderBook(self, marketName):
        url = "https://bittrex.com/api/v1.1/public/getorderbook?market=%s&type=buy" % marketName
        response = requests.get(url)
        response.raise_for_status()
        j = response.json()
        if j["success"] != True:
            raise Exception(j["message"])
        return j["result"]

    def runMarketOperation(self, url, postParameters=None):
        # Handles all the HMAC authentication stuff
        # Check wether in the url there are already GET parameters or not
        # TODO: More elegant to use requests.get()'s "params" parameter
        if url.find("?") < 0:
            url = url + "?"
        else:
            url = url + "&"

        nonce = int(time.time())
        url = url + "apikey=%s&nonce=%s" % (config.bittrexKey, nonce)
        signature = hmac.new(config.bittrexSecret.encode(), url.encode(), hashlib.sha512).hexdigest()
        headers = {"apisign": signature}
        response = None
        if postParameters is None:
            response = requests.get(url, headers=headers)
        else:
            response = requests.post(url, headers=headers, data=postParameters)
        response.raise_for_status()
        j = response.json()
        if j["success"] != True:
            raise Exception(j["message"])
        return j

    def buyLimit(self, marketName, quantity, rate):
        # The quantity is in the target currency, I think
        Logger.log("BUY!")
        if not config.enableActualTrading:
            return
        url = "https://bittrex.com/api/v1.1/market/buylimit?market=%s&quantity=%s&rate=%s" % (marketName, str(quantity), str(rate))
        j = self.runMarketOperation(url)
        
    def sellLimit(self, market, quantity, rate):
        # The quantity is in the target currency, I think
        Logger.log("SELL!")
        if not config.enableActualTrading:
            return

    def sell(self, marketName, quantity, rate):
        # This one uses the v2.0 API
        #
        # quantity/rate must be > 0,0005
        # quantity must be > MinTradeSize (get it with GetMarkets)
        Logger.log("SELL!")
        if not config.enableActualTrading:
            return
        url = "https://bittrex.com/Api/v2.0/key/market/TradeSell"
        params = {
            "ConditionType": "NONE", \
            "MarketName": marketName, \
            "OrderType": "LIMIT", \
            "Quantity": str(quantity), \
            "Rate": str(rate), \
            "Target": 0, \
            "TimeInEffect": "IMMEDIATE_OR_CANCEL"} # Possible values: 'IMMEDIATE_OR_CANCEL', 'GOOD_TIL_CANCELLED', 'FILL_OR_KILL'
        j = self.runMarketOperation(url, postParameters=params)
        return j["result"]

    def marketSell(self, marketName, quantity):
        # Simulates a market sell by selling at the lowest price that wouldn't trigger a
        # DUST_TRADE_DISALLOWED_MIN_VALUE_50K_SAT error, trusting that bittrex will sell at the best
        # prices available anyway (r-right?).
        # Returns the amount of coins that weren't sold (it should happen only if the buy orderbook is empty
        # or the quantity is so low that there's nobody willing to buy it at a rate that would make it worth more
        # than 50k sats, for example trying to sell 7 XRP when the current price is less than 7142 satoshi)

        # TODO: Cancel all pending sell orders for this market:

        rate=0.0005/quantity # This is the rate that makes the estimated bitcoin value of the sale of "quantity" coins equal to 50k sats
        Logger.log("Trying to sell %f on market %s" % (quantity, marketName))
        result = self.sell(marketName, quantity, rate)
        order = self.getOrder(result["OrderId"])
        return order["QuantityRemaining"]

    def buy(self, marketName, quantity, rate):
        pass

    def marketBuy(self, marketname, quantity):
        pass

    def getOrderHistory(self):
        #
        # Gets old orders... Not particularly useful for me
        #
        j = self.runMarketOperation("https://bittrex.com/api/v1.1/account/getorderhistory")
        return j

    def getOrder(self, orderId):
        j = self.runMarketOperation("https://bittrex.com/api/v1.1/account/getorder?uuid=%s" % orderId)
        return j["result"]

    def getBalances(self):
        # Return a dictionary mapping currency names to the corresponding balance
        j = self.runMarketOperation("https://bittrex.com/api/v1.1/account/getbalances")
        return dict([(x["Currency"], x["Balance"]) for x in j["result"] if x["Balance"] > 0])

    def wait(self):
        time.sleep(1)

# def test():
#     ex = ExchangeWrapperForBacktesting()
#     for i in range(1000):
#         print(ex.getCurrentTick("BTC-LTC"))
#         ex.wait()

#TODO: Make a single ExchangeWrapper that depends on a BacktestingExchangeWrapper class
#      and a BittrexExchangeWrapper class

def test():
    Logger.open()
    ex = ExchangeWrapper()
    # print(len(ex.getMarketList()))
    # print(ex.getCurrentTick("BTC-LTC"))
    # print(ex.GetAllCandles("BTC-MONA")[0])
    # print(ex.getCurrentCandle("BTC-MONA"))
    # for i in ex.getSellOrderBook("BTC-MONA"):
        # print(i)
    # for m in ex.getMarketSummary():
    #     print(m["MarketName"], m["BaseVolume"])

    # print(ex.sell("BTC-XRP", quantity=8, rate=0.00006300))
    # print(ex.sell("BTC-XRP", quantity=24, rate=0.0006300))
    # print(ex.sell("BTC-XRP", quantity=8, rate=0.0005/8))

    # print(ex.marketSell("BTC-XRP", 8))
    # utilities.prettyPrintJSON(ex.getOrder("orderid"))
    # print(ex.getBuyOrderBook("BTC-XRP"))

    # print(ex.getBalances())
    print(utilities.prettyPrintJSONVertical(ex.getOrderHistory()))
    Logger.close()

if __name__ == "__main__":
    test()
