import logging
import os
import logging.handlers

handler = logging.handlers.WatchedFileHandler(
    os.environ.get("LOGFILE", os.getcwd() + "/logs/app.log"), encoding='utf-8')
formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
handler.setFormatter(formatter)
root = logging.getLogger()
root.setLevel(os.environ.get("LOGLEVEL", "INFO"))
root.addHandler(handler)
logger = logging.getLogger('spam')
