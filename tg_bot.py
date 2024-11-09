import logging
from random import choice

import redis
from environs import Env
from telegram import Update, Bot, ReplyKeyboardMarkup
from telegram.ext import Updater, CommandHandler, MessageHandler, Filters, \
      CallbackContext, ConversationHandler

from add_questions import parse_file


logger = logging.getLogger(__name__)

ANSWERING = 1


class TelegramLogsHandler(logging.Handler):

    def __init__(self, tg_bot, chat_id):
        super().__init__()
        self.chat_id = chat_id
        self.tg_bot = tg_bot

    def emit(self, record):
        log_entry = self.format(record)
        self.tg_bot.send_message(chat_id=self.chat_id, text=log_entry)


def get_keyboard():
    keyboard = [
        ['Новый вопрос', 'Сдаться'],
        ['Мой счет']
    ]
    reply_markup = ReplyKeyboardMarkup(
        keyboard
    )

    return reply_markup


def start(update: Update, context: CallbackContext) -> None:
    update.message.reply_text(
        'Привет! Я бот для викторин!',
        reply_markup=get_keyboard()
        )


def handle_new_question_request(update: Update, context: CallbackContext) -> None:
    db_connection = context.bot_data['redis_connection']
    question = choice(list(context.bot_data['questions_and_answers'].keys()))
    db_connection.set(update.message.chat_id, question)
    update.message.reply_text(question)

    return ANSWERING


def handle_solution_attempt(update: Update, context: CallbackContext) -> None:
    db_connection = context.bot_data['redis_connection']
    question = db_connection.get(update.message.chat_id)
    user_input = update.effective_message.text
    answer = context.bot_data['questions_and_answers'].get(question)
    correct_answer = ''
    if '.' in answer:
        correct_answer = answer.split('.')[0].lower()
    elif '(' in answer:
        correct_answer = answer.split('(')[0].lower()
    if user_input.lower() in correct_answer:
        update.message.reply_text(
            'Правильно! Поздравляю! Для следующего вопроса нажми «Новый вопрос»',
            reply_markup=get_keyboard()
            )
        return ConversationHandler.END
    else:
        update.message.reply_text(
            'Неправильно… Попробуешь ещё раз?',
            reply_markup=get_keyboard()
            )


def give_up(update: Update, context: CallbackContext):
    db_connection = context.bot_data['redis_connection']
    question = db_connection.get(update.message.chat_id)
    answer = context.bot_data['questions_and_answers'].get(question)
    update.message.reply_text(f'Правильный ответ: "{answer}"')

    return handle_new_question_request(update, context)


def error(bot, update, error):
    logger.warning('Update "%s" caused error "%s"', update, error)


def main() -> None:
    env = Env()
    env.read_env()
    tg_bot_token = env.str('TG_BOT_TOKEN')
    tg_chat_id = env.str('TG_CHAT_ID')
    redis_db_host = env.str('REDIS_DB_HOST')
    redis_db_port = env.str('REDIS_DB_PORT')
    quiz_file_path = env('QUIZ_FILE_PATH', default='questions/1vs1200.txt')
    bot = Bot(tg_bot_token)

    redis_connection = redis.Redis(host=redis_db_host,
                                   port=redis_db_port,
                                   decode_responses=True)
    questions_and_answers = parse_file(quiz_file_path)

    logging.basicConfig(
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        level=logging.INFO
    )
    logger.addHandler(TelegramLogsHandler(bot, tg_chat_id))
    logger.info('Бот запущен')

    updater = Updater(tg_bot_token)
    dispatcher = updater.dispatcher
    dispatcher.bot_data['redis_connection'] = redis_connection
    dispatcher.bot_data['questions_and_answers'] = questions_and_answers

    conversation = ConversationHandler(
        entry_points=[MessageHandler(
            Filters.regex(r'^Новый вопрос$'),
            handle_new_question_request
            )],
        states={
            ANSWERING: [
                MessageHandler(Filters.regex(r'^Сдаться$'), give_up),
                MessageHandler(Filters.text & ~Filters.command,
                               handle_solution_attempt),
            ]
        },
        fallbacks=[CommandHandler('cancel', start)]
    )

    dispatcher.add_handler(CommandHandler('start', start))
    dispatcher.add_handler(conversation)

    dispatcher.add_error_handler(error)

    updater.start_polling()

    updater.idle()


if __name__ == '__main__':
    main()
