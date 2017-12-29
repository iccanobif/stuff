import traceback, sys, time, logging, json
import requests

from logger import Logger
import config
from telegram.ext import Updater, CommandHandler

telegramUpdater = None

def initializeTelegramBot(handlerList):
    # handlerList has to be a list of tuples with the name of the command to be typed 
    # on the chat and the respective function to call (eg. [("summary", someHandler), ("buy", someOtherHandler)])
    global telegramUpdater

    if not config.enableTelegramIntegration:
        return

    logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)
    telegramUpdater = Updater(token='500739610:AAGhPu4Z5BNefe3_86NWqNutOQAV_Ywuzm0')
    dispatcher = telegramUpdater.dispatcher
    chatid = config.telegramChatId
    for command in handlerList:
        dispatcher.add_handler(CommandHandler(command[0], command[1]))
    telegramUpdater.start_polling()
    # updater.idle()
 
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

