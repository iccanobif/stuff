from logger import Logger
import config

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
        self.todaysTicks = [None for x in range(config.ticksBufferSize)] # 24 hours' worth of 1-minute candles
        # It might make sense to make a function that returns the last N days' EMA instead of computing it every time, 
        self.todaysEMAfast = [None for x in range(config.ticksBufferSize)] # Simple Moving Average (fast ticks)
        self.todaysEMAslow = [None for x in range(config.ticksBufferSize)] # Simple Moving Average (slow ticks)
        self.currentTickIndex = -1
        self.totalProcessedTicks = -1
        
    def getLastNTicks(self, tickCount):
        # Only used internally in this class
        if self.currentTickIndex >= tickCount:
            return self.todaysTicks[self.currentTickIndex - tickCount:self.currentTickIndex + 1]
        else:
            # Gotta ignore the None values in the list (this is only a problem when the bot just started and the buffer isn't full yet)
            if tickCount <= self.totalProcessedTicks :
                return self.todaysTicks[self.currentTickIndex - tickCount:] \
                        + self.todaysTicks[0:self.currentTickIndex + 1]
            else:
                return self.todaysTicks[0:self.currentTickIndex + 1]
    
    def addTick(self, tick):
        self.totalProcessedTicks += 1
        self.currentTickIndex += 1
        if self.currentTickIndex == config.ticksBufferSize:
            self.currentTickIndex = 0
        self.todaysTicks[self.currentTickIndex] = tick

        self.computeEMA()

    def updateWithCandleList(self, candles):
        self.todaysTicks = candles[-config.ticksBufferSize:]
        self.currentTickIndex = 0
        for i in range(config.ticksBufferSize):
            self.computeEMA()
            self.currentTickIndex += 1

    def computeEMA(self):

        if len(self.getLastNTicks(config.fastEMAWindow)) < config.fastEMAWindow:
        # Just started the bot, not enough candles for computing the EMA, so fallback to EMA
            if config.accurateMean:
                self.todaysEMAfast[self.currentTickIndex] = statistics.mean([x.price for x in self.getLastNTicks(config.fastEMAWindow) if not x is None])
            else:
                self.todaysEMAfast[self.currentTickIndex] = sum([x.price for x in self.getLastNTicks(config.fastEMAWindow) if not x is None])/len(self.getLastNTicks(config.fastEMAWindow))
        else:
            # Multiplier: (2 / (Time periods + 1) ) = (2 / (10 + 1) ) = 0.1818 (18.18%)
            # EMA: {Close - EMA(previous day)} x multiplier + EMA(previous day). 
            self.todaysEMAfast[self.currentTickIndex] = (self.todaysTicks[self.currentTickIndex].price - self.todaysEMAfast[self.currentTickIndex - 1]) \
                                                        * config.fastEMAMultiplier \
                                                        + self.todaysEMAfast[self.currentTickIndex - 1]

        if len(self.getLastNTicks(config.slowEMAWindow)) < config.slowEMAWindow:
        # Just started the bot, not enough candles for computing the EMA, so fallback to EMA
            if config.accurateMean:
                self.todaysEMAslow[self.currentTickIndex] = statistics.mean([x.price for x in self.getLastNTicks(config.slowEMAWindow)])
            else:
                self.todaysEMAslow[self.currentTickIndex] = sum([x.price for x in self.getLastNTicks(config.slowEMAWindow)])/len(self.getLastNTicks(config.slowEMAWindow))
            
        else:
            # Multiplier: (2 / (Time periods + 1) ) = (2 / (10 + 1) ) = 0.1818 (18.18%)
            # EMA: {Close - EMA(previous day)} x multiplier + EMA(previous day). 
            self.todaysEMAslow[self.currentTickIndex] = (self.todaysTicks[self.currentTickIndex].price - self.todaysEMAslow[self.currentTickIndex - 1]) \
                                                        * config.slowEMAMultiplier \
                                                        + self.todaysEMAslow[self.currentTickIndex - 1]
        
    def getTick(self, index = 0):
        if config.ticksBufferSize - index < 0:
            raise Exception("too old, mang")
        return self.todaysTicks[self.currentTickIndex - index]
        
    def getEMA(self, type):
        if type == "fast":
            return self.todaysEMAfast[self.currentTickIndex]
        if type == "slow":
            return self.todaysEMAslow[self.currentTickIndex]
        raise Exception("meh")
        
    def printMarketStatus(self):
        log = Logger()
        log.log("Current tick: " + str(self.todaysTicks[self.currentTickIndex]))
        log.log("    Current EMAfast: " + str(self.todaysEMAfast[self.currentTickIndex]))
        log.log("    Current EMAslow: " + str(self.todaysEMAslow[self.currentTickIndex]))

import plotly
import plotly.graph_objs as go
import numpy as np
import exchangewrapper

def test():
    ms = MarketStatusRepository("BTC-MONA")
    ex = exchangewrapper.ExchangeWrapper()
    print("Getting candles...")
    candles = ex.GetAllCandles("BTC-MONA")
    print("Computing stuff...")
    ms.updateWithCandleList(candles)
    print("Generating graph...")
    x = list(range(0, len(ms.todaysTicks)))

    coeff = max([x.close for x in ms.todaysTicks]) / max([x.volume for x in ms.todaysTicks])

    pricedata = [go.Scatter(x = x, y = [x.close for x in ms.todaysTicks], name="prices"), \
                 go.Scatter(x = x, y = [x.volume * coeff for x in ms.todaysTicks], name="volume"), \
                 go.Scatter(x = x, y = ms.todaysEMAfast, name="fastEMA"), \
                 go.Scatter(x = x, y = ms.todaysEMAslow, name="slowEMA"), \
                 go.Scatter(x = x, y = [(ms.todaysEMAfast[i] - ms.todaysEMAslow[i]) * ms.todaysTicks[i].volume * 0.0001 \
                                         for i in range(config.ticksBufferSize)], name="kek")]

    plotly.offline.plot(pricedata, filename='../output_files/graph.html')

    print("Done.")

test()