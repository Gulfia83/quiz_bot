import logging
from functools import partial

import redis
from random import choice
from environs import Env
from telegram import Update, Bot, ReplyKeyboardMarkup
from telegram.ext import Updater, CommandHandler, MessageHandler, Filters, CallbackContext

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


def start(update: Update, context: CallbackContext) -> None:
    keyboard = [
        ['Новый вопрос', 'Сдаться'],
        ['Мой счет']
        ]
    reply_markup = ReplyKeyboardMarkup(keyboard)
    update.message.reply_text(
        'Привет! Я бот для викторин!',
        reply_markup=reply_markup
        )


def help_command(update: Update, context: CallbackContext) -> None:
    update.message.reply_text('Help!')


def echo(update: Update, context: CallbackContext, db_connection) -> None:
    questions_and_answers = parse_file('questions/1vs1200.txt')
    print(questions_and_answers)
    questions = list(questions_and_answers.keys())
    user_input = update.effective_message.text
    random_question = choice(questions)
    if user_input == 'Новый вопрос':
        update.message.reply_text(random_question)
        db_connection.set(update.effective_user.id, random_question)
        #saved_question = db_connection.get(update.effective_user.id)
        #logger.info(f"Сохраненный вопрос для пользователя {update.effective_user.id}: {saved_question}")


def main() -> None:
    env = Env()
    env.read_env()
    tg_bot_token = env.str('TG_BOT_TOKEN')
    tg_chat_id = env.str('TG_CHAT_ID')
    redis_db_host = env.str('REDIS_DB_HOST')
    redis_db_port = env.str('REDIS_DB_PORT')
    bot = Bot(tg_bot_token)

    db_connection = redis.Redis(host=redis_db_host,
                                port=redis_db_port,
                                decode_responses=True)
    
    logging.basicConfig(
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO
    )
    logger.addHandler(TelegramLogsHandler(bot, tg_chat_id))
    logger.info('Бот запущен')

    try:
        updater = Updater(tg_bot_token)

        dispatcher = updater.dispatcher

        dispatcher.add_handler(CommandHandler("start", start))
        dispatcher.add_handler(CommandHandler("help", help_command))
        dispatcher.add_handler(MessageHandler(Filters.text & ~Filters.command,
                                              partial(echo, db_connection=db_connection)))

        updater.start_polling()

        updater.idle()
    except Exception as e:
        logging.exception(e)


if __name__ == '__main__':
    main()