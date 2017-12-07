import datetime, calendar, json, os, time, requests

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
        self.currentTime = time.strptime("2017-09-05T22:31:00", "%Y-%m-%dT%H:%M:%S")
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

def test():
    ex = ExchangeWrapperForBacktesting()
    for i in range(1000):
        # for marketName in os.listdir(config.backtestingDataDirectory):
        #     if not marketName.endswith(".json"):
        #         continue
        # print(ex.getCurrentTick("BTC-1ST"))
        print(ex.getCurrentTick("BTC-LTC"))
        ex.wait()

if __name__ == "__main__":
    test()
