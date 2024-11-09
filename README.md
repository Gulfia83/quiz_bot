# QUIZ_BOT
[Russian](RU_README.md)

Chatbots for online quizzes in Telegram and VK.

## Bot links
- [Telegram bot](@quiz_game_play_bot)
- [VK bot](https://vk.com/club228196128)

## Examples of bots

## Installation
1. Install Python 3.10.12 and create a virtual environment, activate it:

2. Install the necessary dependencies using `pip`:
```sh
pip install -r requirements.txt

3. This project uses the Redis database. Create and connect your instance on [redis website](https://app.redislabs.com/)
4. Get a token for your telegram bot and for your VK community.
5. Create a `.env` file and put the following environment variables in it:
```env
TG_BOT_TOKEN='telegram bot token'
VK_API_TOKEN='api key of your VK community'
TG_CHAT_ID='telegram chat id for sending logs'
REDIS_DB_HOST='host address of your Redis database server'
REDIS_DB_PORT='port number of the Redis database server'
QUIZ_FILE_PATH='path to the file with questions and answers'
```
## Launch
1. Launch the telegram bot:
```sh
python3 tg_bot.py
```
2. Launch the VK bot:
```sh
python3 vk_bot.py
```
***
The code is written for educational purposes in an online course for web developers [Devman](dvmn.org).