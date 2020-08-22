from telegram import update
from telegram.ext import DispatcherHandlerStop

import tg_bot.modules.sql.cust_filters_sql as sql
from tg_bot import dispatcher
from tg_bot.modules.cust_filters import HANDLER_GROUP


def import_filter(chatid, trigger, reply):

    is_sticker = False
    is_document = False
    is_image = False
    is_voice = False
    is_audio = False
    is_video = False
    buttons = []
    for handler in dispatcher.handlers.get(HANDLER_GROUP, []):
        if handler.filters == (trigger, chatid):
            dispatcher.remove_handler(handler, HANDLER_GROUP)

    sql.add_filter(chatid, trigger, reply, is_sticker, is_document, is_image, is_audio, is_voice, is_video,
                   buttons)