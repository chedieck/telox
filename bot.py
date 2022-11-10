from core import Watcher
from config import TOKEN, CHAT_ID_LIST, URL_SEARCH_LIST
from telegram.ext import Updater, CommandHandler
from telegram import InputMediaPhoto, ParseMode


watcher_list = [Watcher(url) for url in URL_SEARCH_LIST]
DELAY = 30


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


def print_last_if_changed(context, w):
    if (new_ads:= w.update()):
        for new_ad in new_ads:
            caption = _pre_parse_html(str(new_ad))
            for chat_id in CHAT_ID_LIST:
                pic_arr = make_album(new_ad.image_url_list, caption)
                context.bot.send_media_group(chat_id, media=pic_arr)


def watch_job(context):
    for w in watcher_list:
        print_last_if_changed(context, w)


def start(update, context):
    if (user_id := update.message['chat']['id']) not in CHAT_ID_LIST:
        print(f'User of id {user_id} tried starting the bot.')
        update.message.reply_text('010010110101010101010110101000101010111010101011011101010110111100010110')

    else:
        update.message.reply_text('Ativando...')
        print("Ativado.")
        context.job_queue.run_repeating(watch_job, DELAY, 0)


if __name__ == '__main__':
    updater = Updater(token=TOKEN)
    dispatcher = updater.dispatcher
    dispatcher.add_handler(CommandHandler('start', start))
    updater.start_polling()
    updater.idle()
