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
backtestingDataDirectory = "backtesting_data"