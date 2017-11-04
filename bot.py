import datetime, time, json, statistics

# CONSTANTS:
bittrexCommission = 0.9975 # 0.25% commissions
stopLossPercentage = 0.99
ticksBufferSize = 24*60    # How many candles are kept in memory

class Logger:

    f = None
    structuredLogFile = None
    
    def log(self, message):
        string = time.strftime("[%Y-%m-%d %H:%M:%S]", time.localtime(time.time())) + " " + message
        Logger.f.write(string + "\n")
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

    def getTimestamp(self):
        #Example: 2017-09-05T22:28:00
        t = self.jsonTickData["T"]
        return datetime.strptime(t, "%Y-%m-%dT%H:%M:%S")
    
    # Gets the transaction volume for the target currency (if the market
    # is BTC-LTC, gets the volume in LTC)
    def getVolume(self):
        return self.jsonTickData["V"]

    # Gets the transaction volume for the target currency (if the market
    # is BTC-LTC, gets the volume in BTC)
    def getBaseVolume(self):
        return self.jsonTickData["BV"]

    def getOpen(self):
        return self.jsonTickData["O"]

    def getClose(self):
        return self.jsonTickData["C"]

    def getHig(self):
        return self.jsonTickData["H"]

    def getLow(self):
        return self.jsonTickData["L"]

    def __str__(self):
        return str(self.market + " " + self.jsonTickData["T"] + " C: " + str(self.getClose()))
        
class MarketStatusRepository:
    # Oggetto (singleton?) MarketStatusRepository, in cui posso
    # - aggiungere un nuovo tick (ogni volta che aggiungo, ricalcola subito tutte le moving average eccetera)
    # - recuperare lo stato di un mercato (classe MarketStatus)
    #     - valore attuale
    #     - andamento (in crescita? in discesa?) fondamentalmente qui è il valore delle moving averages
    # keep the ticks in a circular buffer
    # also keep another circular buffer holding the SMA for every corresponding value in the ticks buffer
    
    def __init__(self):
        self.todaysTicks = [None for x in range(ticksBufferSize)] # 24 hours' worth of 1-minute candles
        # It might make sense to make a function that returns the last N days' SMA instead of computing it every time, 
        self.todaysSMA10 = [None for x in range(ticksBufferSize)] # Simple Moving Average (10 ticks)
        self.todaysSMA50 = [None for x in range(ticksBufferSize)] # Simple Moving Average (50 ticks)
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
        self.todaysSMA10[self.currentTickIndex] = statistics.mean([x.getClose() for x in self.getLastNTicks(10)])
        self.todaysSMA50[self.currentTickIndex] = statistics.mean([x.getClose() for x in self.getLastNTicks(50)])
        
    def getTick(self, index = 0):
        if ticksBufferSize - index < 0:
            raise Exception("too old, mang")
        return self.todaysTicks[self.currentTickIndex - index]
        
    def getSMA(self, days):
        if days == 10:
            return self.todaysSMA10[self.currentTickIndex]
        if days == 50:
            return self.todaysSMA50[self.currentTickIndex]
        raise Exception("meh")
        
    def printMarketStatus(self):
        log = Logger()
        log.log("Current tick: " + str(self.todaysTicks[self.currentTickIndex]))
        log.log("    Current SMA10: " + str(self.todaysSMA10[self.currentTickIndex]))
        log.log("    Current SMA50: " + str(self.todaysSMA50[self.currentTickIndex]))
        # print(self.todaysTicks[self.currentTickIndex].getClose(), self.todaysSMA10[self.currentTickIndex], self.todaysSMA50[self.currentTickIndex])

class Analyst:
    # - ha un metodo che riceve in input un MarketStatus, prende una decisione su cosa fare e la fa fare all'exchangeWrapper:
    #     - vendere
    #     - comprare
    #     - NOP
    # - posso averne anche più di uno, ognuno con una strategia diversa
    # - ogni analyst ha una quantità propria di coin su cui giocare
    def __init__(self, exchange):
        print("INIT ANAYLS")
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
            currentPeak = max(self.currentPeak, currTick.getClose())
            
        action = "NONE"
        if self.currentCurrency == "BTC":
            # Look for buying opportunities
            if repo.getSMA(10) > repo.getSMA(50):
                self.exchange.buy("BTC-LTC")
                self.currentCurrency = "LTC"
                self.currentBalance = self.exchange.getCurrentBalance()
                action = "BUY"
        if self.currentCurrency != "BTC":
            # Use stop-loss to see if it's better to sell
            if self.currentBalance < self.currentPeak * stopLossPercentage:
                self.exchange.sell("BTC-LTC")
                self.currentCurrency = "BTC"
                self.currentBalance = self.exchange.getCurrentBalance()
                action = "SELL"
            # if repo.getSMA(10) < repo.getSMA(50):
            #     self.exchange.sell("BTC-LTC")
            #     self.currentCurrency = "BTC"
            #     self.currentBalance = self.exchange.getCurrentBalance()
            #     action = "SELL"
        log.structuredLog(currTick.getClose(), repo.getSMA(10), repo.getSMA(50), action, self.currentBalance)

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
        log.log("Loading csv file...")
        completeTickerData = json.load(open("BTC-LTC.json", "r"))
        for market in completeTickerData:
            marketName = market["market"]
            log.log("Doing %s ticks..." % marketName)
            for tick in market["ticks"]:
                if marketName not in self.ticks: self.ticks[marketName] = []
                self.ticks[marketName].append(Tick(marketName, tick))

    #TODO instead of keeping a huge ticks dictionary in memory, read the text file gradually
    #and use yeld to return each tick
    def getCurrentTick(self, market):
        output = self.ticks[market][self.currentTickIndex]
        self.currentTickIndex += 1
        return output

    def buy(self, market):
        if self.currentCurrency != "BTC":
            raise Exception("Already bought!")
        log = Logger()
        log.log("BUY!")
        price = self.ticks[market][self.currentTickIndex].getClose()
        self.currentBalance = self.currentBalance * price * bittrexCommission
        self.currentCurrency = "LTC"

    def sell(self, market):
        if self.currentCurrency == "BTC":
            raise Exception("Already sold!")
        log = Logger()
        log.log("SELL!")
        price = self.ticks[market][self.currentTickIndex].getClose()
        self.currentBalance = self.currentBalance / price * bittrexCommission
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
    log.log("Initial balance: " + str(exchange.getCurrentBalance()))
    for i in range(0,1000):
        repo.addTick(exchange.getCurrentTick("BTC-LTC"))
        repo.printMarketStatus()
        analyst.doTrading(repo)
    if exchange.getCurrentCurrency() != "BTC":
        log.log("finito, vendo tutto")
        exchange.sell("BTC-LTC")
    log.log("Final balance: " + str(exchange.getCurrentBalance()))
    Logger.close()

if __name__ == "__main__":
    main()
