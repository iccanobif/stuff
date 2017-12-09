# import datetime, time, json, statistics
# import config, ExchangeWrapper
from analyst import Analyst
from exchangewrapper import ExchangeWrapperForBacktesting, ExchangeWrapper
from logger import Logger
from marketstatusrepository import MarketStatusRepository
import config

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

def main():
    Logger.open()
    log = Logger()
    exchange = ExchangeWrapper()
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
        
        # analyst.doTrading([repo])
        exchange.wait()
    Logger.close()

if __name__ == "__main__":
    main()
