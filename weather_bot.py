"""This is telegram bot app for temperature and rain."""
import os
import time
import telebot
import schedule
import requests

bot = telebot.TeleBot(os.getenv('TOKEN_TELEGRAM_BOT'))
start_txt = 'Привет, я готов составить для тебя прогноз погоды!'


@bot.message_handler(commands=['start'])
def start(message):
    """Обработка /start сообщения."""
    bot.send_message(message.from_user.id, start_txt, parse_mode='Markdown')


def response():
    """Функция запроса данных с API.

    И передачи ответа в telegram
    """
    params = {
        "latitude": 22.60448,
        "longitude": 114.321082,
        "hourly": "precipitation",
        "timezone": "Asia/Singapore",
        "forecast_days": 1
    }
    url = (f'https://api.open-meteo.com/v1/forecast?'
           f'latitude={params["latitude"]}'
           f'&longitude={params["longitude"]}'
           f'&hourly=temperature_2m,precipitation&'
           f'timezone=auto&forecast_days=1')
    response = requests.get(url).json()
    try:
        process_data(response)
    except Exception as e:
        print(e)
        bot.send_message(os.getenv('CHAT_ID'), f'Возникло исключение {e}')


def process_data(response):
    """Обработка полученного запроса.

    Анализ необходимости зонта и определение средней температуры.
    """
    hourly = response["hourly"]
    temp_list = hourly["temperature_2m"]
    precipitation_list = hourly["precipitation"]
    needable_hours_temp = temp_list[9:18]
    average_temp = round((sum(needable_hours_temp) / 9), 1)
    needable_hours_precipitation = precipitation_list[9:18]
    needable_umbrella_hours = ([9 + index for index in range(
        len(needable_hours_precipitation))
        if needable_hours_precipitation[index] > 0])
    return create_message(needable_umbrella_hours, average_temp)


def create_message(needable_umbrella_hours, average_temp):
    """Формирование сообщения."""
    if needable_umbrella_hours:
        list_of_hours = ':00, '.join(
            str(hour) for hour in needable_umbrella_hours)
        rain_message = (f'Сегодня точно будет дождь '
                        f'в {list_of_hours}:00, \n'
                        f'возьми зонт')
    else:
        rain_message = 'Дождя не будет, пусть зонт отдохнет!'
    message = (f'Средняя температура воздуха на сегодня: {average_temp}°С.\n'
               f'{rain_message}')
    return bot.send_message(os.getenv('CHAT_ID'), message)


def job_that_executes_once():
    """Выполняет один раз работу и отключается."""
    response()
    return schedule.CancelJob


schedule.every().day.at('12:40').do(job_that_executes_once)
schedule.every().day.at('23:50').do(job_that_executes_once)


if __name__ == '__main__':
    while True:
        schedule.run_pending()
        time.sleep(1)
