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
    logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)
    telegramUpdater = Updater(token='500739610:AAGhPu4Z5BNefe3_86NWqNutOQAV_Ywuzm0')
    dispatcher = telegramUpdater.dispatcher
    chatid = config.telegramChatId
    dispatcher.add_handler(CommandHandler('summary', handleSummaryRequest))
    telegramUpdater.start_polling()
    # updater.idle()
 
def main_backtesting():
    Logger.open()
    log = Logger()
    exchange = ExchangeWrapper()
    btc_eth = MarketStatusRepository("BTC-ETH")
    btc_ltc = MarketStatusRepository("BTC-LTC")
    repo = MarketStatusRepository("BTC-LTC")
    analyst = Analyst(exchange)
    initialBalance = exchange.getCurrentBalance()
    log.log("Initial balance: %f %s" % (initialBalance, config.baseCurrency))
    i = 0
    currentTick = None
    while True:
        currentTick = exchange.getCurrentTick("BTC-LTC")
        if currentTick is None: # Backtesting data is over
            break
        repo.addTick(currentTick)
        analyst.doTrading([repo])
        if i % 1000 == 0:
            print("Done %d..." % i)
        i += 1
        exchange.wait()
    if exchange.getCurrentCurrency() != "BTC":
        log.log("Ran out of test data, selling back to BTC")
        exchange.sell("BTC_" + exchange.getCurrentCurrency(), \
                      exchange.getCurrentBalance(),
                      currentTick.close)
    log.log("Final balance: %f BTC" % exchange.getCurrentBalance())
    Logger.close()
    print("DONE")

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
        # exchange = ExchangeWrapper()
        exchange = ExchangeWrapperForBacktesting()

        Logger.sendTelegramMessage("Bot started...")
        repo_btc_ltc = MarketStatusRepository("BTC-LTC")
        repo_btc_mona = MarketStatusRepository("BTC-MONA")
        analyst = Analyst(exchange)
        while True:
            # currentTick = exchange.getCurrentTick("BTC-LTC")
            print("Nuovo ciclo...")
            currentTick = exchange.getCurrentTick("BTC-LTC")
            repo_btc_ltc.addTick(currentTick)
            print(currentTick, repo_btc_ltc.getEMA("fast"))

            currentTick = exchange.getCurrentTick("BTC-MONA")
            repo_btc_mona.addTick(currentTick)
            print(currentTick, repo_btc_mona.getEMA("fast"))
            
            analyst.doTrading([repo_btc_ltc, repo_btc_mona])
            exchange.wait()
        Logger.close()
    except:
        exceptionInfo = traceback.format_exc()
        print(exceptionInfo)
        log.log(exceptionInfo)
        Logger.sendTelegramMessage(exceptionInfo)
        Logger.close()

def main():
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
        telegramUpdater.stop() # If i don't do this, telegram's thread won't stop and the python interpreter will hang...
        Logger.close()

if __name__ == "__main__":
    main()
