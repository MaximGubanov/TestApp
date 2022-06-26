import sys
import logging.handlers
import os
import logging

sys.path.append('../')

server_formatter = logging.Formatter('%(asctime)s %(levelname)s %(filename)s %(message)s')

path = os.path.dirname(os.path.abspath(__file__))
path = os.path.join(path, 'main.log')

steam = logging.StreamHandler(sys.stderr)
steam.setFormatter(server_formatter)
steam.setLevel(logging.INFO)
log_file = logging.handlers.TimedRotatingFileHandler(path, encoding='utf8', interval=1, when='D')
log_file.setFormatter(server_formatter)

logger = logging.getLogger('logger')
logger.addHandler(steam)
logger.addHandler(log_file)
logger.setLevel(logging.DEBUG)

# тест
if __name__ == '__main__':
    logger.critical('Test critical event')
    logger.error('Test error ivent')
    logger.debug('Test debug ivent')
    logger.info('Test info ivent')
