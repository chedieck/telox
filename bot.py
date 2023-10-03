from typing import List
from core import Watcher
from config import TOKEN, CHAT_TO_URL_DICT
from telegram.ext import ApplicationBuilder, CommandHandler
from telegram import InputMediaPhoto
from telegram.constants import ParseMode


URL_SET = set([
    url for v in CHAT_TO_URL_DICT.values() for url in v
])
WATCHER_LIST = [
    Watcher(url) for url in URL_SET
]
DELAY = 30
CHAT_ID_LIST = CHAT_TO_URL_DICT.keys()


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
        await context.bot.send_media_group(chat_id, media=pic_arr[i: i+10])

async def print_last_if_changed(context, w):
    if (new_ads:= w.update()):
        for new_ad in new_ads:
            caption = _pre_parse_html(str(new_ad))
            pic_arr = make_album(new_ad.image_url_list, caption)
            for chat_id in CHAT_ID_LIST:
                await send_album(context, chat_id, pic_arr)


async def watch_job(context):
    for w in WATCHER_LIST:
        await print_last_if_changed(context, w)

async def stop(update, context):
    user_id = update.message['chat']['id']
    current_jobs = await context.job_queue.get_jobs_by_name(f'{user_id}-watcher')
    if current_jobs:
        for job in current_jobs:
            job.schedule_removal()

async def start(update, context):
    user_id = update.message['chat']['id']
    if user_id not in CHAT_ID_LIST:
        print(f'User of id {user_id} tried starting the bot.')
        await update.message.reply_text('010010110101010101010110101000101010111010101011011101010110111100010110')

    else:
        await update.message.reply_text('Ativado.')
        print("Ativado.")
        [w.update() for w in WATCHER_LIST]
        context.job_queue.run_repeating(
            watch_job,
            DELAY,
            0,
            name=f'{user_id}-watcher'
        )


if __name__ == '__main__':
    application = ApplicationBuilder().token(TOKEN).build()
    start_handler = CommandHandler('start', start)
    stop_handler = CommandHandler('stop', stop)
    application.add_handler(start_handler)
    application.add_handler(stop_handler)
    application.run_polling()
