from telegram import update
from telegram.ext import DispatcherHandlerStop

import tg_bot.modules.sql.cust_filters_sql as filters
import tg_bot.modules.sql.rules_sql as rules_sql
import tg_bot.modules.sql.notes_sql as notes_sql
from tg_bot import dispatcher
from tg_bot.modules.cust_filters import HANDLER_GROUP
from tg_bot.modules.helper_funcs.string_handling import markdown_parser


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

    filters.add_filter(chatid, trigger, reply, is_sticker, is_document, is_image, is_audio, is_voice, is_video,
                   buttons)

def import_rules(chatid, rules):
    markdown_rules = markdown_parser(rules)
    rules_sql.set_rules(chatid, markdown_rules)

def import_note(chatid, name, text):
    notes_sql.add_note_to_db(chatid, name, text, 0)