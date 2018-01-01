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
        
        # find the market where (fast EMA - slow EMA) is highest
        fastestMarket = self.findFastestGrowingMarket(marketStatusRepoList)

        # Keep track in this class how much value I put on a certain market, to calculate 
        # the gains and take decisions about doing a stop loss or not

        # if config.verbose:
        #     repo.printMarketStatus()
        #     Logger.log("self.currentCurrency %s; self.currentPeak %f; currTick.price %f" \
        #              % (self.currentCurrency, self.currentPeak, currTick.price))

        # Cool algo idea:
        # define the mooning index for a candle as:
        # Original idea (full of problems): a*volume*(close-open) / b*(high-low-(close-open))

        # moon_index = sign*a*volume*(max(close, open)/min(close, open)) - b*percentage_outside_candle
        #     where percentage_outside_candle = (high-close + open-low)/(high-low) 
        #           sign = 1 if close >= open, -1 if close < open
        #           a and b are parameters to be configured (and validated with backtesting)
 
        action = "NONE"

        log.structuredLog({"action": action, "merda": "cacca", "faststmarket": fastestMarket.marketName}, True)
