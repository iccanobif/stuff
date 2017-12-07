# import datetime, time, json, statistics
# import config, ExchangeWrapper
from analyst import Analyst
from exchangewrapper import ExchangeWrapperForBacktesting
from logger import Logger
from marketstatusrepository import MarketStatusRepository
import config

def main():
    Logger.open()
    log = Logger()
    exchange = ExchangeWrapperForBacktesting()
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

if __name__ == "__main__":
    main()
