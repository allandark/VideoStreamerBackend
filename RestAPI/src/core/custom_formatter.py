
import logging


def InitLogger(app):
    logger = app.logger
    logger.setLevel(logging.DEBUG)
    logger.handlers.clear()

    ch1 = logging.StreamHandler()
    ch1.setFormatter(CustomFormatter(colors=True))
    logger.addHandler(ch1)
    ch2 = logging.FileHandler("logs/app.log")
    ch2.setFormatter(CustomFormatter(colors=False))
    logger.addHandler(ch2)

    
    werkzeug_logger = logging.getLogger('werkzeug')
    werkzeug_logger.handlers.clear()
    werkzeug_logger.addHandler(ch1)
    werkzeug_logger.setLevel(logging.DEBUG)

    

class CustomFormatter(logging.Formatter):
    
    def __init__(self, colors: bool, **kvargs):
        self.colors = colors

    NO_COLOR = -1

    green = "\x1b[32m"
    blue = "\x1b[36m"
    grey = "\x1b[38;20m"
    yellow = "\x1b[33;20m"
    red = "\x1b[31;20m"
    bold_red = "\x1b[31;1m"
    reset = "\x1b[0m"
    format = "[%(asctime)s]:[%(name)s]:[%(levelname)s]: %(message)s (%(filename)s:%(lineno)d)"

    FORMATS = {
        logging.DEBUG: blue + format + reset,
        logging.INFO: green + format + reset,
        logging.WARNING: yellow + format + reset,
        logging.ERROR: red + format + reset,
        logging.CRITICAL: bold_red + format + reset,
        NO_COLOR: format
    }

    def format(self, record):
        if self.colors:
          log_fmt = self.FORMATS.get(record.levelno)
        else:
          log_fmt = self.FORMATS.get(self.NO_COLOR)
        formatter = logging.Formatter(log_fmt)
        return formatter.format(record)