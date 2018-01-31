import config
from logger import Logger

class Analyst:
    def __init__(self, exchange):
        self.exchange = exchange
        self.currentCurrency = config.baseCurrency

    def findFastestGrowingMarket(self, marketStatusRepoList):
        # the "fastest growing market" is merely the one where (fast EMA - slow EMA) is highest
        shit = [(m, m.getEMA("fast") - m.getEMA("slow")) for m in marketStatusRepoList]
        shit = sorted(shit, key=lambda x: -x[1])
        return shit[0][0]

    def doTrading(self, marketStatusRepoList):
        """here do stuff on the exchange depending on the info I get from the marketStatus"""
        
        fastestMarket = self.findFastestGrowingMarket(marketStatusRepoList)

        # Keep track in this class how much value I put on a certain market, to calculate 
        # the gains and take decisions about doing a stop loss or not

        # Cool algo idea:
        # define the mooning index for a candle as:
        # Original idea (full of problems): a*volume*(close-open) / b*(high-low-(close-open))

        # moon_index = sign*a*volume*(max(close, open)/min(close, open)) - b*percentage_outside_candle
        #     where percentage_outside_candle = (high-close + open-low)/(high-low) 
        #           sign = 1 if close >= open, -1 if close < open
        #           a and b are parameters to be configured (and validated with backtesting)
 
        action = "NONE"

        Logger.structuredLog({"action": action, "merda": "cacca", "faststmarket": fastestMarket.marketName}, True)
