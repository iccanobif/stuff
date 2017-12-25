import traceback, sys, time, logging
import requests

from telegram.ext import Updater, CommandHandler

from exchangewrapper import ExchangeWrapper
from logger import Logger
import config
import utilities

def main():
    try:
        Logger.open()
        log = Logger()
        utilities.initializeTelegramBot()

        exchange = ExchangeWrapper()

        Logger.sendTelegramMessage("Bot started...")
        while True:
            Logger.sendTelegramMessage(utilities.getCurrentHoldings())
            time.sleep(60*10) # 10 minutes
        Logger.close()
    except:
        log.log("eccezione gestita...")
        exceptionInfo = traceback.format_exc()
        print(exceptionInfo)
        log.log(exceptionInfo)
        Logger.sendTelegramMessage(exceptionInfo)
        
        if utilities.isTelegramUpdaterActive():
            utilities.stopTelegramUpdater()
        Logger.close()

if __name__ == "__main__":
    main()
