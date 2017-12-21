import traceback, sys, time, logging
import requests

from analyst import Analyst
from exchangewrapper import ExchangeWrapperForBacktesting, ExchangeWrapper
from logger import Logger
from marketstatusrepository import MarketStatusRepository
import config
from telegram.ext import Updater, CommandHandler

telegramUpdater = None

def getBTCPriceInEuro():
    try:
        response = requests.get("https://api.coinmarketcap.com/v1/ticker/bitcoin/?convert=EUR")
        return float(response.json()[0]["price_eur"])
    except:
        # I don't care if CoinMarketCap is down or something, this function should never throw exceptions
        return 0 

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

def main():
    try:
        Logger.open()
        log = Logger()
        Logger.sendTelegramMessage("Bot started...")
        exchange = ExchangeWrapper()
        analyst = Analyst(exchange)
        marketRepos = dict() # TODO: Markets can appear and disappear, with time...
        for marketName in [x["MarketName"] for x in exchange.getMarketSummary() if x["BaseVolume"] > 3000]:
            marketRepos[marketName] = MarketStatusRepository(marketName) 
        while True:
            for market in marketRepos.keys():
                print("Updating for", market)
                marketRepos[market].updateWithCandleList(exchange.GetAllCandles(market))
            analyst.doTrading(marketRepos.values())
            quit()
            exchange.wait()
        Logger.close()
    except:
        exceptionInfo = traceback.format_exc()
        print(exceptionInfo)
        log.log(exceptionInfo)
        Logger.sendTelegramMessage(exceptionInfo)
        Logger.close()

def mainTelegramUpdatesOnly():
    try:
        Logger.open()
        log = Logger()
        initializeTelegramBot()

        exchange = ExchangeWrapper()

        Logger.sendTelegramMessage("Bot started...")
        while True:
            Logger.sendTelegramMessage(getCurrentHoldings())
            time.sleep(60*10) # 10 minutes
        Logger.close()
    except:
        print("eccezione gestita...")
        exceptionInfo = traceback.format_exc()
        print(exceptionInfo)
        log.log(exceptionInfo)
        Logger.sendTelegramMessage(exceptionInfo)
        if telegramUpdater is not None:
            telegramUpdater.stop() # If i don't do this, telegram's thread won't stop and the python interpreter will hang...
        Logger.close()

if __name__ == "__main__":
    main()
