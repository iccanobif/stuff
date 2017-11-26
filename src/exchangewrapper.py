import datetime, calendar
import json
import os
import time

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
            self.currentTime = timestamp
            while self.currTick is None or self.currTick.getTimestamp() < timestamp:
                line = self.f.readline()
                self.currTick = Candle(self.marketName, json.loads(line))
            return self.currTick # Returns the current tick (it's the one I was asked for)

    def __init__(self):
        self.currentTime = time.strptime("2017-09-05T22:31:00", "%Y-%m-%dT%H:%M:%S")
        self.iterators = dict()
        self.currentTicks = dict() # key: market
        for marketName in os.listdir(config.backtestingDataDirectory):
            if not marketName.endswith(".json"):
                continue
            marketName = marketName.replace(".json", "")
            self.iterators[marketName] = self.TickIterator(marketName)

    def getCurrentTick(self, marketName):
        # Returns a Tick object
        print("current time", time.strftime("[%Y-%m-%d %H:%M:%S]",self.currentTime))
        return self.iterators[marketName].get(self.currentTime)


    def wait(self):
        # Simulate the passage of time when backtesting
        # Adds 60 seconds
        self.currentTime = time.gmtime(calendar.timegm(self.currentTime) + 60)

    def getMarketList(self):
        pass

    def buy(self):
        pass

    def sell(self):
        pass

    def getCurrentBalance(self):
        pass

    def getCurrentCurrency(self):
        pass

def test():
    ex = ExchangeWrapperForBacktesting()
    for i in range(1000):
        # for marketName in os.listdir(config.backtestingDataDirectory):
        #     if not marketName.endswith(".json"):
        #         continue
        print(ex.getCurrentTick("BTC-1ST"))
        ex.wait()

if __name__ == "__main__":
    test()
