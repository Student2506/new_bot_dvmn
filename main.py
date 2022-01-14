import os
import time
import requests
import telegram


BASE_URL = 'https://dvmn.org/api/long_polling/'
CBOT_DVMN_KEY = os.environ['DVMN_KEY']
CBOT_BOT_TOKEN = os.environ['BOT_TOKEN']
CBOT_CHAT_ID = os.environ['CHAT_ID']
TIMEOUT = 90

def main():
    delay = 10
    timestamp = time.time()
    headers = {'Authorization': f'Token {CBOT_DVMN_KEY}'}
    bot = telegram.Bot(token=CBOT_BOT_TOKEN)
    while True:
        params = {"timestamp": timestamp}
        try:
            response = requests.get(BASE_URL, headers=headers, params=params, timeout=(TIMEOUT+delay))
            response.raise_for_status()
            homeworks = response.json()
            if 'timeout' in homeworks:
                timestamp = homeworks.get('timestamp_to_request')
            if 'found' in homeworks:
                timestamp = homeworks.get('last_attempt_timestamp')
                results = homeworks.get('new_attempts', [])
                for result in results:
                    result_title = result.get('lesson_title')
                    result_url = result.get('lesson_url')    
                    if result.get('is_negative'):
                        bot.send_message(
                            chat_id=CBOT_CHAT_ID,
                            text=f'У Вас проверили работу "{result_title}"\n\n'
                                  'К сожалению в работе нашлись ошибки.\n'
                                  f'{result_url}'
                        )
                    else:
                        bot.send_message(
                            chat_id=CBOT_CHAT_ID,
                            text=f'У Вас проверили работу "{result_title}"\n\n'
                                  'Преподавателю все понравилось, '
                                  f'можно приступать к следующему уроку!\n{result_url}'
                        )
        except ConnectionError as e:
            print(e)
            time.sleep(delay)
        except requests.ReadTimeout:
            pass
        

if __name__ == '__main__':
    main()