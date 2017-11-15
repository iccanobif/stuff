# import datetime, time, json, statistics
# import config, ExchangeWrapper
from logger import Logger
from exchangewrapper import ExchangeWrapper
from marketstatusrepository import MarketStatusRepository
from analyst import Analyst

def main():
    Logger.open()
    log = Logger()
    exchange = ExchangeWrapper()
    repo = MarketStatusRepository()
    analyst = Analyst(exchange)
    initialBalance = exchange.getCurrentBalance()
    log.log("Initial balance: %f BTC" % initialBalance)
    i = 0
    while exchange.gotMoreTicks("BTC-LTC"):
        repo.addTick(exchange.getCurrentTick("BTC-LTC"))
        analyst.doTrading(repo)
        if i % 1000 == 0:
            print("Done %d out of %d (%d%%)..." % (i, len(exchange.ticks["BTC-LTC"]), round(float(i) / len(exchange.ticks["BTC-LTC"]) * 100, 0)))
        i += 1
    if exchange.getCurrentCurrency() != "BTC":
        log.log("Ran out of test data, selling back to BTC")
        exchange.sell("BTC-LTC")
    log.log("Final balance: %f BTC" % exchange.getCurrentBalance())
    Logger.close()
    print("DONE")

if __name__ == "__main__":
    main()

