import datetime, time, json, statistics

# CONFIGURATION:
bittrexCommission = 0.9975 # 0.25% commissions
stopLossPercentage = 0.99
ticksBufferSize = 24*60*7    # How many candles are kept in memory
enableStdoutLog = False
verbose = True
accurateMean = True
fastSMAWindow = 10000
slowSMAWindow = 100

class Logger:

    f = None
    structuredLogFile = None
    
    def log(self, message):
        string = time.strftime("[%Y-%m-%d %H:%M:%S]", time.localtime(time.time())) + " " + message
        Logger.f.write(string + "\n")
        if enableStdoutLog:
            print(string)
        
    def structuredLog(self, price, fastSMAValue, slowSMAValue, action, currentBalance):
        Logger.structuredLogFile.write("{\"price\": " + str(price))
        Logger.structuredLogFile.write(", \"fastSMAValue\": " + str(fastSMAValue))
        Logger.structuredLogFile.write(", \"slowSMAValue\": " + str(slowSMAValue))
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
    # also keep another circular buffer holding the SMA for every corresponding value in the ticks buffer

    # Might be a good idea to make a CircularBuffer class to avoid having to deal with its complexities here.
    
    def __init__(self):
        self.todaysTicks = [None for x in range(ticksBufferSize)] # 24 hours' worth of 1-minute candles
        # It might make sense to make a function that returns the last N days' SMA instead of computing it every time, 
        self.todaysSMAfast = [None for x in range(ticksBufferSize)] # Simple Moving Average (fast ticks)
        self.todaysSMAslow = [None for x in range(ticksBufferSize)] # Simple Moving Average (slow ticks)
        self.currentTickIndex = -1
        
    def getLastNTicks(self, tickCount):
        if self.currentTickIndex >= tickCount:
            return self.todaysTicks[self.currentTickIndex - tickCount:self.currentTickIndex + 1]
        else:
            return [x for x in self.todaysTicks[self.currentTickIndex - tickCount:] if not x is None] \
                   + [x for x in self.todaysTicks[0:self.currentTickIndex + 1]]
    
    def addTick(self, tick):
        self.currentTickIndex += 1
        if self.currentTickIndex == ticksBufferSize:
            self.currentTickIndex = 0
        self.todaysTicks[self.currentTickIndex] = tick
        # Update SMAs
        # Ignore None values (it just means the bot has just started and doesn't have 
        # enough ticks to compute the average of the entire window)

        # statistics.mean might be slightly more precise, but it's probably not worth it

        if accurateMean:
            self.todaysSMAfast[self.currentTickIndex] = statistics.mean([x.close for x in self.getLastNTicks(fastSMAValue) if not x is None])
            self.todaysSMAslow[self.currentTickIndex] = statistics.mean([x.close for x in self.getLastNTicks(slowSMAWindow) if not x is None])
        else:
            self.todaysSMAfast[self.currentTickIndex] = sum([x.close for x in self.getLastNTicks(fastSMAWindow) if not x is None])/len(self.getLastNTicks(fastSMAWindow))
            self.todaysSMAslow[self.currentTickIndex] = sum([x.close for x in self.getLastNTicks(slowSMAWindow) if not x is None])/len(self.getLastNTicks(slowSMAWindow))
        
    def getTick(self, index = 0):
        if ticksBufferSize - index < 0:
            raise Exception("too old, mang")
        return self.todaysTicks[self.currentTickIndex - index]
        
    def getSMA(self, type):
        if type == "fast":
            return self.todaysSMAfast[self.currentTickIndex]
        if type == "slow":
            return self.todaysSMAslow[self.currentTickIndex]
        raise Exception("meh")
        
    def printMarketStatus(self):
        log = Logger()
        log.log("Current tick: " + str(self.todaysTicks[self.currentTickIndex]))
        log.log("    Current SMAfast: " + str(self.todaysSMAfast[self.currentTickIndex]))
        log.log("    Current SMAslow: " + str(self.todaysSMAslow[self.currentTickIndex]))

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
            if repo.getSMA("fast") > repo.getSMA("slow"):
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
            if repo.getSMA("fast") < repo.getSMA("slow"):
                self.exchange.sell("BTC-LTC")
                self.currentCurrency = "BTC"
                self.currentBalance = self.exchange.getCurrentBalance()
                action = "SELL"
        log.structuredLog(currTick.close, repo.getSMA("fast"), repo.getSMA("slow"), action, self.currentBalance)

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
        return self.currentTickIndex < 2000
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
    while exchange.gotMoreTicks("BTC-LTC"):
        repo.addTick(exchange.getCurrentTick("BTC-LTC"))
        analyst.doTrading(repo)
    if exchange.getCurrentCurrency() != "BTC":
        log.log("Ran out of test data, selling back to BTC")
        exchange.sell("BTC-LTC")
    log.log("Final balance: %f BTC" % exchange.getCurrentBalance())
    Logger.close()

if __name__ == "__main__":
    main()
