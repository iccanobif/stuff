import datetime
import config

class Candle:
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
        self.price = self.close # FIXME: A pretty shitty way of making code that expects Ticks work with Candles too
        self.high = jsonTickData["H"]
        self.low = jsonTickData["L"]
        self.timestamp = self.jsonTickData["T"]

    def getTimestamp(self):
        #Example: 2017-09-05T22:28:00
        return datetime.datetime.strptime(self.timestamp, config.timestampStringFormat)

    def __str__(self):
        return str(self.market + " " + self.jsonTickData["T"] + " C: " + str(self.close))

class Tick:
    def __init__(self, candle = None):
        # The candle parameter is only useful when "converting" a Candle to a Tick.
        # This only makes sense when backtesting, since my backtesting data has candles, not ticks...
        if candle is None:
            self.market = None
            self.price = None
            self.ask = None
            self.bid = None
            self.timestamp = None # Datetime object
        else:
            self.market = candle.market
            self.price = candle.close
            self.ask = None
            self.bid = None
            self.timestamp = candle.getTimestamp() # Datetime object

    def __str__(self):
        return str(self.market + " " + self.timestamp.strftime(config.timestampStringFormat) + " value: " + str(self.price))