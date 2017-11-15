import time
import config

class Logger:

    f = None
    structuredLogFile = None
    
    def log(self, message):
        string = time.strftime("[%Y-%m-%d %H:%M:%S]", time.localtime(time.time())) + " " + message
        Logger.f.write(string + "\n")
        if config.enableStdoutLog:
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