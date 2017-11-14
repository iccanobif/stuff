import datetime, time, json, statistics

# CONFIGURATION:
bittrexCommission = 0.9975 # 0.25% commissions
stopLossPercentage = 0.99
ticksBufferSize = 24*60*7    # How many candles are kept in memory
enableStdoutLog = False
verbose = True
accurateMean = False # statistics.mean might be slightly more precise, but it's probably not worth it
fastEMAWindow = 100
slowEMAWindow = 5000
fastEMAMultiplier = (2 / (fastEMAWindow + 1.0) )
slowEMAMultiplier = (2 / (slowEMAWindow + 1.0) )

class Logger:

    f = None
    structuredLogFile = None
    
    def log(self, message):
        string = time.strftime("[%Y-%m-%d %H:%M:%S]", time.localtime(time.time())) + " " + message
        Logger.f.write(string + "\n")
        if enableStdoutLog:
            print(string)
        
    def structuredLog(self, price, volume, fastEMAValue, slowEMAValue, action, currentBalance):
        Logger.structuredLogFile.write("{\"price\": " + str(price))
        Logger.structuredLogFile.write(", \"volume\": " + str(volume))
        Logger.structuredLogFile.write(", \"fastEMAValue\": " + str(fastEMAValue))
        Logger.structuredLogFile.write(", \"slowEMAValue\": " + str(slowEMAValue))
        Logger.structuredLogFile.write(", \"currentBalance\": " + str(currentBalance))
        Logger.structuredLogFile.write(", \"action\": \"%s\"},\n" % action)
        
    def open():
        Logger.f = open("log.txt", "w")
        Logger.structuredLogFile = open("structuredlog.json", "w")
        Logger.structuredLogFile.write("[")
    def close():
        Logger.f.close()
        Logger.structuredLogFile.write("{\"action\": \"QUIT\"}]")
        Logger.structuredLogFile.close()

class Tick:
    #Tick (open point: ma un tick avrà le candele o solo valori attuali?)
    # - timestamp
    # - lunghezza periodo (1 minuto?)
    # - mercato (coppia valute)
    # - candela per quel periodo (high, low, open, close, volume)
    # - oppure i valori del tick (bid, sell, quella roba li' che non ho ancora capito)
    
    def __init__(self, market, jsonTickData):
        self.market = market
        self.jsonTickData = jsonTickData
        # "volume" is the transaction volume for the target currency (if the market is BTC-LTC, gets the volume in LTC)
        self.volume = jsonTickData["V"]
        # "baseVolume" is the transaction volume for the target currency (if the market is BTC-LTC, gets the volume in BTC)
        self.baseVolume = jsonTickData["BV"]
        self.open = jsonTickData["O"]
        self.close = jsonTickData["C"]
        self.high = jsonTickData["H"]
        self.low = jsonTickData["L"]
        self.timestamp = self.jsonTickData["T"]

    def getTimestamp(self):
        #Example: 2017-09-05T22:28:00
        return datetime.strptime(timestamp, "%Y-%m-%dT%H:%M:%S")

    def __str__(self):
        return str(self.market + " " + self.jsonTickData["T"] + " C: " + str(self.close))
        
