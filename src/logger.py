import time, json, logging, os
from telegram.ext import Updater, CommandHandler
import config

class Logger:

    f = None
    structuredLogFile = None

    telegramUpdater = None
    if config.enableTelegramIntegration:
        telegramUpdater = Updater(token=config.telegramToken)
    logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)

    def log(message):
        string = time.strftime("[%Y-%m-%d %H:%M:%S]", time.localtime(time.time())) + " " + message
        if config.enableStdoutLog:
            print(string)
        Logger.f.write(string + "\n")

    def structuredLog(obj, printToStdout = False):
        j = json.dumps(obj)
        Logger.structuredLogFile.write(j + ",\n")
        if printToStdout:
            print(j)

    def open():
        if not os.path.exists("../output_files"):
            os.mkdir("../output_files")
        Logger.f = open("../output_files/log.txt", "w")
        Logger.structuredLogFile = open("../output_files/structuredlog.json", "w")
        Logger.structuredLogFile.write("[")

    def close():
        Logger.f.close()
        Logger.structuredLogFile.write("{\"action\": \"QUIT\"}]")
        Logger.structuredLogFile.close()

    def sendTelegramMessage(message):
        if config.verbose:
            Logger.log("Sending to telegram: %s" % message)
        if config.enableTelegramIntegration:
            Logger.telegramUpdater.bot.send_message(chat_id=config.telegramChatId, text=message)

def test():
    Logger.open()
    l.structuredLog({"lol": "lol", "merda": "dfscsdafads"})
    Logger.close()

if __name__ == "__main__":
    test()
