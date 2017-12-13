import datetime, calendar, json, os, time, requests, hashlib, hmac

import config
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
                log = Logger()
                log.log("timestamp " + str(timestamp))
                log.log("currTick.getTimestamp " + str(self.currTick.getTimestamp()))
                raise Exception("timestamp:")
            # If asked for tick in the future, go find it even if i have to skip some
            while self.currTick is None or self.currTick.getTimestamp() < timestamp:
                line = self.f.readline()
                if line == "":
                     self.f.close()
                     return None
                self.currTick = Candle(self.marketName, json.loads(line))
            return self.currTick # Returns the current tick (it's the one I was asked for)

    def __init__(self):
        self.currentTime = time.strptime("2017-09-05T22:31:00", config.timestampStringFormat)
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
        return self.iterators[marketName].get(self.currentTime)

    def wait(self):
        # Simulate the passage of time when backtesting
        # Adds 60 seconds
        self.currentTime = time.gmtime(calendar.timegm(self.currentTime) + 60)

    def getMarketList(self):
        pass

    def buy(self, market, quantity, rate):
        # 1 CURR = rate BTC
        if self.currentCurrency != "BTC":
            raise Exception("Already bought!")
        log = Logger()
        log.log("BUY!")
        self.currentBalance = self.currentBalance / rate * config.bittrexCommission
        self.currentCurrency = market.split("-")[1]

    #TODO: make quantity and rate optional, at least for the backtester
    def sell(self, market, quantity, rate): 
        if self.currentCurrency == "BTC":
            raise Exception("Already sold!")
        log = Logger()
        log.log("SELL!")
        self.currentBalance = self.currentBalance * rate * config.bittrexCommission
        self.currentCurrency = "BTC"

    def getCurrentBalance(self):
        return self.currentBalance

    def getCurrentCurrency(self):
        return self.currentCurrency

class ExchangeWrapper:

    def getCurrentTick(self, marketName):
        # Returns an object with the properties Bid, Ask and Last
        initialTime = time.clock()
        response = requests.get("https://bittrex.com/api/v1.1/public/getticker?market=%s" % marketName)
        response.raise_for_status()
        j = response.json()["result"]
        output = Tick()
        output.market = marketName
        output.price = j["Last"]
        output.ask = j["Ask"]
        output.bid = j["Bid"]
        output.timestamp = datetime.datetime.fromtimestamp(time.time())
        # print(time.clock() - initialTime)
        return output

    def getCurrentCandle(self, marketName, timeWindow = "oneMin"):
        url = "https://bittrex.com/Api/v2.0/pub/market/GetLatestTick?marketName=%s&tickInterval=%s" % (marketName, timeWindow)
        response = requests.get(url)
        response.raise_for_status()
        j = response.json()
        if j["success"] != True:
            raise Exception(j["message"])
        return Candle(marketName, j["result"][0])

    def getMarketList(self):
        response = requests.get("https://bittrex.com/api/v1.1/public/getmarkets")
        response.raise_for_status()
        if j["success"] != True:
            raise Exception(j["message"])
        return [x for x in response.json()["result"] if x["BaseCurrency"] == "BTC"]

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

    def runMarketOperation(self, url):
        # Handles all the HMAC authentication stuff
        # Check wether in the url there are already GET parameters or not
        if url.find("?") < 0:
            url = url + "?"
        else:
            url = url + "&"

        nonce = int(time.time())    
        url = url + "apikey=%s&nonce=%s" % (config.bittrexKey, nonce)
        signature = hmac.new(config.bittrexSecret.encode(), url.encode(), hashlib.sha512).hexdigest()
        headers = {"apisign": signature}
        response = requests.get(url, headers=headers)
        response.raise_for_status()
        return response.json()

    def buy(self, marketName, quantity, rate):
        log = Logger()
        log.log("BUY!")
        if not config.enableActualTrading:
            return
        url = "https://bittrex.com/api/v1.1/market/buylimit?market=%s&quantity=%s&rate=%s" % (marketName, str(quantity), str(rate))

    def sell(self, market, quantity, rate): 
        log = Logger()
        log.log("SELL!")
        if not config.enableActualTrading:
            return

    def getBalances(self):
        # Return a dictionary mapping currency names to the corresponding balance
        j = self.runMarketOperation("https://bittrex.com/api/v1.1/account/getbalances")
        if j["success"] != True:
            raise Exception(j["message"])
        
        return dict([(x["Currency"], x["Balance"]) for x in j["result"] if x["Balance"] > 0])

    def wait(self):
        time.sleep(1)

# def test():
#     ex = ExchangeWrapperForBacktesting()
#     for i in range(1000):
#         print(ex.getCurrentTick("BTC-LTC"))
#         ex.wait()

def test():
    ex = ExchangeWrapper()
    # print(len(ex.getMarketList()))
    # print(ex.getCurrentTick("BTC-LTC"))
    print(ex.getBalances())
    # print(ex.getCurrentCandle("BTC-MONA"))
    # for i in ex.getSellOrderBook("BTC-MONA"):
        # print(i)


if __name__ == "__main__":
    test()
