import board_getter as bg
from variables import TOKEN, CHAT_ID_LIST, URL_SEARCH_LIST
from telegram.ext import Updater, CommandHandler
from telegram import InputMediaPhoto, ParseMode


watcher_list = [bg.Watcher(url) for url in URL_SEARCH_LIST]
DELAY = 30


def _pre_parse_html(text: str):
    return text.replace('<br>', '')


def print_last_if_changed(context, w):
    changed = w.update()
    if changed:
        print('will show last...')
        last_ad = w.get_last_ad()

        # images_files = [Image.open(urllib2.urlopen(url)) for url in last_ad.images]
        print('oi', str(w.get_last_ad()))
        for chat_id in CHAT_ID_LIST:
            context.bot.send_message(chat_id,
                                     text=_pre_parse_html(str(w.get_last_ad())),
                                     parse_mode=ParseMode.HTML,
                                     disable_web_page_preview=True)
            pics_urls = [x['original'] for x in last_ad.images]
            n_pics = len(pics_urls)
            while n_pics > 0:
                if n_pics >= 10:
                    this_n = 10
                else:
                    this_n = n_pics

                # get urls and send media album
                url_arr = pics_urls[0: this_n]
                pic_arr = [InputMediaPhoto(url) for url in url_arr]
                context.bot.send_media_group(chat_id, media=pic_arr)

                # adjust variables
                del pics_urls[0:this_n]
                n_pics = n_pics - this_n


def watch_job(context):
    for w in watcher_list:
        print_last_if_changed(context, w)


def start(update, context):
    if (user_id := update.message['chat']['id']) not in CHAT_ID_LIST:
        print(f'id {user_id} tentando mandar msg')
        update.message.reply_text('010010110101010101010110101000101010111010101011011101010110111100010110')

    update.message.reply_text('Ativando...')
    print("Ativado.")
    context.job_queue.run_repeating(watch_job, DELAY, 0)


if __name__ == '__main__':
    updater = Updater(token=TOKEN)
    dispatcher = updater.dispatcher
    dispatcher.add_handler(CommandHandler('start', start))
    updater.start_polling()
    updater.idle()
