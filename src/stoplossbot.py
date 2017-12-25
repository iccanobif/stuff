import traceback, time
import config, utilities
from logger import Logger
from exchangewrapper import ExchangeWrapper

def main():
    try:
        Logger.open()
        log = Logger()
        utilities.initializeTelegramBot()
        exchange = ExchangeWrapper()

        Logger.sendTelegramMessage("Bot started...")

        # maxValues keeps the max value (in BTC) for each currency held
        maxValues = dict()

        # Initialize maxValues with the current values
        for currency in [b for b in exchange.getBalances() if b != "BTC"]:
            maxValues[currency] = exchange.getCurrentTick("BTC-" + currency).price

        while True:
            # time.sleep(60*10) # 10 minutes
            time.sleep(1)
            print("New iteration...")
            currentValues = dict([(b, exchange.getCurrentTick("BTC-" + b).price) \
                                  for b \
                                  in exchange.getBalances() \
                                  if b != "BTC"])

            currentlyHeldCoins = [b for b in currentValues]

            # If one or more coins were sold directly from coinbase (or some other bot), delete their
            # values from maxValues

            for coin in maxValues.keys():
                if coin not in currentlyHeldCoins:
                    del maxValues[coin]

            # Update the values

            for currency in currentlyHeldCoins:
                if currency not in maxValues:
                    maxValues[currency] = currentValues[currency]
                else:
                    if maxValues[currency] < currentValues[currency]:
                        maxValues[currency] = currentValues[currency]

            # Check if some coin is below the stop-loss threshold
            for currency in currentlyHeldCoins:
                if currentValues[currency] < maxValues[currency] * config.stopLossPercentage:
                    print(currency, "STOOOOP!")


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
