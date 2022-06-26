import telebot

import creds
from logger import logger


bot = telebot.TeleBot(creds.TOKEN_BOT)


def bot_send_to_chat(text):
    """ Bot-телеграмм для отправки сообщений в чат-группу
        CHANNEL_NAME: id чат-группы (-642148596 - GroupTestApi)
        text: сообщение для отправки в чат-группу
    """
    CHANNEL_NAME = -642148596
    bot.send_message(CHANNEL_NAME, text)
    logger.info("Отправка сообщеня в чат")

    # bot.polling(none_stop=True, interval=0)


if __name__ == '__main__':
    logger.info("тест")
