from collections import deque

from logger import Logger
import config

import plotly
import plotly.graph_objs as go
import numpy as np
import exchangewrapper

class MarketStatusRepository:
    # Oggetto MarketStatusRepository, in cui posso
    # - aggiungere un nuovo tick (ogni volta che aggiungo, ricalcola subito tutte le moving average eccetera)
    # - recuperare lo stato di un mercato (classe MarketStatus)
    #     - valore attuale
    #     - andamento (in crescita? in discesa?) fondamentalmente qui è il valore delle moving averages
    # keep the ticks in a circular buffer
    # also keep another circular buffer holding the EMA for every corresponding value in the ticks buffer

    # TODO: Might be a good idea to make a CircularBuffer class to avoid having to deal with its complexities here.
    #       calls to getLastNTicks are currently the performance bottleneck in backtesting
    
    def __init__(self, marketName):
        self.marketName = marketName
        self.todaysTicks = deque([], config.ticksBufferSize) # 24 hours' worth of 1-minute candles. To be appended new data to on the right side.
        self.todaysEMAfast = deque([], config.ticksBufferSize) # Simple Moving Average (fast ticks)
        self.todaysEMAslow = deque([], config.ticksBufferSize) # Simple Moving Average (slow ticks)
        self.currentTickIndex = -1
        self.totalProcessedTicks = -1
    
    def addTick(self, tick):
        self.totalProcessedTicks += 1
        self.todaysTicks.append(tick)
        self.computeEMA()

    def updateWithCandleList(self, candles):
        # TODO: to be rewritten so that it uses the deques

        self.todaysTicks = candles[-config.ticksBufferSize:]
        if len(candles) < config.ticksBufferSize:
            # Add padding if the candles aren't enough to fill the entire buffer
            self.todaysTicks += [None for x in range(config.ticksBufferSize - len(candles))]
        self.currentTickIndex = -1
        for i in range(min(config.ticksBufferSize, len(candles))):
            self.currentTickIndex += 1
            self.computeEMA()

    def computeEMA(self):
        # EMA: alpha*Price + (1-alpha)*PreviousEMA

        # TODO: Handle the first tick! As it is now, it will probably crash.

        for EMAList, smoothingFactor in [(self.todaysEMAfast, config.fastEMASmoothingFactor), (self.todaysEMAslow, config.slowEMASmoothingFactor)]:
            EMAList.append(smoothingFactor * self.todaysTicks[-1].price  \
                           + (1 - smoothingFactor) * EMAList[-1])

    def getTick(self, index = 0):
        if config.ticksBufferSize - index < 0:
            raise Exception("too old, mang")
        return self.todaysTicks[-1]
        
    def getEMA(self, type):
        if type == "fast":
            return self.todaysEMAfast[-1]
        if type == "slow":
            return self.todaysEMAslow[-1]
        raise Exception("meh")
        
    def printMarketStatus(self):
        Logger.log("Current tick: " + str(self.todaysTicks[-1]))
        Logger.log("    Current EMAfast: " + str(self.todaysEMAfast[-1]))
        Logger.log("    Current EMAslow: " + str(self.todaysEMAslow[-1]))

    def drawPlot(self):

        x = list(range(0, len(self.todaysTicks)))

        coeff = max([x.close for x in self.todaysTicks]) / max([x.volume for x in self.todaysTicks])

        pricedata = [go.Scatter(x = x, y = [x.close for x in self.todaysTicks], name="prices"), \
                    go.Scatter(x = x, y = [x.volume * coeff for x in self.todaysTicks], name="volume"), \
                    go.Scatter(x = x, y = self.todaysEMAfast, name="fastEMA"), \
                    go.Scatter(x = x, y = self.todaysEMAslow, name="slowEMA"), \
                    go.Scatter(x = x, y = [(self.todaysEMAfast[i] - self.todaysEMAslow[i]) * self.todaysTicks[i].volume * 0.0000001 \
                                            for i in range(config.ticksBufferSize)], name="kek")]

        plotly.offline.plot(pricedata, filename="../output_files/graph_%s.html" % self.marketName)

def test():
    ms = MarketStatusRepository("BTC-XVG")
    ex = exchangewrapper.ExchangeWrapper()
    print("Getting candles...")
    candles = ex.GetAllCandles("BTC-XVG")
    print("Computing stuff...")
    ms.updateWithCandleList(candles)
    print("Generating graph...")
    ms.drawPlot()
    print("Done.")

if __name__ == "__main__":
    test()