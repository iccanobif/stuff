import config
from logger import Logger

class Analyst:
    # - ha un metodo che riceve in input un MarketStatus, prende una decisione su cosa fare e la fa fare all'exchangeWrapper:
    #     - vendere
    #     - comprare
    #     - NOP
    # - posso averne anche più di uno, ognuno con una strategia diversa
    # - ogni analyst ha una quantità propria di coin su cui giocare
    def __init__(self, exchange):
        self.exchange = exchange
        self.currentPeak = 0 # Used for stop-loss. 0 when I'm merely holding BTC
        self.currentCurrency = "BTC"
        self.currentBalance = exchange.getCurrentBalance()

    def doTrading(self, repo):
        """here do stuff on the exchange depending on the info I get from the marketStatus"""
        log = Logger()
        currTick = repo.getTick()
        if self.currentCurrency == "BTC":
            self.currentPeak = 0
        else:
            self.currentPeak = max(self.currentPeak, currTick.close)
            
        if config.verbose:
            repo.printMarketStatus()
            log.log("self.currentCurrency %s; self.currentPeak %f; currTick.close %f" \
                     % (self.currentCurrency, self.currentPeak, currTick.close))
        action = "NONE"

        if self.currentCurrency == "BTC":
            # Look for buying opportunities
            if repo.getEMA("fast") > repo.getEMA("slow"):
                self.exchange.buy("BTC-LTC", self.exchange.getCurrentBalance(), currTick.close)
                self.currentCurrency = "LTC"
                self.currentBalance = self.exchange.getCurrentBalance()
                action = "BUY"
        if self.currentCurrency != "BTC":
            if repo.getEMA("fast") < repo.getEMA("slow"):
                self.exchange.sell("BTC-LTC", self.exchange.getCurrentBalance(), currTick.close)
                self.currentCurrency = "BTC"
                self.currentBalance = self.exchange.getCurrentBalance()
                action = "SELL"
        log.structuredLog(currTick.close, currTick.baseVolume, repo.getEMA("fast"), repo.getEMA("slow"), action, self.currentBalance)
