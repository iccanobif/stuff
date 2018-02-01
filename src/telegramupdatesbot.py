import traceback, sys, time, logging
import requests

from telegram.ext import Updater, CommandHandler

from exchangewrapper import ExchangeWrapper
from logger import Logger
import config
import utilities

def getCurrentHoldings():
    # Returns a formatted string
    exchange = ExchangeWrapper()
    balances = exchange.getBalances()
    totalBtcValue = 0
    output = ""
    for currency in balances.keys():
        btcValue = None
        if currency == "BTC":
            btcValue = balances[currency]
        else:
            btcValue = exchange.getCurrentTick("BTC-" + currency).price * balances[currency]
        totalBtcValue += btcValue
        output += "%f %s (%f BTC)\n" % (balances[currency], currency, btcValue)
    output += "\nBTC total: %f (%f EURO)" % (totalBtcValue, totalBtcValue * utilities.getBTCPriceInEuro())
    
    return output

def handleSummaryRequest(bot, update):
    bot.send_message(chat_id=update.message.chat_id, text="Gathering data...")
    bot.send_message(chat_id=update.message.chat_id, text=getCurrentHoldings())

def main():
    try:
        Logger.open()
        utilities.initializeTelegramBot([("summary", handleSummaryRequest)])

        exchange = ExchangeWrapper()

        Logger.sendTelegramMessage("Bot started...")
        while True:
            Logger.sendTelegramMessage(getCurrentHoldings())
            time.sleep(60*10) # 10 minutes
        Logger.close()
    except:
        Logger.log("eccezione gestita...")
        exceptionInfo = traceback.format_exc()
        Logger.log(exceptionInfo)
        Logger.sendTelegramMessage(exceptionInfo)
        
        if utilities.isTelegramUpdaterActive():
            utilities.stopTelegramUpdater()
        Logger.close()

if __name__ == "__main__":
    main()
