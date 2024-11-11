from random import choice, randint
import logging

import redis
from environs import Env
from telegram import Bot
import vk_api as vk
from vk_api.longpoll import VkLongPoll, VkEventType
from vk_api.keyboard import VkKeyboard

from add_questions import parse_file


logger = logging.getLogger(__name__)


class TelegramLogsHandler(logging.Handler):

    def __init__(self, tg_bot, chat_id):
        super().__init__()
        self.chat_id = chat_id
        self.tg_bot = tg_bot

    def emit(self, record):
        log_entry = self.format(record)
        self.tg_bot.send_message(chat_id=self.chat_id, text=log_entry)


def handle_new_question_request(event,
                                vk_api,
                                keyboard,
                                redis_connection,
                                questions_and_answers):
    question = choice(list(questions_and_answers.keys()))
    redis_connection.set(event.user_id, question)
    vk_api.messages.send(
        user_id=event.user_id,
        message=question,
        random_id=randint(1, 1000),
        keyboard=keyboard.get_keyboard(),
    )


def handle_solution_attempt(event,
                            vk_api,
                            keyboard,
                            redis_connection,
                            questions_and_answers):

    question = redis_connection.get(event.user_id)
    answer = questions_and_answers[question]
    correct_answer = ''
    if '.' in answer:
        correct_answer = answer.split('.')[0].lower()
    elif '(' in answer:
        correct_answer = answer.split('(')[0].lower()
    if event.text in correct_answer:
        vk_api.messages.send(
            user_id=event.user_id,
            message='Правильно! Поздравляю! Для следующего вопроса нажми «Новый вопрос».',
            keyboard=keyboard.get_keyboard(),
            random_id=randint(1, 1000)
        )
    else:
        vk_api.messages.send(
            user_id=event.user_id,
            message='Неправильно… Попробуешь ещё раз?',
            keyboard=keyboard.get_keyboard(),
            random_id=randint(1, 1000)
        )


def give_up(event,
            vk_api,
            keyboard,
            redis_connection,
            questions_and_answers):

    question = redis_connection.get(event.user_id)
    answer = questions_and_answers[question]
    vk_api.messages.send(
            user_id=event.user_id,
            message=f'Правильный ответ: "{answer}"',
            keyboard=keyboard.get_keyboard(),
            random_id=randint(1, 1000)
        )

    return handle_new_question_request(event,
                                       vk_api,
                                       keyboard,
                                       redis_connection,
                                       questions_and_answers)


if __name__ == '__main__':
    env = Env()
    env.read_env()

    vk_token = env.str('VK_API_TOKEN')
    redis_db_host = env.str('REDIS_DB_HOST')
    redis_db_port = env.str('REDIS_DB_PORT')
    quiz_file_path = env('QUIZ_FILE_PATH', default='questions/1vs1200.txt')
    tg_bot_token = env.str('TG_BOT_TOKEN')
    tg_chat_id = env.str('TG_CHAT_ID')

    bot = Bot(tg_bot_token)

    redis_connection = redis.Redis(host=redis_db_host,
                                   port=redis_db_port,
                                   decode_responses=True)
    questions_and_answers = parse_file(quiz_file_path)

    logging.basicConfig(format="%(asctime)s %(levelname)s %(message)s")
    logger.setLevel(logging.INFO)
    logger.addHandler(TelegramLogsHandler(bot, tg_chat_id))
    logger.info('VK бот запущен')

    try:
        vk_session = vk.VkApi(token=vk_token)
        vk_api = vk_session.get_api()

        keyboard = VkKeyboard(one_time=True)
        keyboard.add_button('Новый вопрос')
        keyboard.add_button('Сдаться')
        keyboard.add_line()
        keyboard.add_button('Мой счет')

        longpoll = VkLongPoll(vk_session)
        for event in longpoll.listen():
            if not (event.type == VkEventType.MESSAGE_NEW and event.to_me):
                continue

            if event.text == '/start':
                vk_api.messages.send(
                    user_id=event.user_id,
                    message='Привет! Я бот для викторин!',
                    keyboard=keyboard.get_keyboard(),
                    random_id=randint(1, 1000)
                )
                continue

            if event.text == 'Новый вопрос':
                handle_new_question_request(event,
                                            vk_api,
                                            keyboard,
                                            redis_connection,
                                            questions_and_answers)
                continue

            if event.text == 'Сдаться':
                give_up(event,
                        vk_api,
                        keyboard,
                        redis_connection,
                        questions_and_answers)
                continue

            handle_solution_attempt(event,
                                    vk_api,
                                    keyboard,
                                    redis_connection,
                                    questions_and_answers)
    except Exception as exception:
        logger.exception(exception)