class MarketStatusRepository:
    # Oggetto (singleton?) MarketStatusRepository, in cui posso
    # - aggiungere un nuovo tick (ogni volta che aggiungo, ricalcola subito tutte le moving average eccetera)
    # - recuperare lo stato di un mercato (classe MarketStatus)
    #     - valore attuale
    #     - andamento (in crescita? in discesa?) fondamentalmente qui è il valore delle moving averages
    # keep the ticks in a circular buffer
    # also keep another circular buffer holding the EMA for every corresponding value in the ticks buffer

    # TODO: Might be a good idea to make a CircularBuffer class to avoid having to deal with its complexities here.
    #       calls to getLastNTicks are currently the performance bottleneck in backtesting
    
    def __init__(self):
        self.todaysTicks = [None for x in range(ticksBufferSize)] # 24 hours' worth of 1-minute candles
        # It might make sense to make a function that returns the last N days' EMA instead of computing it every time, 
        self.todaysEMAfast = [None for x in range(ticksBufferSize)] # Simple Moving Average (fast ticks)
        self.todaysEMAslow = [None for x in range(ticksBufferSize)] # Simple Moving Average (slow ticks)
        self.currentTickIndex = -1
        self.totalProcessedTicks = -1
        
    def getLastNTicks(self, tickCount):
        if self.currentTickIndex >= tickCount:
            return self.todaysTicks[self.currentTickIndex - tickCount:self.currentTickIndex + 1]
        else:
            # Gotta ignore the None values in the list (this is only a problem when the bot just started and the buffer isn't full yet)
            if tickCount <= self.totalProcessedTicks :
                return self.todaysTicks[self.currentTickIndex - tickCount:] \
                        + self.todaysTicks[0:self.currentTickIndex + 1]
            else:
                return self.todaysTicks[0:self.currentTickIndex + 1]
    
    def addTick(self, tick):
        self.totalProcessedTicks += 1
        self.currentTickIndex += 1
        if self.currentTickIndex == ticksBufferSize:
            self.currentTickIndex = 0
        self.todaysTicks[self.currentTickIndex] = tick
        # Update EMAs
        # Ignore None values (it just means the bot has just started and doesn't have 
        # enough ticks to compute the average of the entire window)

        self.computeEMA()

    def computeEMA(self):

        if len(self.getLastNTicks(fastEMAWindow)) < fastEMAWindow:
        # Just started the bot, not enough candles for computing the EMA, so fallback to EMA
            if accurateMean:
                self.todaysEMAfast[self.currentTickIndex] = statistics.mean([x.close for x in self.getLastNTicks(fastEMAWindow) if not x is None])
            else:
                self.todaysEMAfast[self.currentTickIndex] = sum([x.close for x in self.getLastNTicks(fastEMAWindow) if not x is None])/len(self.getLastNTicks(fastEMAWindow))
        else:
            # Multiplier: (2 / (Time periods + 1) ) = (2 / (10 + 1) ) = 0.1818 (18.18%)
            # EMA: {Close - EMA(previous day)} x multiplier + EMA(previous day). 
            self.todaysEMAfast[self.currentTickIndex] = (self.todaysTicks[self.currentTickIndex].close - self.todaysEMAfast[self.currentTickIndex - 1]) \
                                                        * fastEMAMultiplier \
                                                        + self.todaysEMAfast[self.currentTickIndex - 1]

        if len(self.getLastNTicks(slowEMAWindow)) < slowEMAWindow:
        # Just started the bot, not enough candles for computing the EMA, so fallback to EMA
            if accurateMean:
                self.todaysEMAslow[self.currentTickIndex] = statistics.mean([x.close for x in self.getLastNTicks(slowEMAWindow) if not x is None])
            else:
                self.todaysEMAslow[self.currentTickIndex] = sum([x.close for x in self.getLastNTicks(slowEMAWindow) if not x is None])/len(self.getLastNTicks(slowEMAWindow))
            
        else:
            # Multiplier: (2 / (Time periods + 1) ) = (2 / (10 + 1) ) = 0.1818 (18.18%)
            # EMA: {Close - EMA(previous day)} x multiplier + EMA(previous day). 
            self.todaysEMAslow[self.currentTickIndex] = (self.todaysTicks[self.currentTickIndex].close - self.todaysEMAslow[self.currentTickIndex - 1]) \
                                                        * slowEMAMultiplier \
                                                        + self.todaysEMAslow[self.currentTickIndex - 1]
        
    def getTick(self, index = 0):
        if ticksBufferSize - index < 0:
            raise Exception("too old, mang")
        return self.todaysTicks[self.currentTickIndex - index]
        
    def getEMA(self, type):
        if type == "fast":
            return self.todaysEMAfast[self.currentTickIndex]
        if type == "slow":
            return self.todaysEMAslow[self.currentTickIndex]
        raise Exception("meh")
        
    def printMarketStatus(self):
        log = Logger()
        log.log("Current tick: " + str(self.todaysTicks[self.currentTickIndex]))
        log.log("    Current EMAfast: " + str(self.todaysEMAfast[self.currentTickIndex]))
        log.log("    Current EMAslow: " + str(self.todaysEMAslow[self.currentTickIndex]))

