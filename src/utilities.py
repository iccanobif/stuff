import traceback, sys, time, logging, json
import requests

from analyst import Analyst
from exchangewrapper import ExchangeWrapper
from logger import Logger
from marketstatusrepository import MarketStatusRepository
import config
from telegram.ext import Updater, CommandHandler

telegramUpdater = None

def handleSummaryRequest(bot, update):
    bot.send_message(chat_id=update.message.chat_id, text="Gathering data...")
    bot.send_message(chat_id=update.message.chat_id, text=getCurrentHoldings())

def initializeTelegramBot():
    global telegramUpdater

    if not config.enableTelegramIntegration:
        return

    logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)
    telegramUpdater = Updater(token='500739610:AAGhPu4Z5BNefe3_86NWqNutOQAV_Ywuzm0')
    dispatcher = telegramUpdater.dispatcher
    chatid = config.telegramChatId
    dispatcher.add_handler(CommandHandler('summary', handleSummaryRequest))
    telegramUpdater.start_polling()
    # updater.idle()
 
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
    output += "\nBTC total: %f (%f EURO)" % (totalBtcValue, totalBtcValue * getBTCPriceInEuro())
    
    return output

def isTelegramUpdaterActive():
    global telegramUpdater
    return telegramUpdater is not None

def stopTelegramUpdater():
    # If this function isn't called when stopping the application, telegram's thread won't stop and the python interpreter will hang...
    global telegramUpdater
    telegramUpdater.stop() 

def getBTCPriceInEuro():
    try:
        response = requests.get("https://api.coinmarketcap.com/v1/ticker/bitcoin/?convert=EUR")
        return float(response.json()[0]["price_eur"])
    except:
        # I don't care if CoinMarketCap is down or something, this function should never throw exceptions
        return 0 

def prettyPrintJSONVertical(j):
    # for i in j:
    #     print("   ", i, j[i])
    return json.dumps(j, sort_keys=True, indent=4)

def prettyPrintJSONHorizontal(j):
    return json.dumps(j, sort_keys=True)

if __name__ == "__main__":
    print(getCurrentHoldings())
