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
        