class Analyst:
    # - ha un metodo che riceve in input un MarketStatus, prende una decisione su cosa fare e la fa fare all'exchangeWrapper:
    #     - vendere
    #     - comprare
    #     - NOP
    # - posso averne anche più di uno, ognuno con una strategia diversa
    # - ogni analyst ha una quantità propria di coin su cui giocare
    def __init__(self, exchange):
        self.exchange = exchange
        self.currentPeak = 0 # Used for stop-loss. 0 when I'm merely holding BTC
        self.currentCurrency = "BTC"
        self.currentBalance = exchange.getCurrentBalance()

    def doTrading(self, repo):
        """here do stuff on the exchange depending on the info I get from the marketStatus"""
        log = Logger()
        currTick = repo.getTick()
        if self.currentCurrency == "BTC":
            self.currentPeak = 0
        else:
            self.currentPeak = max(self.currentPeak, currTick.close)
            
        if verbose:
            repo.printMarketStatus()
            log.log("self.currentCurrency %s; self.currentPeak %f; currTick.close %f" \
                     % (self.currentCurrency, self.currentPeak, currTick.close))
        action = "NONE"

        if self.currentCurrency == "BTC":
            # Look for buying opportunities
            if repo.getEMA("fast") > repo.getEMA("slow"):
                self.exchange.buy("BTC-LTC")
                self.currentCurrency = "LTC"
                self.currentBalance = self.exchange.getCurrentBalance()
                action = "BUY"
        if self.currentCurrency != "BTC":
            # # Use stop-loss to see if it's better to sell
            # if currTick.close < self.currentPeak * stopLossPercentage:
            #     self.exchange.sell("BTC-LTC")
            #     self.currentCurrency = "BTC"
            #     self.currentBalance = self.exchange.getCurrentBalance()
            #     action = "SELL"
            if repo.getEMA("fast") < repo.getEMA("slow"):
                self.exchange.sell("BTC-LTC")
                self.currentCurrency = "BTC"
                self.currentBalance = self.exchange.getCurrentBalance()
                action = "SELL"
        log.structuredLog(currTick.close, currTick.baseVolume, repo.getEMA("fast"), repo.getEMA("slow"), action, self.currentBalance)

class ExchangeWrapper:
    # Oggetto (singleton?) che wrappa le chiamate al sito di exchange
    # - vendere
    # - comprare
    # - get del tick attuale
    # può anche essere mock, e in realtà leggere direttamente da un json coi dati storici
    
    def __init__(self):
        self.currentTickIndex = 0
        self.ticks = dict()
        self.currentBalance = 100
        self.currentCurrency = "BTC"
        log = Logger()
        log.log("Loading backtest data file...")
        completeTickerData = json.load(open("BTC-LTC.json", "r"))
        # for market in completeTickerData:
        #     marketName = market["market"]
        #     log.log("Doing %s ticks..." % marketName)
        #     for tick in market["ticks"]:
        #         if marketName not in self.ticks: self.ticks[marketName] = []
        #         self.ticks[marketName].append(Tick(marketName, tick))
        self.ticks["BTC-LTC"] = []
        for tick in completeTickerData:
            self.ticks["BTC-LTC"].append(Tick("BTC-LTC", tick))

    #TODO instead of keeping a huge ticks dictionary in memory, read the text file gradually
    #and use yeld to return each tick
    def getCurrentTick(self, market):
        output = self.ticks[market][self.currentTickIndex]
        self.currentTickIndex += 1
        return output

    def gotMoreTicks(self, market):
        # -1 because i want to keep the last tick "unpopped", so that the last sell() works
        # return self.currentTickIndex < 2000
        return self.currentTickIndex < len(self.ticks[market]) - 1 

    def buy(self, market):
        if self.currentCurrency != "BTC":
            raise Exception("Already bought!")
        log = Logger()
        log.log("BUY!")
        price = self.ticks[market][self.currentTickIndex].close
        self.currentBalance = self.currentBalance / price * bittrexCommission
        self.currentCurrency = "LTC"

    def sell(self, market):
        if self.currentCurrency == "BTC":
            raise Exception("Already sold!")
        log = Logger()
        log.log("SELL!")
        price = self.ticks[market][self.currentTickIndex].close
        self.currentBalance = self.currentBalance * price * bittrexCommission
        self.currentCurrency = "BTC"

    def getCurrentBalance(self):
        return self.currentBalance

    def getCurrentCurrency(self):
        return self.currentCurrency

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

