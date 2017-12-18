import config
from logger import Logger

class Analyst:
    def __init__(self, exchange):
        self.exchange = exchange
        self.currentCurrency = config.baseCurrency

    def findFastestGrowingMarket(self, marketStatusRepoList):
        maxValue = -1
        maxRepo = None
        for repo in marketStatusRepoList:
            if repo.getTick().price > maxValue:
                maxRepo = repo
        return maxRepo

    def doTrading(self, marketStatusRepoList):
        """here do stuff on the exchange depending on the info I get from the marketStatus"""
        log = Logger()
        
        # find the market where (fast EMA - slow EMA) is highest
        fastestMarket = self.findFastestGrowingMarket(marketStatusRepoList)

        # Keep track in this class how much value I put on a certain market, to calculate 
        # the gains and take decisions about doing a stop loss or not

        # if config.verbose:
        #     repo.printMarketStatus()
        #     log.log("self.currentCurrency %s; self.currentPeak %f; currTick.price %f" \
        #              % (self.currentCurrency, self.currentPeak, currTick.price))
        action = "NONE"

        log.structuredLog({"action": action, "merda": "cacca", "faststmarket": fastestMarket.marketName})
