import logging

msgLogger = logging.getLogger("msgLogger")
msgLogger.setLevel(logging.INFO)

logger_file_handler = logging.FileHandler("msgLog.log")
logger_file_handler.setLevel(logging.INFO)

logger_console_handler = logging.StreamHandler()
logger_console_handler.setLevel(logging.DEBUG)

logger_formatter = logging.Formatter("%(asctime)s %(levelname)s %(message)s")

logger_file_handler.setFormatter(logger_formatter)
logger_console_handler.setFormatter(logger_formatter)

msgLogger.addHandler(logger_file_handler)
msgLogger.addHandler(logger_console_handler)


chatLogger = logging.getLogger("chatLogger")
chatLogger.setLevel(logging.INFO)
chat_file_handler = None

giftLogger = logging.getLogger("giftLogger")
giftLogger.setLevel(logging.INFO)
gift_file_handler = None

def setGiftLoggerFilename(filename:str):
    global gift_file_handler
    global giftLogger

    if len(filename) == 0:
        filename = "gift"
    filename += ".log"

    if gift_file_handler:
        giftLogger.removeHandler(gift_file_handler)

    file_handler = logging.FileHandler(filename)
    file_handler.setLevel(logging.INFO)
    formatter = logging.Formatter("%(asctime)s %(message)s")
    file_handler.setFormatter(formatter )

    gift_file_handler = file_handler
    giftLogger.addHandler(gift_file_handler)

def setChatLoggerFilename(filename:str):
    global chat_file_handler
    global chatLogger

    if len(filename) == 0:
        filename = "chat"
    filename += ".log"

    if chat_file_handler:
        chatLogger.removeHandler(chat_file_handler)

    file_handler = logging.FileHandler(filename)
    file_handler.setLevel(logging.INFO)
    formatter = logging.Formatter("%(asctime)s %(message)s")
    file_handler.setFormatter(formatter )

    chat_file_handler = file_handler
    chatLogger.addHandler(chat_file_handler)