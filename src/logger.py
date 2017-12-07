import time
import config
import json

class Logger:

    f = None
    structuredLogFile = None
    
    def log(self, message):
        string = time.strftime("[%Y-%m-%d %H:%M:%S]", time.localtime(time.time())) + " " + message
        Logger.f.write(string + "\n")
        if config.enableStdoutLog:
            print(string)
        
    def structuredLog(self, obj):
        Logger.structuredLogFile.write(json.dumps(obj) + ",\n")
        
    def open():
        Logger.f = open("../output_files/log.txt", "w")
        Logger.structuredLogFile = open("../output_files/structuredlog.json", "w")
        Logger.structuredLogFile.write("[")
    def close():
        Logger.f.close()
        Logger.structuredLogFile.write("{\"action\": \"QUIT\"}]")
        Logger.structuredLogFile.close()

def test():
    l = Logger()
    Logger.open()
    l.structuredLog({"lol": "lol", "merda": "dfscsdafads"})
    Logger.close()

if __name__ == "__main__":
    test()
