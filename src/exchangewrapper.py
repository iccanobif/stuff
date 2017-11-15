import json
import config
from logger import Logger
from tick import Tick



class ExchangeWrapper:
    # Oggetto (singleton?) che wrappa le chiamate al sito di exchange
    # - vendere
    # - comprare
    # - get del tick attuale
    # può anche essere mock, e in realtà leggere direttamente da un json coi dati storici
    
    def __init__(self):
        self.currentTickIndex = 0
        self.ticks = dict()
        self.currentBalance = 100
        self.currentCurrency = "BTC"
        log = Logger()
        log.log("Loading backtest data file...")
        completeTickerData = json.load(open("../BTC-LTC.json", "r"))
        # for market in completeTickerData:
        #     marketName = market["market"]
        #     log.log("Doing %s ticks..." % marketName)
        #     for tick in market["ticks"]:
        #         if marketName not in self.ticks: self.ticks[marketName] = []
        #         self.ticks[marketName].append(Tick(marketName, tick))
        self.ticks["BTC-LTC"] = []
        for tick in completeTickerData:
            self.ticks["BTC-LTC"].append(Tick("BTC-LTC", tick))

    #TODO instead of keeping a huge ticks dictionary in memory, read the text file gradually
    #and use yeld to return each tick
    def getCurrentTick(self, market):
        output = self.ticks[market][self.currentTickIndex]
        self.currentTickIndex += 1
        return output

    def gotMoreTicks(self, market):
        # -1 because i want to keep the last tick "unpopped", so that the last sell() works
        # return self.currentTickIndex < 2000
        return self.currentTickIndex < len(self.ticks[market]) - 1 

    def buy(self, market):
        if self.currentCurrency != "BTC":
            raise Exception("Already bought!")
        log = Logger()
        log.log("BUY!")
        price = self.ticks[market][self.currentTickIndex].close
        self.currentBalance = self.currentBalance / price * config.bittrexCommission
        self.currentCurrency = "LTC"

    def sell(self, market):
        if self.currentCurrency == "BTC":
            raise Exception("Already sold!")
        log = Logger()
        log.log("SELL!")
        price = self.ticks[market][self.currentTickIndex].close
        self.currentBalance = self.currentBalance * price * config.bittrexCommission
        self.currentCurrency = "BTC"

    def getCurrentBalance(self):
        return self.currentBalance

    def getCurrentCurrency(self):
        return self.currentCurrency
