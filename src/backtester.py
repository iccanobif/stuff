import traceback, sys, time, logging
import requests

from analyst import Analyst
from exchangewrapper import ExchangeWrapperForBacktesting, ExchangeWrapper
from logger import Logger
from marketstatusrepository import MarketStatusRepository
import config
from telegram.ext import Updater, CommandHandler

def main():
    try:
        Logger.open()
        Logger.sendTelegramMessage("Bot started...")
        exchange = ExchangeWrapperForBacktesting()
        analyst = Analyst(exchange)
        marketRepos = dict() # TODO: Markets can appear and disappear, with time...
        for marketName in [x["MarketName"] for x in exchange.getMarketSummary() if x["BaseVolume"] > 3000]:
            marketRepos[marketName] = MarketStatusRepository(marketName) 
        Logger.log("Markets: " + " ".join(marketRepos.keys()))
        while True:
            for market in marketRepos.keys():
                # TODO: the iterations of this loop don't depend on each other, so we can parallelize
                marketRepos[market].addTick(exchange.getCurrentCandle(market))
            analyst.doTrading(marketRepos.values())
            exchange.wait()
        Logger.close()
    except:
        exceptionInfo = traceback.format_exc()
        Logger.log(exceptionInfo)
        Logger.close()

if __name__ == "__main__":
    main()
