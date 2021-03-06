import logging
import os
import time

import requests
import telegram
# from dotenv import load_dotenv

# load_dotenv()

BASE_URL = 'https://dvmn.org/api/long_polling/'
CBOT_DVMN_KEY = os.environ['DVMN_KEY']
CBOT_BOT_TOKEN = os.environ['BOT_TOKEN']
CBOT_CHAT_ID = os.environ['CHAT_ID']
TIMEOUT = 90


logger = logging.getLogger('dvmn_bot')


class TelegramLogsHandler(logging.Handler):

    def __init__(self, tg_bot, chat_id):
        super().__init__()
        self.chat_id = chat_id
        self.tg_bot = tg_bot

    def emit(self, record):
        log_entry = self.format(record)
        self.tg_bot.send_message(chat_id=self.chat_id, text=log_entry)


def main():
    logging_bot = telegram.Bot(token=CBOT_BOT_TOKEN)
    logging.basicConfig(
        level=logging.DEBUG,
        format='%(asctime)s, %(levelname)s, %(message)s, %(name)s'
    )
    logger.setLevel(logging.WARNING)
    logger.addHandler(TelegramLogsHandler(logging_bot, CBOT_CHAT_ID))
    main_bot = telegram.Bot(token=CBOT_BOT_TOKEN)
    logging.debug('Бот стартовал')
    delay = 10
    timestamp = time.time()
    headers = {'Authorization': f'Token {CBOT_DVMN_KEY}'}

    while True:
        params = {"timestamp": timestamp}
        try:
            response = requests.get(
                BASE_URL, headers=headers, params=params, timeout=(
                    TIMEOUT+delay
                )
            )
            logging.debug(response.text)
            response.raise_for_status()
            homeworks = response.json()
            if 'timeout' in response.text:
                timestamp = homeworks.get('timestamp_to_request')
            if 'found' in response.text:
                timestamp = homeworks.get('last_attempt_timestamp')
                logging.debug(homeworks)

                results = homeworks.get('new_attempts', [])
                for result in results:
                    result_title = result.get('lesson_title')
                    result_url = result.get('lesson_url')
                    if result.get('is_negative'):
                        main_bot.send_message(
                            chat_id=CBOT_CHAT_ID,
                            text=f'У Вас проверили работу "{result_title}"\n\n'
                                 'К сожалению в работе нашлись ошибки.\n'
                                 f'{result_url}'
                        )
                    else:
                        main_bot.send_message(
                            chat_id=CBOT_CHAT_ID,
                            text=f'У Вас проверили работу "{result_title}"\n\n'
                                 'Преподавателю все понравилось, '
                                 'можно приступать к следующему уроку!\n'
                                 f'{result_url}'
                        )
        except ConnectionError:
            logger.exception('Site connection lost')
            time.sleep(delay)
        except requests.ReadTimeout:
            pass


if __name__ == '__main__':
    main()
