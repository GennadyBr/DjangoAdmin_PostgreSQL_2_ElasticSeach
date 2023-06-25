import logging
import logging.handlers

def init_logger(name):
    logger = logging.getLogger(name)  #инициализация
    FORMAT = '%(asctime)s :: %(name)s:%(lineno)s :: %(levelname)s :: %(message)s' #формат сообщения
    logger.setLevel(logging.INFO)  #2
    sh = logging.StreamHandler()  #3
    sh.setFormatter(logging.Formatter(FORMAT))  #инициализация формата
    sh.setLevel(logging.INFO)  #4
    fh = logging.handlers.RotatingFileHandler(filename='test.log')  #файл с перезаписью при переполнении
    fh.setFormatter(logging.Formatter(FORMAT))  #6
    fh.setLevel(logging.INFO)  #4
    logger.addHandler(sh)  #хендлер sh
    logger.addHandler(fh)  #хендлер fh
    logger.debug("logger was initialized")  #7

