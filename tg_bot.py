import logging

from environs import Env
from telegram import Update, ForceReply, Bot
from telegram.ext import Updater, CommandHandler, MessageHandler, Filters, CallbackContext


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
    update.message.reply_markdown_v2(
        'Привет! Я бот для викторин!',
        reply_markup=ForceReply(selective=True),
    )


def help_command(update: Update, context: CallbackContext) -> None:
    update.message.reply_text('Help!')


def echo(update: Update, context: CallbackContext) -> None:
    update.message.reply_text(update.message.text)


def main() -> None:
    env = Env()
    env.read_env()
    tg_bot_token = env.str('TG_BOT_TOKEN')
    tg_chat_id = env.str('TG_CHAT_ID')
    bot = Bot(tg_bot_token)

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
                                              echo))

        updater.start_polling()

        updater.idle()
    except Exception as e:
        logging.exception(e)


if __name__ == '__main__':
    main()