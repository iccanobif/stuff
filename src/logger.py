import time, json, logging
from telegram.ext import Updater, CommandHandler
import config

class Logger:

    f = None
    structuredLogFile = None

    telegramUpdater = Updater(token=config.telegramToken)
    logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)

    # TODO: Make this a static function, instantiating Logger everywhere is just inconvenient
    def log(self, message):
        string = time.strftime("[%Y-%m-%d %H:%M:%S]", time.localtime(time.time())) + " " + message
        Logger.f.write(string + "\n")
        if config.enableStdoutLog:
            print(string)

    # TODO: Make this a static function, instantiating Logger everywhere is just inconvenient
    def structuredLog(self, obj, printToStdout = False):
        j = json.dumps(obj)
        Logger.structuredLogFile.write(j + ",\n")
        if printToStdout:
            print(j)

    def open():
        Logger.f = open("../output_files/log.txt", "w")
        Logger.structuredLogFile = open("../output_files/structuredlog.json", "w")
        Logger.structuredLogFile.write("[")

    def close():
        Logger.f.close()
        Logger.structuredLogFile.write("{\"action\": \"QUIT\"}]")
        Logger.structuredLogFile.close()

    def sendTelegramMessage(message):
        if config.verbose:
            # TODO: shoud use Logger.log
            print("Sending to telegram: %s" % message)
        if config.enableTelegramIntegration:
            Logger.telegramUpdater.bot.send_message(chat_id=config.telegramChatId, text=message)

def test():
    l = Logger()
    Logger.open()
    l.structuredLog({"lol": "lol", "merda": "dfscsdafads"})
    Logger.close()

if __name__ == "__main__":
    test()
