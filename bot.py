from typing import List
from core import Watcher, scan_logger, log_formatter
from config import TOKEN, URL_TO_CHAT_DICT, SHOW_NEW_ON_START, SCAN_DELAY, LOG_LEVEL
from telegram.ext import ApplicationBuilder, CommandHandler, CallbackContext
from telegram import InputMediaPhoto, Update
from telegram.constants import ParseMode
from pathlib import Path
from time import sleep

import logging


FLOOD_PREVENTIVE_DELAY_MS = 9000
CHAT_ID_SET = set([
    chat_id for v in URL_TO_CHAT_DICT.values() for chat_id in v
])
URL_LIST = URL_TO_CHAT_DICT.keys()
WATCHER_LIST = [
    Watcher(url) for url in URL_LIST
]
ON = False


## Configure logging
Path("logs/").mkdir(exist_ok=True)

app_logger = logging.getLogger(__name__)
app_logger.setLevel(LOG_LEVEL)
app_file_handler = logging.FileHandler('logs/full.log')
app_file_handler.setLevel(LOG_LEVEL)
app_file_handler.setFormatter(log_formatter)
chat_logger = logging.getLogger('chat')
chat_logger.setLevel(LOG_LEVEL)
chat_file_handler = logging.FileHandler('logs/chat.log')
chat_file_handler.setFormatter(log_formatter)
chat_logger.addHandler(chat_file_handler)

def _pre_parse_html(text: str):
    return text.replace('<br>', '')


def make_album(url_arr, caption):
    ret = []
    for idx, url in enumerate(url_arr):
        if idx == 0:
            pic = InputMediaPhoto(url, caption=caption, parse_mode=ParseMode.HTML)
        else:
            pic = InputMediaPhoto(url)
        ret.append(pic)
    return ret

async def send_album(context, chat_id: int, pic_arr: List):
    for i in range(0, len(pic_arr), 10):
        if (i > 0):
            sleep(FLOOD_PREVENTIVE_DELAY_MS/1000)
        await context.bot.send_media_group(chat_id, media=pic_arr[i: i+10])

async def print_last_if_changed(context, w: Watcher):
    if (new_ads:= await w.update()):
        subscribed_users = URL_TO_CHAT_DICT[w.url]
        chat_logger.info(f'Sending {len(new_ads):^3} ads to {len(subscribed_users):^3} users...')
        chat_logger.debug(f'{new_ads=}\n{subscribed_users=}')
        for idx, new_ad in enumerate(new_ads):
            caption = _pre_parse_html(str(new_ad))
            chat_logger.info(f'— Ad: {new_ad.title} ({len(new_ad.image_url_list):^2}) pics to users {subscribed_users}')
            chat_logger.debug(f'{new_ad=}')
            pic_arr = make_album(new_ad.image_url_list, caption)
            for chat_id in subscribed_users:
                await send_album(context, chat_id, pic_arr)
            sleep(FLOOD_PREVENTIVE_DELAY_MS/1000)
        chat_logger.info(f'Finished sending ads to users')
    else:
        scan_logger.info(f'No new ads for {w}')


async def watch_job(context):
    scan_logger.info(f'Scanning {len(WATCHER_LIST)} URLs...')
    for w in WATCHER_LIST:
        scan_logger.info(f'— Watcher URL: {w.url}')
        scan_logger.debug(f'{w.seen=}')
        scan_logger.debug(f'{w.hash=}')
        await print_last_if_changed(context, w)

async def stop(update, context):
    user_id = update.message['chat']['id']
    current_jobs = await context.job_queue.get_jobs_by_name(f'{user_id}-watcher')
    if current_jobs:
        for job in current_jobs:
            job.schedule_removal()

async def start(update: Update, context: CallbackContext):
    global ON
    chat = update.message.chat
    user_id = chat.id
    username = chat.username
    first_name = chat.first_name
    last_name = chat.last_name

    if user_id not in CHAT_ID_SET:
        chat_logger.warn(f'User {user_id} tried starting the bot!')
        chat_logger.debug(f'{new_ads=}\n{subscribed_users=}')
        await update.message.reply_text('010010110101010101010110101000101010111010101011011101010110111100010110')

    else:
        subscribed_urls_string = '\n'.join([u for u in URL_LIST if user_id in URL_TO_CHAT_DICT[u]])
        await update.message.reply_text(f'<b>{first_name} {last_name}</b>\n@{username}\n<i>#{user_id}</i>\nURLS:\n{subscribed_urls_string}\n---\nAtivado.', parse_mode=ParseMode.HTML)
        chat_logger.info(f"Ativado para usuário ({first_name} {last_name}) @{username} #{user_id}")
        if not SHOW_NEW_ON_START:
            [await w.update() for w in WATCHER_LIST]
        if not ON:
            job = context.job_queue.run_repeating(
                watch_job,
                SCAN_DELAY,
                name=f'{user_id}-watcher'
            )
            await job.run(context.application)
            ON = True



if __name__ == '__main__':
    application = ApplicationBuilder().token(TOKEN).build()
    start_handler = CommandHandler('start', start)
    stop_handler = CommandHandler('stop', stop)
    application.add_handler(start_handler)
    application.add_handler(stop_handler)
    application.run_polling()
