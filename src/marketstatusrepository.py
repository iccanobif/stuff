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
        self.computeEMA(tick)

    def updateWithCandleList(self, candles):
        
        if len(self.todaysTicks) > 0:
            if candles[-1].timestamp <= self.todaysTicks[-1].timestamp:
                # There are no new candles to add
                return
            # Consider only the candles that are not already in the buffer
            candles = filter(lambda x: x.timestamp > self.todaysTicks[-1].timestamp, candles)
        
        self.todaysTicks.extend(candles)
        
        self.computeEMAFull() # TODO: figure out a decent way to avoid recalculating the EMA for the entire buffer everytime

    def computeEMA(self, tick):
        for EMAList, smoothingFactor in [(self.todaysEMAfast, config.fastEMASmoothingFactor), (self.todaysEMAslow, config.slowEMASmoothingFactor)]:
            if len(EMAList) == 0:
                EMAList.append(self.todaysTicks[-1].price)
            else:
                EMAList.append(smoothingFactor * self.todaysTicks[-1].price  \
                               + (1 - smoothingFactor) * EMAList[-1])

    def computeEMAFull(self):
        # EMA: alpha*Price + (1-alpha)*PreviousEMA
        self.todaysEMAfast.clear()
        self.todaysEMAslow.clear()

        for tick in self.todaysTicks:
            self.computeEMA(tick)

    def getTick(self, index = 0):
        if config.ticksBufferSize - index < 0:
            raise Exception("too old, mang")
        return self.todaysTicks[index-1]
        
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
                    go.Scatter(x = x, y = list(self.todaysEMAfast), name="fastEMA"),  \
                    go.Scatter(x = x, y = list(self.todaysEMAslow), name="slowEMA"), \
                    # go.Scatter(x = x, y = [(self.todaysEMAfast[i] - self.todaysEMAslow[i]) * self.todaysTicks[i].volume * 0.0000001 \
                    #                         for i in range(config.ticksBufferSize)], name="kek") \
                                            ]

        plotly.offline.plot(pricedata, filename="../output_files/graph_%s.html" % self.marketName)

def test():
    ms = MarketStatusRepository("BTC-XVG")
    ex = exchangewrapper.ExchangeWrapper()
    Logger.open()
    Logger.log("Getting candles...")
    candles = ex.GetAllCandles("BTC-XVG") # TODO: Fill the missing candles
    Logger.log("Computing stuff...")
    ms.updateWithCandleList(candles)
    Logger.log("Generating graph...")
    ms.drawPlot()
    Logger.log("Done.")
    Logger.close()

if __name__ == "__main__":
    test()