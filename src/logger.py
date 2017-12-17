import time, json, logging
from telegram.ext import Updater, CommandHandler
import config


class Logger:

    f = None
    structuredLogFile = None

    telegramUpdater = Updater(token=config.telegramToken)
    logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)
    
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

    def sendTelegramMessage(message):
        if config.enableTelegramIntegration:
            Logger.telegramUpdater.bot.send_message(chat_id=config.telegramChatId, text=message)

def test():
    l = Logger()
    Logger.open()
    l.structuredLog({"lol": "lol", "merda": "dfscsdafads"})
    Logger.close()

if __name__ == "__main__":
    test()
